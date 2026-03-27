"""Qdrant async client wrapper (singleton)."""
from __future__ import annotations

import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointStruct,
    Range,
    VectorParams,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None


async def get_qdrant() -> AsyncQdrantClient:
    """Return the Qdrant client singleton."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=30,
        )
    return _client


async def close_qdrant() -> None:
    """Close the Qdrant client."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


async def ensure_collection(client: AsyncQdrantClient, collection: str) -> None:
    """Ensure the collection exists with correct config."""
    collections = await client.get_collections()
    names = [c.name for c in collections.collections]
    if collection not in names:
        await client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            on_disk_payload=True,
            optimizers_config={"memmap_threshold": 20000},
        )
        logger.info(f"Created Qdrant collection: {collection}")


async def upsert_vectors(
    client: AsyncQdrantClient,
    collection: str,
    points: list[PointStruct],
) -> None:
    """Upsert points into a Qdrant collection."""
    if not points:
        return
    await client.upsert(collection_name=collection, points=points)
    logger.info(f"Upserted {len(points)} vectors to {collection}")


async def search_vectors(
    client: AsyncQdrantClient,
    collection: str,
    query_vector: list[float],
    *,
    limit: int = 10,
    score_threshold: float | None = None,
    source: str | None = None,
    tier: str | None = None,
    geo_zone: str | None = None,
    min_risk_score: float | None = None,
    transport_mode: str | None = None,
) -> list[dict[str, Any]]:
    """Search vectors with optional payload filters."""
    must_conditions: list[FieldCondition] = []

    if source:
        must_conditions.append(
            FieldCondition(key="source", match=MatchValue(value=source))
        )
    if tier:
        must_conditions.append(
            FieldCondition(key="tier", match=MatchValue(value=tier))
        )
    if geo_zone:
        must_conditions.append(
            FieldCondition(key="geo_zone", match=MatchValue(value=geo_zone))
        )
    if min_risk_score is not None:
        must_conditions.append(
            FieldCondition(key="risk_score", range=Range(gte=min_risk_score))
        )
    if transport_mode:
        must_conditions.append(
            FieldCondition(key="transport_mode", match=MatchValue(value=transport_mode))
        )

    search_filter = Filter(must=must_conditions) if must_conditions else None

    results = await client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=search_filter,
        with_payload=True,
    )

    return [
        {
            "id": str(hit.id),
            "score": round(hit.score, 4),
            "payload": hit.payload or {},
        }
        for hit in results
    ]


async def get_collection_info(
    client: AsyncQdrantClient, collection: str
) -> dict[str, Any]:
    """Get collection stats (vector count, segments, etc.)."""
    info = await client.get_collection(collection_name=collection)
    return {
        "name": collection,
        "vectors_count": getattr(info, 'vectors_count', 0),
        "points_count": getattr(info, 'points_count', 0),
        "segments_count": len(info.segments) if hasattr(info, 'segments') and info.segments else 0,
        "status": info.status.value if info.status else "unknown",
        "on_disk_payload": info.config.params.on_disk_payload if info.config and hasattr(info.config, 'params') else None,
    }


async def check_similarity(
    client: AsyncQdrantClient,
    collection: str,
    vector: list[float],
    threshold: float = 0.92,
) -> bool:
    """Check if a similar vector exists above the threshold."""
    results = await client.search(
        collection_name=collection,
        query_vector=vector,
        limit=1,
        score_threshold=threshold,
    )
    return len(results) > 0
