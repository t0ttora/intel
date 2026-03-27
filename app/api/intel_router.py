"""Intel API router — POST /query, GET /signals, GET /events."""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from psycopg import AsyncConnection

from app.api.schemas import (
    EventResponse,
    EventsListResponse,
    IntelligenceResponse,
    QueryRequest,
    SignalResponse,
    SignalsListResponse,
)
from app.config import Settings
from app.dependencies import ApiKeyDep, DBConn, QdrantDep, SettingsDep
from app.ingestion.sanitizer import contains_injection, sanitize_content
from app.intelligence.query_pipeline import execute_query
from app.db.queries import get_active_events, get_event_with_signals, get_signals, get_signal_count

logger = logging.getLogger(__name__)

intel_router = APIRouter(prefix="/api/v1", tags=["intel"])

# ── Rate Limiter (in-memory, per API key) ─────────────────────────────────

_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 30     # requests per window


def _check_rate_limit(api_key: str) -> None:
    """Check if API key has exceeded rate limit (30 req/min on /query)."""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    # Clean old entries
    _rate_limit_store[api_key] = [
        t for t in _rate_limit_store[api_key] if t > window_start
    ]

    if len(_rate_limit_store[api_key]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {RATE_LIMIT_MAX} requests per minute.",
        )

    _rate_limit_store[api_key].append(now)


# ── POST /query ───────────────────────────────────────────────────────────


@intel_router.post("/query", response_model=IntelligenceResponse)
async def query_intelligence(
    body: QueryRequest,
    request: Request,
    api_key: ApiKeyDep,
    conn: DBConn,
    qdrant: QdrantDep,
    settings: SettingsDep,
) -> dict:
    """Execute an intelligence query through the full 7-step pipeline.

    Rate limited to 30 requests/minute per API key.
    Query text is sanitized against prompt injection.
    """
    # Rate limit
    _check_rate_limit(api_key)

    # Sanitize query
    if contains_injection(body.query):
        raise HTTPException(
            status_code=400,
            detail="Query contains suspicious content and was rejected.",
        )
    sanitized_query = sanitize_content(body.query)

    # Execute pipeline
    result = await execute_query(
        sanitized_query,
        conn=conn,
        qdrant=qdrant,
        settings=settings,
        geo_zone=body.geo_zone,
        min_risk_score=body.min_risk_score,
        include_cascade=body.include_cascade,
        include_user_impact=body.include_user_impact,
        user_id=body.user_id,
    )

    return result


# ── GET /signals ──────────────────────────────────────────────────────────


@intel_router.get("/signals", response_model=SignalsListResponse)
async def list_signals(
    api_key: ApiKeyDep,
    conn: DBConn,
    tier: Annotated[str | None, Query(description="Filter by tier")] = None,
    geo_zone: Annotated[str | None, Query(description="Filter by geo zone")] = None,
    min_risk_score: Annotated[float | None, Query(ge=0, le=1)] = None,
    last_hours: Annotated[int, Query(ge=1, le=168)] = 24,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> dict:
    """List intelligence signals with filters."""
    signals = await get_signals(
        conn,
        tier=tier,
        geo_zone=geo_zone,
        min_risk_score=min_risk_score or 0.0,
        last_hours=last_hours,
        limit=limit,
        offset=offset,
    )

    total = await get_signal_count(conn, last_hours=last_hours)

    return {
        "signals": [
            SignalResponse(
                id=s.id,
                title=s.title,
                content=s.content[:500],
                source=s.source,
                url=s.url,
                geo_zone=s.geo_zone,
                risk_score=s.risk_score,
                tier=s.tier,
                created_at=s.created_at,
            )
            for s in signals
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── GET /events ───────────────────────────────────────────────────────────


@intel_router.get("/events", response_model=EventsListResponse)
async def list_events(
    api_key: ApiKeyDep,
    conn: DBConn,
    min_priority: Annotated[str | None, Query(description="Minimum priority: CRITICAL, HIGH, MEDIUM, LOW")] = None,
    last_hours: Annotated[int, Query(ge=1, le=168)] = 24,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> dict:
    """List active events with optional priority filter."""
    events = await get_active_events(
        conn,
        min_priority=min_priority,
        last_hours=last_hours,
        limit=limit,
    )

    return {
        "events": [_event_to_response(e) for e in events],
        "total": len(events),
    }


# ── GET /events/{event_id} ───────────────────────────────────────────────


@intel_router.get("/events/{event_id}", response_model=EventResponse)
async def get_event_detail(
    event_id: UUID,
    api_key: ApiKeyDep,
    conn: DBConn,
) -> dict:
    """Get full event detail with signals, decisions, and cascade predictions."""
    event = await get_event_with_signals(conn, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return _event_to_response(event)


def _event_to_response(event) -> dict:
    """Convert an Event model to an API response dict."""
    decisions = event.decisions or []
    cascade = event.cascade_effects or []

    # Handle both Pydantic models and raw dicts
    if decisions and hasattr(decisions[0], "model_dump"):
        decisions = [d.model_dump() for d in decisions]
    if cascade and hasattr(cascade[0], "model_dump"):
        cascade = [c.model_dump() for c in cascade]

    return {
        "event_id": str(event.event_id),
        "title": event.title,
        "summary": event.summary,
        "impact_score": event.impact_score,
        "priority": event.priority if isinstance(event.priority, str) else event.priority.value,
        "transport_modes": event.transport_modes,
        "regions": event.regions,
        "confidence": event.confidence,
        "signal_count": event.signal_count,
        "source_diversity": event.source_diversity,
        "decisions": decisions,
        "cascade_effects": cascade,
        "status": event.status if isinstance(event.status, str) else event.status.value,
        "start_time": event.start_time,
        "updated_at": event.updated_at,
    }
