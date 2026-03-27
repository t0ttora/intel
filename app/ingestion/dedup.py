"""Hash dedup + cosine similarity >= 0.92."""
from __future__ import annotations

import hashlib
import logging

from qdrant_client import AsyncQdrantClient

from app.vectordb.client import check_similarity

logger = logging.getLogger(__name__)

COSINE_DEDUP_THRESHOLD = 0.92


def content_hash(text: str) -> str:
    """Generate SHA-256 hash of normalized text."""
    normalized = " ".join(text.lower().split())
    return hashlib.sha256(normalized.encode()).hexdigest()


async def is_duplicate(
    text: str,
    embedding: list[float],
    qdrant_client: AsyncQdrantClient,
    collection: str,
    *,
    known_hashes: set[str] | None = None,
) -> bool:
    """Check if content is a duplicate via hash or cosine similarity.

    Returns True if:
    1. Exact hash match in known_hashes set, OR
    2. Cosine similarity >= 0.92 with any existing vector in Qdrant
    """
    # Step 1: Hash check (fast, in-memory)
    text_hash = content_hash(text)
    if known_hashes is not None and text_hash in known_hashes:
        logger.debug("Duplicate detected via hash match")
        return True

    # Step 2: Cosine similarity check (Qdrant search)
    try:
        is_similar = await check_similarity(
            qdrant_client,
            collection,
            embedding,
            threshold=COSINE_DEDUP_THRESHOLD,
        )
        if is_similar:
            logger.debug("Duplicate detected via cosine similarity >= 0.92")
            return True
    except Exception as exc:
        logger.warning(f"Qdrant similarity check failed, assuming not duplicate: {exc}")

    # Add hash to known set for future in-batch dedup
    if known_hashes is not None:
        known_hashes.add(text_hash)

    return False
