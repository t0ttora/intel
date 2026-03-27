"""CLI server FastAPI router — mounted on /cli/* in main app."""
from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from cli.server.handlers import (
    handle_dashboard_ws,
    get_cli_status,
    get_cli_signals,
    get_cli_sources,
)

cli_router = APIRouter(prefix="/cli", tags=["cli"])


@cli_router.get("/status")
async def cli_status() -> dict:
    """CLI status endpoint for remote mode."""
    return await get_cli_status()


@cli_router.get("/signals")
async def cli_signals(
    tier: str | None = None,
    geo_zone: str | None = None,
    limit: int = 20,
) -> dict:
    """CLI signals endpoint for remote mode."""
    return await get_cli_signals(tier=tier, geo_zone=geo_zone, limit=limit)


@cli_router.get("/sources")
async def cli_sources() -> dict:
    """CLI source weights endpoint for remote mode."""
    return await get_cli_sources()


@cli_router.websocket("/ws/dashboard")
async def dashboard_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for live dashboard updates."""
    await websocket.accept()
    try:
        await handle_dashboard_ws(websocket)
    except WebSocketDisconnect:
        pass
