"""Full 7-step query pipeline (intent → retrieval → cascade → scenario → output)."""
from __future__ import annotations

import logging
from typing import Any

from psycopg import AsyncConnection
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.db.queries import get_signals
from app.engine.cascade import propagate_cascade
from app.engine.fusion import ActiveEvent, compute_grc_with_events
from app.engine.scenarios import simulate_scenario
from app.intelligence.intent_classifier import classify_intent
from app.intelligence.output_builder import (
    DegradationLevel,
    build_intelligence_response,
)
from app.intelligence.user_context import fetch_user_shipments
from app.scoring.geo_criticality import detect_geo_zone, get_geo_criticality
from app.vectordb.search import semantic_search

logger = logging.getLogger(__name__)


async def execute_query(
    query: str,
    *,
    conn: AsyncConnection,
    qdrant: AsyncQdrantClient,
    settings: Settings,
    geo_zone: str | None = None,
    min_risk_score: float | None = None,
    include_cascade: bool = True,
    include_user_impact: bool = False,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Execute the full 7-step intelligence query pipeline.

    Steps:
    1. Classify intent
    2. Detect geo zone (if not provided)
    3. Retrieve relevant signals (Qdrant + PostgreSQL)
    4. Compute cascade propagation
    5. Fuse into GRC
    6. Simulate scenario
    7. Build structured response with data quality
    """
    degradation_level = DegradationLevel.FULL
    degraded_sources: list[str] = []

    # ── Step 1: Intent Classification ──
    intent = classify_intent(query)
    logger.info(f"Intent: {intent.primary_intent} (confidence={intent.confidence})")

    # ── Step 2: Geo Zone Detection ──
    if not geo_zone:
        geo_zone = detect_geo_zone(query)
    geo_crit = get_geo_criticality(geo_zone) if geo_zone else 0.5

    # ── Step 3: Signal Retrieval ──
    # Try Qdrant semantic search first
    qdrant_results: list[dict[str, Any]] = []
    try:
        qdrant_results = await semantic_search(
            qdrant,
            settings.qdrant_collection,
            query,
            limit=20,
            geo_zone=None,  # Don't hard-filter — let semantic relevance decide
            min_risk_score=min_risk_score,
        )
    except Exception as exc:
        logger.warning(f"Qdrant search failed, falling back to PG: {exc}")
        degradation_level = DegradationLevel.RAG_OFFLINE
        degraded_sources.append("qdrant")

    # Fallback / supplement with PostgreSQL — try geo-specific first, then broader
    pg_signals = await get_signals(
        conn,
        geo_zone=geo_zone,
        min_risk_score=min_risk_score or 0.3,
        last_hours=72,
        limit=20,
    )

    # If geo-specific returns nothing, search without geo filter
    if not pg_signals:
        pg_signals = await get_signals(
            conn,
            geo_zone=None,
            min_risk_score=min_risk_score or 0.3,
            last_hours=72,
            limit=20,
        )

    # Merge: start with PG signals, add Qdrant-only signal IDs
    all_signals = pg_signals  # PG signals have full model
    if qdrant_results and not all_signals:
        # Qdrant found matches but PG didn't — fetch signals by IDs from Qdrant hits
        from app.db.queries import get_signal_by_id
        from uuid import UUID
        seen_ids = {s.id for s in all_signals}
        for hit in qdrant_results[:10]:
            sid_str = hit.get("signal_id") or (hit.get("payload", {}).get("signal_id"))
            if sid_str:
                try:
                    sid = UUID(sid_str)
                    if sid not in seen_ids:
                        sig = await get_signal_by_id(conn, sid)
                        if sig:
                            all_signals.append(sig)
                            seen_ids.add(sid)
                except (ValueError, TypeError):
                    pass

    if not all_signals:
        # Last resort: any recent signals at all (no geo, no risk filters)
        pg_all = await get_signals(conn, last_hours=168, limit=10)
        if pg_all:
            all_signals = pg_all
            if degradation_level < DegradationLevel.HISTORICAL:
                degradation_level = DegradationLevel.HISTORICAL
        elif degradation_level < DegradationLevel.FULL_DEGRADATION:
            degradation_level = DegradationLevel.FULL_DEGRADATION

    # Find top risk score
    risk_score = max((s.risk_score or 0 for s in all_signals), default=0.0)

    # ── Step 4: Cascade Propagation ──
    cascade = None
    if include_cascade and geo_zone and risk_score >= 0.40:
        cascade = propagate_cascade(geo_zone, risk_score)

    # ── Step 5: GRC Fusion ──
    active_events: list[ActiveEvent] = []
    if geo_zone:
        active_events.append(
            ActiveEvent(
                zone=geo_zone,
                risk_score=risk_score,
                label=geo_zone.replace("_", " ").title(),
                event_count=len(all_signals),
            )
        )
    if cascade:
        for node in cascade.affected_zones[:3]:
            active_events.append(
                ActiveEvent(
                    zone=node.zone,
                    risk_score=node.propagated_risk,
                    label=node.zone.replace("_", " ").title(),
                )
            )

    grc_data = compute_grc_with_events(active_events)

    # ── Step 6: Scenario Simulation ──
    scenario = simulate_scenario(
        intent.primary_intent,
        risk_score,
        geo_crit,
    )

    # ── Step 7: User Impact (optional) ──
    user_shipments = None
    if include_user_impact and user_id:
        try:
            user_shipments = await fetch_user_shipments(user_id)
        except Exception as exc:
            logger.warning(f"Failed to fetch user shipments: {exc}")

    # Build affected zones list
    affected_zones: list[str] = []
    if geo_zone:
        affected_zones.append(geo_zone)
    if cascade:
        affected_zones.extend(n.zone for n in cascade.affected_zones)

    # ── Build Response ──
    response = build_intelligence_response(
        query=query,
        signals=all_signals,
        cascade=cascade,
        scenario=scenario,
        user_shipments=user_shipments,
        affected_zones=affected_zones,
        risk_score=risk_score,
        grc=grc_data["grc"],
        degradation_level=degradation_level,
        degraded_sources=degraded_sources,
    )

    return response
