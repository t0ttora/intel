"""CLI database helper — local-mode DB access for CLI commands."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

from psycopg import AsyncConnection

from app.config import get_settings
from app.db.pool import get_pool
from app.intelligence.query_pipeline import execute_query
from app.vectordb.client import get_qdrant

logger = logging.getLogger(__name__)


async def get_connection() -> AsyncConnection:
    """Get a connection from the pool."""
    pool = await get_pool()
    return await pool.getconn()


async def run_local_query(
    query: str,
    *,
    geo_zone: str | None = None,
    include_cascade: bool = True,
) -> dict[str, Any]:
    """Run a full intelligence query in local mode."""
    settings = get_settings()
    pool = await get_pool()
    qdrant = await get_qdrant()

    async with pool.connection() as conn:
        result = await execute_query(
            query,
            conn=conn,
            qdrant=qdrant,
            settings=settings,
            geo_zone=geo_zone,
            include_cascade=include_cascade,
        )
    return result


async def get_local_status() -> dict[str, Any]:
    """Get system status in local mode."""
    from app.db.queries import get_signal_count, get_signal_stats

    pool = await get_pool()
    settings = get_settings()

    status: dict[str, Any] = {
        "mode": "local",
        "version": "3.0.0",
        "db_connected": False,
        "qdrant_connected": False,
        "signal_count": 0,
    }

    try:
        async with pool.connection() as conn:
            status["signal_count"] = await get_signal_count(conn)
            status["stats"] = await get_signal_stats(conn)
            status["db_connected"] = True
    except Exception as exc:
        logger.error(f"DB status check failed: {exc}")

    try:
        qdrant = await get_qdrant()
        from app.vectordb.client import get_collection_info
        info = await get_collection_info(qdrant, settings.qdrant_collection)
        status["qdrant_connected"] = True
        status["qdrant_points"] = info.get("points_count", 0) if info else 0
    except Exception as exc:
        logger.error(f"Qdrant status check failed: {exc}")

    return status


async def get_local_signals(
    *,
    tier: str | None = None,
    geo_zone: str | None = None,
    min_risk: float = 0.0,
    last_hours: int = 24,
    limit: int = 20,
) -> list[dict]:
    """Get signals in local mode."""
    from app.db.queries import get_signals

    pool = await get_pool()
    async with pool.connection() as conn:
        signals = await get_signals(
            conn,
            tier=tier,
            geo_zone=geo_zone,
            min_risk_score=min_risk,
            last_hours=last_hours,
            limit=limit,
        )

    return [
        {
            "id": str(s.id),
            "title": s.title,
            "source": s.source,
            "geo_zone": s.geo_zone,
            "risk_score": s.risk_score,
            "tier": s.tier,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in signals
    ]


async def get_local_source_weights() -> list[dict]:
    """Get all source weights in local mode."""
    from app.db.queries import get_all_source_weights

    pool = await get_pool()
    async with pool.connection() as conn:
        weights = await get_all_source_weights(conn)

    return [
        {
            "source": w.source,
            "weight": w.current_weight,
            "last_calibrated": w.last_calibrated_at.isoformat() if w.last_calibrated_at else None,
        }
        for w in weights
    ]
