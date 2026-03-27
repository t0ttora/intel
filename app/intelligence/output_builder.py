"""Build structured JSON intelligence response with data quality block."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.db.models import Signal
from app.engine.cascade import CascadeResult
from app.engine.scenarios import Scenario
from app.intelligence.user_context import UserShipment

logger = logging.getLogger(__name__)


# ── Degradation Levels ────────────────────────────────────────────────────


class DegradationLevel:
    """Data quality degradation levels."""

    FULL = 0           # All sources active
    PARTIAL = 1        # One+ sources down
    HISTORICAL = 2     # No fresh signals for zone
    RAG_OFFLINE = 3    # Qdrant unreachable
    FULL_DEGRADATION = 4  # Multiple systems down


def build_data_quality(
    *,
    level: int = DegradationLevel.FULL,
    signal_count: int = 0,
    source_diversity: int = 0,
    avg_source_weight: float = 0.0,
    freshest_signal_age_hours: float = 0.0,
    degraded_sources: list[str] | None = None,
    fallback_mode: str | None = None,
    confidence_drop_reason: str | None = None,
) -> dict[str, Any]:
    """Build the data_quality block included in every intelligence response."""
    return {
        "level": level,
        "signal_count": signal_count,
        "source_diversity": source_diversity,
        "avg_source_weight": round(avg_source_weight, 3),
        "freshest_signal_age_hours": round(freshest_signal_age_hours, 2),
        "degraded_sources": degraded_sources or [],
        "fallback_mode": fallback_mode,
        "confidence_drop_reason": confidence_drop_reason,
    }


def compute_confidence(
    *,
    signal_count: int,
    source_diversity: int,
    avg_source_weight: float,
    degradation_level: int = DegradationLevel.FULL,
) -> float:
    """Compute response confidence based on data quality factors."""
    base_confidence = min(1.0, signal_count / 20) * 0.3  # More signals = higher

    diversity_factor = min(1.0, source_diversity / 4) * 0.3  # More diverse sources = higher

    weight_factor = avg_source_weight * 0.4  # Higher source weight = higher

    confidence = base_confidence + diversity_factor + weight_factor

    # Apply degradation penalties
    degradation_multipliers = {
        DegradationLevel.FULL: 1.0,
        DegradationLevel.PARTIAL: 0.7,
        DegradationLevel.HISTORICAL: 0.5,
        DegradationLevel.RAG_OFFLINE: 0.5,
        DegradationLevel.FULL_DEGRADATION: 0.2,
    }

    multiplier = degradation_multipliers.get(degradation_level, 0.5)
    confidence *= multiplier

    return round(max(0.1, min(0.99, confidence)), 2)


# ── Response Builder ──────────────────────────────────────────────────────


def build_intelligence_response(
    *,
    query: str,
    signals: list[Signal],
    cascade: CascadeResult | None = None,
    scenario: Scenario | None = None,
    user_shipments: list[UserShipment] | None = None,
    affected_zones: list[str] | None = None,
    risk_score: float = 0.0,
    grc: float = 0.0,
    degradation_level: int = DegradationLevel.FULL,
    degraded_sources: list[str] | None = None,
) -> dict[str, Any]:
    """Build the complete structured intelligence response."""

    # Compute data quality metrics
    sources = list(set(s.source for s in signals))
    source_diversity = len(sources)
    avg_source_weight = (
        sum(s.source_weight or 0 for s in signals) / len(signals)
        if signals
        else 0.0
    )

    now = datetime.now(timezone.utc)
    freshest_age = 0.0
    if signals:
        freshest = max(s.created_at for s in signals)
        if freshest.tzinfo is None:
            freshest = freshest.replace(tzinfo=timezone.utc)
        freshest_age = (now - freshest).total_seconds() / 3600.0

    confidence = compute_confidence(
        signal_count=len(signals),
        source_diversity=source_diversity,
        avg_source_weight=avg_source_weight,
        degradation_level=degradation_level,
    )

    # Build data quality block
    data_quality = build_data_quality(
        level=degradation_level,
        signal_count=len(signals),
        source_diversity=source_diversity,
        avg_source_weight=avg_source_weight,
        freshest_signal_age_hours=freshest_age,
        degraded_sources=degraded_sources,
        fallback_mode="historical" if degradation_level == DegradationLevel.HISTORICAL else None,
        confidence_drop_reason=(
            "Multiple sources degraded" if degradation_level >= DegradationLevel.PARTIAL else None
        ),
    )

    # Risk level
    from app.scoring.risk_scorer import classify_risk_level
    risk_level = classify_risk_level(risk_score)

    # Event summary from top signals
    event_summary = _build_event_summary(signals[:5])

    # Build response
    response: dict[str, Any] = {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 2),
        "global_risk_composite": round(grc, 4),
        "event_summary": event_summary,
        "confidence": confidence,
        "data_quality": data_quality,
        "generated_at": now.isoformat(),
        "ttl_hours": _compute_ttl(risk_score),
    }

    # Scenario block
    if scenario:
        response["scenario"] = {
            "reroute_probability": scenario.reroute_probability,
            "delay_distribution": {
                "p10": scenario.delay_distribution.p10,
                "p50": scenario.delay_distribution.p50,
                "p90": scenario.delay_distribution.p90,
                "unit": scenario.delay_distribution.unit,
            },
            "cost_distribution": {
                "p10": scenario.cost_distribution.p10,
                "p50": scenario.cost_distribution.p50,
                "p90": scenario.cost_distribution.p90,
                "unit": scenario.cost_distribution.unit,
            },
        }

    # Cascade block
    if cascade and cascade.affected_zones:
        response["cascade"] = {
            "propagation_depth": cascade.max_depth_reached,
            "affected_zones": [n.zone for n in cascade.affected_zones],
            "downstream_effects": _build_cascade_summary(cascade),
        }

    # User impact block
    if user_shipments:
        all_affected = affected_zones or []
        if cascade:
            all_affected = list(set(all_affected + [n.zone for n in cascade.affected_zones]))

        user_impact = _build_user_impact(user_shipments, all_affected, scenario)
        if user_impact:
            response["user_impact"] = user_impact

    # Sources block
    response["sources"] = _build_sources(signals[:10])

    # Full degradation override
    if degradation_level == DegradationLevel.FULL_DEGRADATION:
        response["event_summary"] = (
            "Intel system degraded. Manual monitoring recommended. "
            "Multiple data sources are currently unavailable."
        )
        response["confidence"] = 0.1

    return response


def _build_event_summary(signals: list[Signal]) -> str:
    """Build a human-readable event summary from top signals."""
    if not signals:
        return "No relevant signals found for this query."

    parts: list[str] = []
    for s in signals[:3]:
        title = s.title or s.content[:80]
        parts.append(f"[{s.source.upper()}] {title}")

    return " | ".join(parts)


def _build_cascade_summary(cascade: CascadeResult) -> str:
    """Build a human-readable cascade summary."""
    parts: list[str] = []
    for node in cascade.affected_zones[:5]:
        zone_name = node.zone.replace("_", " ").title()
        parts.append(f"{zone_name} (risk: {node.propagated_risk:.2f}, hop {node.hop})")
    return "; ".join(parts)


def _build_user_impact(
    shipments: list[UserShipment],
    affected_zones: list[str],
    scenario: Scenario | None,
) -> dict[str, Any] | None:
    """Build user impact block for affected shipments."""
    from app.intelligence.user_context import match_shipment_to_zone
    from app.engine.scenarios import estimate_shipment_impact

    affected_shipments: list[dict] = []
    total_exposure = 0

    for shipment in shipments:
        if not match_shipment_to_zone(shipment, affected_zones):
            continue

        shipment_data: dict[str, Any] = {
            "code": shipment.code,
            "route": shipment.route,
            "current_status": shipment.current_status,
        }

        if scenario:
            impact = estimate_shipment_impact(scenario, shipment.teu)
            shipment_data.update({
                "delay_probability": scenario.reroute_probability,
                "estimated_delay": {
                    "p50": impact["delay_p50_days"],
                    "unit": "days",
                },
                "cost_exposure": {
                    "p50": impact["cost_p50_usd"],
                    "unit": "USD",
                },
            })
            total_exposure += impact["cost_p50_usd"]

        affected_shipments.append(shipment_data)

    if not affected_shipments:
        return None

    return {
        "affected_shipments": affected_shipments,
        "total_exposure_usd": total_exposure,
        "priority_score": round(min(1.0, len(affected_shipments) * 0.3 + 0.1), 2),
    }


def _build_sources(signals: list[Signal]) -> list[dict[str, Any]]:
    """Build the sources block with type, weight, URL, and title."""
    sources: list[dict[str, Any]] = []
    for s in signals:
        entry: dict[str, Any] = {
            "type": s.source,
            "weight": round(s.source_weight or 0, 3),
            "title": s.title or "",
        }
        if s.url:
            entry["url"] = s.url
        sources.append(entry)
    return sources


def _compute_ttl(risk_score: float) -> int:
    """Compute TTL (hours) based on risk level — higher risk = shorter TTL."""
    if risk_score >= 0.80:
        return 1
    elif risk_score >= 0.60:
        return 3
    elif risk_score >= 0.40:
        return 6
    return 12
