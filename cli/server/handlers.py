"""CLI server handlers — data aggregation for CLI endpoints and WebSocket."""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.config import get_settings
from app.db.pool import get_pool
from app.db.queries import (
    get_signal_count,
    get_signal_stats,
    get_signals,
    get_all_source_weights,
    get_active_alerts,
)
from app.vectordb.client import get_qdrant, get_collection_info

logger = logging.getLogger(__name__)


async def get_cli_status() -> dict[str, Any]:
    """Aggregate system status for CLI."""
    settings = get_settings()
    pool = await get_pool()

    status: dict[str, Any] = {
        "version": "3.0.0",
        "db_connected": False,
        "qdrant_connected": False,
        "signal_count": 0,
        "stats": {},
    }

    try:
        async with pool.connection() as conn:
            status["signal_count"] = await get_signal_count(conn)
            status["stats"] = await get_signal_stats(conn)
            status["db_connected"] = True
    except Exception as exc:
        logger.error(f"DB check failed: {exc}")

    try:
        qdrant = await get_qdrant()
        info = await get_collection_info(qdrant, settings.qdrant_collection)
        status["qdrant_connected"] = True
        status["qdrant_points"] = info.get("points_count", 0) if info else 0
    except Exception as exc:
        logger.error(f"Qdrant check failed: {exc}")

    return status


async def get_cli_signals(
    *,
    tier: str | None = None,
    geo_zone: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Get signals for CLI display."""
    pool = await get_pool()

    async with pool.connection() as conn:
        signals = await get_signals(
            conn,
            tier=tier,
            geo_zone=geo_zone,
            last_hours=24,
            limit=limit,
        )

    return {
        "signals": [
            {
                "id": s.id,
                "title": s.title,
                "source": s.source,
                "geo_zone": s.geo_zone,
                "risk_score": s.risk_score,
                "tier": s.tier,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in signals
        ],
        "total": len(signals),
    }


async def get_cli_sources() -> dict[str, Any]:
    """Get source weights for CLI display."""
    pool = await get_pool()

    async with pool.connection() as conn:
        weights = await get_all_source_weights(conn)

    return {
        "sources": [
            {
                "source": w.source,
                "weight": w.current_weight,
                "last_calibrated": w.last_calibrated_at.isoformat() if w.last_calibrated_at else None,
            }
            for w in weights
        ]
    }


async def handle_dashboard_ws(websocket: WebSocket) -> None:
    """Stream live dashboard data over WebSocket.

    Sends a JSON update every 5 seconds with:
    - signal_count, latest signals, active alerts, source weights
    """
    settings = get_settings()
    pool = await get_pool()

    while True:
        try:
            async with pool.connection() as conn:
                signal_count = await get_signal_count(conn)
                latest_signals = await get_signals(conn, last_hours=1, limit=5)
                active_alerts = await get_active_alerts(conn, limit=5)
                source_weights = await get_all_source_weights(conn)

            # Build dashboard frame
            frame = {
                "type": "dashboard_update",
                "signal_count": signal_count,
                "latest_signals": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "source": s.source,
                        "risk_score": s.risk_score,
                        "tier": s.tier,
                        "geo_zone": s.geo_zone,
                    }
                    for s in latest_signals
                ],
                "active_alerts": [
                    {
                        "id": str(a.id),
                        "risk_level": a.risk_level,
                        "risk_score": a.risk_score,
                        "signal_id": str(a.signal_id) if a.signal_id else None,
                    }
                    for a in active_alerts
                ],
                "source_weights": [
                    {"source": w.source, "weight": w.current_weight}
                    for w in source_weights
                ],
            }

            await websocket.send_text(json.dumps(frame, default=str))
            await asyncio.sleep(5)

        except Exception as exc:
            logger.error(f"Dashboard WS error: {exc}")
            break
