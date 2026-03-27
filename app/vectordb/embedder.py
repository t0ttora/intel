"""Gemini embedding — batch embedder."""
from __future__ import annotations

import logging
from typing import Sequence

from google import genai

from app.config import get_settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIM = 768
MAX_BATCH_SIZE = 100

_genai_client: genai.Client | None = None


def _get_client() -> genai.Client:
    """Return the cached Gemini client."""
    global _genai_client
    if _genai_client is None:
        settings = get_settings()
        _genai_client = genai.Client(api_key=settings.gemini_api_key)
    return _genai_client


async def embed_texts(texts: Sequence[str]) -> list[list[float]]:
    """Batch embed texts via Gemini text-embedding-004.

    Splits into batches of MAX_BATCH_SIZE (100) if needed.
    Returns list of 768-dim float vectors.
    """
    if not texts:
        return []

    client = _get_client()
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = list(texts[i : i + MAX_BATCH_SIZE])
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config={"output_dimensionality": EMBEDDING_DIM},
            )
            batch_embeddings = [e.values for e in result.embeddings]
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Embedded batch {i // MAX_BATCH_SIZE + 1}: {len(batch)} texts")
        except Exception as exc:
            logger.error(f"Embedding batch failed: {exc}")
            # Return zero vectors for failed batch to maintain alignment
            all_embeddings.extend([[0.0] * EMBEDDING_DIM] * len(batch))

    return all_embeddings


async def embed_single(text: str) -> list[float]:
    """Embed a single text. Returns 768-dim vector."""
    results = await embed_texts([text])
    return results[0] if results else [0.0] * EMBEDDING_DIM
