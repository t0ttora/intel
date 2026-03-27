"""Qdrant search with filters (tier, geo_zone, min_risk_score)."""
from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient

from app.vectordb.client import search_vectors
from app.vectordb.embedder import embed_single

logger = logging.getLogger(__name__)


async def semantic_search(
    client: AsyncQdrantClient,
    collection: str,
    query: str,
    *,
    limit: int = 10,
    source: str | None = None,
    tier: str | None = None,
    geo_zone: str | None = None,
    min_risk_score: float | None = None,
) -> list[dict[str, Any]]:
    """Run a semantic search: embed query → search Qdrant with filters."""
    query_vector = await embed_single(query)

    results = await search_vectors(
        client,
        collection,
        query_vector,
        limit=limit,
        source=source,
        tier=tier,
        geo_zone=geo_zone,
        min_risk_score=min_risk_score,
    )

    logger.info(
        f"Semantic search for '{query[:50]}...' returned {len(results)} results"
    )
    return results
