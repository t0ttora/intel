"""Full 7-step query pipeline (intent → retrieval → cascade → scenario → output)."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from psycopg import AsyncConnection
from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.db.queries import get_active_events as db_get_active_events, get_signals
from app.engine.cascade import propagate_cascade
from app.engine.fusion import ActiveEvent, compute_grc_with_events
from app.engine.scenarios import simulate_scenario
from app.intelligence.intent_classifier import classify_intent
from app.intelligence.output_builder import (
    DegradationLevel,
    build_intelligence_response,
)
from app.intelligence.hybrid_search import hybrid_rerank
from app.intelligence.geo_fence import apply_geo_fence
from app.intelligence.query_expander import detect_transport_mode, detect_transport_modes, expand_query
from app.intelligence.user_context import fetch_user_shipments
from app.scoring.geo_criticality import detect_geo_zone, get_geo_criticality
from app.intelligence.signal_tagger import detect_region
from app.vectordb.search import semantic_search

logger = logging.getLogger(__name__)


# ── Geo-zone → region mapping ───────────────────────────────────────────────
# Maps chokepoint-style geo_zone codes to canonical region codes used by
# the signal tagger. This links the two systems for geo-fencing.

_GEO_ZONE_TO_REGION: dict[str, str] = {
    "suez_canal": "RED_SEA",
    "strait_of_malacca": "SE_ASIA",
    "panama_canal": "PANAMA",
    "bab_el_mandeb": "RED_SEA",
    "hormuz": "MIDDLE_EAST",
    "shanghai": "CHINA",
    "ningbo": "CHINA",
    "singapore": "SE_ASIA",
    "rotterdam": "N_EUROPE",
    "hamburg": "N_EUROPE",
    "los_angeles": "USWC",
    "long_beach": "USWC",
    "busan": "KOREA",
    "colombo": "INDIA",
    "piraeus": "MED",
    "valencia": "MED",
    "jeddah": "MIDDLE_EAST",
}

# Regions that are geographically proximate / on the same trade lane.
# Used to prevent false-positive rejections for neighboring regions.
_COMPATIBLE_REGIONS: dict[str, set[str]] = {
    "CHINA": {"SE_ASIA", "JAPAN", "KOREA", "TAIWAN", "CENTRAL_ASIA", "RUSSIA", "N_EUROPE", "MED", "BALTIC"},
    "SE_ASIA": {"CHINA", "INDIA", "JAPAN", "KOREA", "AUSTRALIA", "MIDDLE_EAST"},
    "N_EUROPE": {"BALTIC", "UK", "MED", "CHINA", "CENTRAL_ASIA", "RUSSIA"},
    "MED": {"N_EUROPE", "RED_SEA", "MIDDLE_EAST", "BALTIC", "UK", "E_AFRICA", "W_AFRICA"},
    "RED_SEA": {"MIDDLE_EAST", "MED", "E_AFRICA", "INDIA", "SE_ASIA"},
    "MIDDLE_EAST": {"RED_SEA", "INDIA", "MED", "E_AFRICA", "CENTRAL_ASIA"},
    "USEC": {"US_GULF", "USWC", "CANADA", "MEXICO"},
    "USWC": {"USEC", "US_GULF", "CANADA", "MEXICO", "CHINA", "SE_ASIA", "JAPAN", "KOREA"},
    "US_GULF": {"USEC", "USWC", "MEXICO", "CANADA"},
    "CANADA": {"USEC", "USWC", "US_GULF"},
    "INDIA": {"SE_ASIA", "MIDDLE_EAST", "RED_SEA", "E_AFRICA"},
    "JAPAN": {"KOREA", "CHINA", "SE_ASIA", "TAIWAN"},
    "KOREA": {"JAPAN", "CHINA", "SE_ASIA", "TAIWAN"},
    "TAIWAN": {"CHINA", "JAPAN", "KOREA", "SE_ASIA"},
    "CENTRAL_ASIA": {"CHINA", "RUSSIA", "N_EUROPE", "MIDDLE_EAST"},
    "RUSSIA": {"CENTRAL_ASIA", "CHINA", "N_EUROPE", "BALTIC"},
    "BALTIC": {"N_EUROPE", "RUSSIA", "UK"},
    "UK": {"N_EUROPE", "MED", "BALTIC"},
    "PANAMA": {"USWC", "USEC", "MEXICO", "COLOMBIA", "CHILE"},
    "BRAZIL": {"ARGENTINA", "COLOMBIA"},
    "MEXICO": {"USEC", "USWC", "US_GULF", "PANAMA"},
    "AUSTRALIA": {"NEW_ZEALAND", "SE_ASIA"},
    "NEW_ZEALAND": {"AUSTRALIA", "SE_ASIA"},
    "E_AFRICA": {"RED_SEA", "MIDDLE_EAST", "INDIA", "S_AFRICA"},
    "W_AFRICA": {"MED", "N_EUROPE", "S_AFRICA"},
    "S_AFRICA": {"E_AFRICA", "W_AFRICA"},
    "ARGENTINA": {"BRAZIL", "CHILE"},
    "CHILE": {"ARGENTINA", "PANAMA"},
    "COLOMBIA": {"PANAMA", "BRAZIL"},
}


def detect_region_from_geo_zone(geo_zone: str) -> str | None:
    """Map a geo_zone code to a canonical region code."""
    return _GEO_ZONE_TO_REGION.get(geo_zone)


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
    0. Expand query (ontology injection + mode detection)
    1. Classify intent (on expanded query)
    2. Detect geo zone (if not provided)
    3. Retrieve relevant signals (Qdrant with mode pre-filter + PostgreSQL)
    4. Compute cascade propagation
    5. Fuse into GRC
    6. Simulate scenario
    7. Build structured response with data quality
    """
    degradation_level = DegradationLevel.FULL
    degraded_sources: list[str] = []

    # ── Step 0: Query Expansion ──
    expanded_query = expand_query(query)
    detected_modes = detect_transport_modes(expanded_query)
    transport_mode = detected_modes[0] if len(detected_modes) == 1 else None
    logger.info(f"Expanded query: '{query}' → modes={detected_modes or ['none']}")

    # ── Step 1: Intent Classification (on expanded query) ──
    intent = classify_intent(query)
    logger.info(f"Intent: {intent.primary_intent} (confidence={intent.confidence})")

    # FLAW 1 FIX: "unknown" intent does NOT auto-reject.
    # We still attempt retrieval — 0 signals = "Insufficient Intelligence",
    # not "not logistics". Only truly non-logistics queries (unknown + 0 signals)
    # get the empty response. If Qdrant finds relevant signals for an "unknown"
    # intent, we elevate to the best-matching intent.

    # ── Step 2: Geo Zone Detection ──
    if not geo_zone:
        geo_zone = detect_geo_zone(expanded_query)
    geo_crit = get_geo_criticality(geo_zone) if geo_zone else 0.5

    # ── Step 3: Signal Retrieval (Multi-Modal Split-Retrieval) ──────────
    # If the query spans multiple transport modes (e.g. "sea-air freight
    # conversion"), we split the retrieval limit K equally across modes and
    # run parallel Qdrant queries with strict metadata filters. This
    # mechanically prevents Vector Domination — the heavy semantic weight
    # of one domain can no longer crowd out minority-mode signals.
    TOTAL_K = 20
    qdrant_results: list[dict[str, Any]] = []
    score_threshold = 0.50 if intent.primary_intent == "unknown" else None

    try:
        if len(detected_modes) >= 2:
            # ── MULTI-MODE PARALLEL SPLIT-RETRIEVAL ──
            k_per_mode = max(4, TOTAL_K // len(detected_modes))
            logger.info(
                f"Multi-mode decomposition: {detected_modes} "
                f"(K={k_per_mode} per mode, {len(detected_modes)} parallel queries)"
            )

            async def _search_mode(mode: str) -> list[dict[str, Any]]:
                return await semantic_search(
                    qdrant,
                    settings.qdrant_collection,
                    expanded_query,
                    limit=k_per_mode,
                    geo_zone=None,
                    min_risk_score=min_risk_score,
                    transport_mode=mode,
                    score_threshold=score_threshold,
                )

            mode_results = await asyncio.gather(
                *[_search_mode(m) for m in detected_modes],
                return_exceptions=True,
            )
            for i, result in enumerate(mode_results):
                if isinstance(result, list):
                    logger.info(
                        f"  mode={detected_modes[i]}: {len(result)} results"
                    )
                    qdrant_results.extend(result)
                elif isinstance(result, Exception):
                    logger.warning(f"  mode={detected_modes[i]} search failed: {result}")
        else:
            # ── SINGLE-MODE (or no-mode) RETRIEVAL ──
            qdrant_results = await semantic_search(
                qdrant,
                settings.qdrant_collection,
                expanded_query,
                limit=TOTAL_K,
                geo_zone=None,
                min_risk_score=min_risk_score,
                transport_mode=transport_mode,  # None or single mode
                score_threshold=score_threshold,
            )
    except Exception as exc:
        logger.warning(f"Qdrant search failed, falling back to PG: {exc}")
        degradation_level = DegradationLevel.RAG_OFFLINE
        degraded_sources.append("qdrant")

    # FLAW 2 FIX: Hybrid re-ranking (BM25 + vector fusion)
    # For multi-mode results, first dedup by vector ID (same signal can
    # appear in multiple mode buckets), then re-rank the merged pool.
    if qdrant_results:
        if len(detected_modes) >= 2:
            seen_vids: set[str] = set()
            deduped: list[dict[str, Any]] = []
            for hit in qdrant_results:
                vid = hit.get("id", "")
                if vid not in seen_vids:
                    deduped.append(hit)
                    seen_vids.add(vid)
            if len(deduped) < len(qdrant_results):
                logger.info(
                    f"Multi-mode dedup: {len(qdrant_results)} → {len(deduped)} "
                    f"({len(qdrant_results) - len(deduped)} cross-mode duplicates)"
                )
            qdrant_results = deduped
        qdrant_results = hybrid_rerank(expanded_query, qdrant_results)

    # Resolve Qdrant hits to full Signal objects (preserves relevance order)
    all_signals: list = []
    if qdrant_results:
        from app.db.queries import get_signals_by_ids
        from uuid import UUID
        qdrant_ids: list[UUID] = []
        for hit in qdrant_results:
            sid_str = hit.get("payload", {}).get("signal_id")
            if sid_str:
                try:
                    qdrant_ids.append(UUID(sid_str))
                except (ValueError, TypeError):
                    pass
        signal_map = await get_signals_by_ids(conn, qdrant_ids)
        seen_ids: set = set()
        for sid in qdrant_ids:
            if sid in seen_ids:
                continue
            sig = signal_map.get(sid)
            if sig:
                all_signals.append(sig)
                seen_ids.add(sid)

    # Supplement with PG if Qdrant returned few results
    # BUT: skip PG fallback for "unknown" intent when Qdrant found nothing relevant
    # (prevents generic PG results from creating false positives)
    skip_pg_fallback = (intent.primary_intent == "unknown" and len(all_signals) == 0)
    if len(all_signals) < 5 and not skip_pg_fallback:
        seen_ids_pg = {s.id for s in all_signals}
        # For multi-mode queries, try PG per detected mode
        pg_modes = detected_modes if len(detected_modes) >= 2 else [transport_mode]
        for pg_mode in pg_modes:
            pg_signals = await get_signals(
                conn,
                geo_zone=geo_zone,
                min_risk_score=min_risk_score or 0.3,
                last_hours=72,
                limit=20 // max(1, len(pg_modes)),
                transport_mode=pg_mode,
            )
            if not pg_signals:
                pg_signals = await get_signals(
                    conn,
                    geo_zone=None,
                    min_risk_score=min_risk_score or 0.3,
                    last_hours=72,
                    limit=20 // max(1, len(pg_modes)),
                    transport_mode=pg_mode,
                )
            for sig in pg_signals:
                if sig.id not in seen_ids_pg:
                    all_signals.append(sig)
                    seen_ids_pg.add(sig.id)

    # ── URL-based collapse (deduplicate by URL) ───────────────────────
    # Multiple chunks from the same article can appear as separate signals.
    # Keep only the first (highest-ranked) signal per URL so the LLM
    # never sees the same link twice.
    if all_signals:
        seen_urls: set[str] = set()
        collapsed: list = []
        for sig in all_signals:
            url = getattr(sig, "url", None)
            if url:
                if url in seen_urls:
                    continue
                seen_urls.add(url)
            collapsed.append(sig)
        if len(collapsed) < len(all_signals):
            logger.info(
                f"URL collapse: {len(all_signals)} → {len(collapsed)} signals "
                f"({len(all_signals) - len(collapsed)} duplicate URLs removed)"
            )
        all_signals = collapsed

    # ── Geo-fencing guardrail ──────────────────────────────────────────
    # If the query targets a specific region, reject signals from
    # completely unrelated regions. Prevents geographic hallucination
    # (e.g., US rail news answering China-Europe queries).
    pre_fence_count = len(all_signals)
    if all_signals and geo_zone:
        query_region = detect_region_from_geo_zone(geo_zone)
        all_signals = apply_geo_fence(all_signals, expanded_query, query_region)
    # Also apply geo-fence when geo_zone wasn't detected from chokepoints
    # but the query text itself contains a clear regional reference
    elif all_signals:
        query_region_text = detect_region(expanded_query)
        if query_region_text:
            all_signals = apply_geo_fence(all_signals, expanded_query, query_region_text)

    geo_fenced_out = pre_fence_count > 0 and len(all_signals) == 0

    # ── FLAW 1 FIX: Proper fallback logic ──
    # 0 signals + unknown intent → "Not logistics" (true negative)
    # 0 signals + KNOWN intent → "Insufficient Intelligence" (we know
    # the domain but have no data — don't blame the user's query)
    if not all_signals:
        if intent.primary_intent == "unknown":
            # True negative — query really isn't logistics
            return {
                "risk_score": 0.0,
                "risk_level": "NONE",
                "global_risk_composite": 0.0,
                "confidence": intent.confidence,
                "event_summary": "Query does not appear to be related to logistics, maritime, or supply chain operations.",
                "intent": {"primary": intent.primary_intent, "confidence": intent.confidence, "scores": intent.all_scores},
                "scenario": None,
                "cascade": None,
                "user_impact": None,
                "data_quality": {"level": 4, "signal_count": 0, "source_diversity": 0, "avg_source_weight": 0, "freshest_signal_age_hours": 0, "degraded_sources": degraded_sources},
                "sources": [],
                "ttl_hours": 24,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "warnings": ["Query did not match any logistics intent patterns. Try a logistics-specific query."],
            }
        else:
            # KNOWN intent but no signals
            mode_label = f" ({transport_mode})" if transport_mode else ""

            # Check if geo-fencing rejected all signals
            if geo_fenced_out:
                return {
                    "risk_score": 0.0,
                    "risk_level": "INSUFFICIENT",
                    "global_risk_composite": 0.0,
                    "confidence": 0.0,
                    "event_summary": (
                        f"INSUFFICIENT (Geographic mismatch in data). "
                        f"The system found {pre_fence_count} signal(s) but all belonged to "
                        f"unrelated geographic regions. No relevant intelligence exists for "
                        f"the requested region{mode_label}."
                    ),
                    "intent": {"primary": intent.primary_intent, "confidence": intent.confidence, "scores": intent.all_scores},
                    "scenario": None,
                    "cascade": None,
                    "user_impact": None,
                    "data_quality": {"level": 4, "signal_count": 0, "source_diversity": 0, "avg_source_weight": 0, "freshest_signal_age_hours": 0, "degraded_sources": degraded_sources, "geo_fenced_out": pre_fence_count},
                    "sources": [],
                    "ttl_hours": 6,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "warnings": [
                        f"Geographic mismatch: {pre_fence_count} signals rejected — none matched the query region.",
                        "The system has data for this topic, but not in the requested geographic area.",
                    ],
                }

            # Standard "Insufficient Intelligence" — no data at all
            return {
                "risk_score": 0.0,
                "risk_level": "INSUFFICIENT",
                "global_risk_composite": 0.0,
                "confidence": intent.confidence,
                "event_summary": (
                    f"No intelligence signals found for this {intent.primary_intent}{mode_label} query. "
                    f"The system recognized the logistics context but has insufficient data coverage. "
                    f"This may indicate a gap in source feeds or a very recent/niche event."
                ),
                "intent": {"primary": intent.primary_intent, "confidence": intent.confidence, "scores": intent.all_scores},
                "scenario": None,
                "cascade": None,
                "user_impact": None,
                "data_quality": {"level": 4, "signal_count": 0, "source_diversity": 0, "avg_source_weight": 0, "freshest_signal_age_hours": 0, "degraded_sources": degraded_sources},
                "sources": [],
                "ttl_hours": 6,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "warnings": [
                    f"Intent classified as '{intent.primary_intent}' but 0 signals matched.",
                    "Consider broadening the query or checking source feed health.",
                ],
            }

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

    # ── Inject Active Events (Decision Engine v1.0) ──
    try:
        active_events = await db_get_active_events(
            conn, min_priority="HIGH", last_hours=24, limit=10,
        )
        # Filter to events matching this query's geo/modes
        matching_events = []
        for ev in active_events:
            # Match by region or transport mode overlap
            ev_regions = set(ev.regions)
            ev_modes = set(ev.transport_modes)
            query_region = _GEO_ZONE_TO_REGION.get(geo_zone, "") if geo_zone else ""

            region_match = not query_region or query_region.lower() in {r.lower() for r in ev_regions} or not ev_regions
            mode_match = not detected_modes or bool(ev_modes & set(detected_modes)) or not ev_modes

            if region_match or mode_match:
                matching_events.append(ev)

        if matching_events:
            response["active_events"] = [
                {
                    "event_id": str(ev.event_id),
                    "title": ev.title,
                    "impact_score": ev.impact_score,
                    "priority": ev.priority if isinstance(ev.priority, str) else ev.priority.value,
                    "transport_modes": ev.transport_modes,
                    "regions": ev.regions,
                    "decisions": [
                        d if isinstance(d, dict) else d.model_dump()
                        for d in (ev.decisions or [])
                    ][:3],
                    "confidence": ev.confidence,
                }
                for ev in matching_events[:5]
            ]
            # CRITICAL event boost: +0.10 to risk score
            has_critical = any(
                (ev.priority if isinstance(ev.priority, str) else ev.priority.value) == "CRITICAL"
                for ev in matching_events
            )
            if has_critical and response.get("risk_score", 0) < 1.0:
                response["risk_score"] = round(
                    min(1.0, response.get("risk_score", 0) + 0.10), 4
                )
    except Exception as exc:
        logger.warning(f"Failed to inject active events: {exc}")

    return response
