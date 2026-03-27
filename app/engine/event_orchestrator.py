"""Event Orchestrator — the 10-step background pipeline that fuses signals into events.

Steps:
1. Fetch recent unclustered signals (last 6h, risk_score > 0.20)
2. Noise control → filter_noise()
3. Cluster → cluster_signals()
4. Build events → merge_into_event()
5. Score → compute_impact_score() per event
6. Decide → generate_decisions() per event
7. Cascade → generate_cascade_predictions() for HIGH+ events
8. Dedup against existing active events
9. Persist to PostgreSQL
10. Push CRITICAL events to Supabase alerts

Returns: stats dict with counts.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from psycopg import AsyncConnection
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.db.event_models import EventCreate, EventStatus, Priority
from app.db.queries import (
    get_active_events,
    get_signals_for_clustering,
    insert_event,
    update_event,
)
from app.engine.decision_generator import generate_cascade_predictions, generate_decisions
from app.engine.event_fusion import cluster_signals, deduplicate_events, merge_into_event
from app.engine.noise_control import filter_noise
from app.scoring.impact_scorer import score_and_classify

logger = logging.getLogger(__name__)

# Default lookback window for clustering
CLUSTERING_WINDOW_HOURS = 6.0
MIN_RISK_FOR_CLUSTERING = 0.20
CASCADE_MIN_PRIORITY = Priority.HIGH


async def run_event_pipeline(
    conn: AsyncConnection,
    qdrant: AsyncQdrantClient,
    settings: Settings,
) -> dict:
    """Execute the full event pipeline. Returns stats."""
    stats = {
        "signals_fetched": 0,
        "signals_after_noise": 0,
        "clusters_found": 0,
        "events_created": 0,
        "events_updated": 0,
        "decisions_generated": 0,
        "cascade_effects": 0,
        "critical_events": 0,
    }

    # ── Step 1: Fetch unclustered signals ──────────────────────────────
    signals = await get_signals_for_clustering(
        conn,
        last_hours=CLUSTERING_WINDOW_HOURS,
        min_risk_score=MIN_RISK_FOR_CLUSTERING,
    )
    stats["signals_fetched"] = len(signals)

    if not signals:
        logger.info("Event pipeline: no eligible signals")
        return stats

    # ── Step 2: Noise control ──────────────────────────────────────────
    clean_signals = filter_noise(signals)
    stats["signals_after_noise"] = len(clean_signals)

    if len(clean_signals) < 2:
        logger.info("Event pipeline: too few signals after noise control")
        return stats

    # ── Step 3: Cluster signals ────────────────────────────────────────
    clusters = await cluster_signals(clean_signals, qdrant, settings)
    stats["clusters_found"] = len(clusters)

    if not clusters:
        logger.info("Event pipeline: no clusters formed")
        return stats

    # ── Step 4: Build events ───────────────────────────────────────────
    raw_events = [merge_into_event(c) for c in clusters]

    # Build signal lookup for scoring/decision phases
    signal_map = {s.id: s for s in clean_signals}

    # ── Step 5: Score each event ───────────────────────────────────────
    for event in raw_events:
        event_signals = [signal_map[sid] for sid in event.signal_ids if sid in signal_map]
        score_and_classify(event, event_signals)

    # ── Step 6: Generate decisions ─────────────────────────────────────
    for event in raw_events:
        event_signals = [signal_map[sid] for sid in event.signal_ids if sid in signal_map]
        event.decisions = generate_decisions(event, event_signals)
        stats["decisions_generated"] += len(event.decisions)

    # ── Step 7: Cascade predictions for HIGH+ ──────────────────────────
    for event in raw_events:
        if event.priority in (Priority.CRITICAL, Priority.HIGH):
            event.cascade_effects = generate_cascade_predictions(event)
            stats["cascade_effects"] += len(event.cascade_effects)

    # ── Step 8: Dedup against existing events ──────────────────────────
    existing = await get_active_events(conn, last_hours=48)
    truly_new, updates = deduplicate_events(raw_events, existing)

    # ── Step 9: Persist ────────────────────────────────────────────────
    for event in truly_new:
        event_create = EventCreate(
            title=event.title,
            summary=event.summary,
            impact_score=event.impact_score,
            priority=event.priority.value,
            transport_modes=event.transport_modes,
            regions=event.regions,
            confidence=event.confidence,
            signal_ids=event.signal_ids,
            signal_count=event.signal_count,
            source_diversity=event.source_diversity,
            decisions=[d.model_dump() for d in event.decisions],
            cascade_effects=[c.model_dump() for c in event.cascade_effects],
            status=EventStatus.ACTIVE.value,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )
        await insert_event(conn, event_create)
        stats["events_created"] += 1

        if event.priority == Priority.CRITICAL:
            stats["critical_events"] += 1

    # Update existing events with new signals/scores
    for new_ev, existing_ev in updates:
        await update_event(
            conn,
            existing_ev.event_id,
            impact_score=new_ev.impact_score,
            priority=new_ev.priority.value,
            confidence=new_ev.confidence,
            decisions=[d.model_dump() for d in new_ev.decisions],
            cascade_effects=[c.model_dump() for c in new_ev.cascade_effects],
        )
        stats["events_updated"] += 1

    # ── Step 10: Log results ───────────────────────────────────────────
    logger.info(
        f"Event pipeline complete: {stats['events_created']} new, "
        f"{stats['events_updated']} updated, "
        f"{stats['critical_events']} CRITICAL, "
        f"{stats['decisions_generated']} decisions"
    )
    return stats
