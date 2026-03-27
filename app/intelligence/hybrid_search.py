"""Hybrid search — BM25 keyword scoring + dense vector fusion.

Implements Reciprocal Rank Fusion (RRF) to combine Qdrant dense vector
results with application-level BM25 keyword scoring.  This prevents
"vector domination" where semantically similar but domain-irrelevant
signals outrank exact keyword matches (FLAW 2 fix).
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

# ── BM25 Parameters ─────────────────────────────────────────────────────────
_K1 = 1.5   # Term frequency saturation
_B = 0.75   # Length normalization


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + punctuation tokenizer."""
    return re.findall(r"\b\w{2,}\b", text.lower())


def _compute_idf(term: str, doc_freqs: dict[str, int], n_docs: int) -> float:
    """IDF with smoothing to avoid log(0)."""
    df = doc_freqs.get(term, 0)
    return math.log((n_docs - df + 0.5) / (df + 0.5) + 1.0)


def bm25_score(
    query_tokens: list[str],
    doc_tokens: list[str],
    doc_freqs: dict[str, int],
    n_docs: int,
    avg_doc_len: float,
) -> float:
    """Compute BM25 score for a single document against query tokens."""
    tf_counter = Counter(doc_tokens)
    doc_len = len(doc_tokens)
    score = 0.0

    for term in query_tokens:
        if term not in tf_counter:
            continue
        tf = tf_counter[term]
        idf = _compute_idf(term, doc_freqs, n_docs)
        numerator = tf * (_K1 + 1)
        denominator = tf + _K1 * (1 - _B + _B * doc_len / max(avg_doc_len, 1))
        score += idf * (numerator / denominator)

    return score


def hybrid_rerank(
    query: str,
    qdrant_results: list[dict[str, Any]],
    *,
    rrf_k: int = 60,
    vector_weight: float = 0.6,
    bm25_weight: float = 0.4,
) -> list[dict[str, Any]]:
    """Re-rank Qdrant results using Reciprocal Rank Fusion of vector + BM25 scores.

    Each result dict must have:
      - "id": unique identifier
      - "score": cosine similarity from Qdrant
      - "payload": dict with at least "signal_id" and optionally "content" or "title"

    Returns: Re-ranked list with "hybrid_score" added to each result.
    """
    if not qdrant_results:
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        # No meaningful tokens — just return vector-ranked results
        for r in qdrant_results:
            r["hybrid_score"] = r.get("score", 0.0)
        return qdrant_results

    # Build document token lists from payload content
    doc_token_lists: list[list[str]] = []
    for result in qdrant_results:
        payload = result.get("payload", {})
        # Combine whatever text fields are available
        text_parts = []
        for field in ("title", "content", "source"):
            val = payload.get(field)
            if val:
                text_parts.append(str(val))
        doc_tokens = _tokenize(" ".join(text_parts))
        doc_token_lists.append(doc_tokens)

    # Compute document frequencies for IDF
    n_docs = len(qdrant_results)
    doc_freqs: dict[str, int] = Counter()
    for tokens in doc_token_lists:
        unique_terms = set(tokens)
        for term in unique_terms:
            doc_freqs[term] += 1

    avg_doc_len = sum(len(t) for t in doc_token_lists) / max(n_docs, 1)

    # Compute BM25 scores
    bm25_scores: list[float] = []
    for doc_tokens in doc_token_lists:
        score = bm25_score(query_tokens, doc_tokens, doc_freqs, n_docs, avg_doc_len)
        bm25_scores.append(score)

    # Rank by vector score (already sorted by Qdrant, but be explicit)
    vector_ranked = sorted(
        range(n_docs), key=lambda i: qdrant_results[i].get("score", 0), reverse=True
    )
    # Rank by BM25 score
    bm25_ranked = sorted(range(n_docs), key=lambda i: bm25_scores[i], reverse=True)

    # Reciprocal Rank Fusion
    rrf_scores: dict[int, float] = {}
    for rank, idx in enumerate(vector_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + vector_weight / (rrf_k + rank + 1)
    for rank, idx in enumerate(bm25_ranked):
        rrf_scores[idx] = rrf_scores.get(idx, 0) + bm25_weight / (rrf_k + rank + 1)

    # Sort by RRF score and annotate results
    final_order = sorted(rrf_scores, key=rrf_scores.get, reverse=True)  # type: ignore[arg-type]

    reranked: list[dict[str, Any]] = []
    for idx in final_order:
        result = qdrant_results[idx].copy()
        result["hybrid_score"] = round(rrf_scores[idx], 6)
        result["bm25_score"] = round(bm25_scores[idx], 4)
        reranked.append(result)

    return reranked
