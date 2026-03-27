"""Impact Scoring v2 — compute 0-100 impact score for fused events.

Formula:
    impact = source_weight × severity_weight × geographic_weight × recency_weight
             × multimodal_multiplier × 100

Reuses existing modules: geo_criticality, time_decay.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone

from app.db.event_models import Event, classify_priority
from app.db.models import Signal
from app.scoring.geo_criticality import get_geo_criticality
from app.scoring.time_decay import compute_time_decay_from_timestamp

logger = logging.getLogger(__name__)

# ── Severity Keywords ─────────────────────────────────────────────────────

_HIGH_SEVERITY: set[str] = {
    "strike", "closure", "blockage", "embargo", "cyberattack", "cyber attack",
    "shutdown", "collapse", "explosion", "seizure", "grounding", "sinking",
    "war", "missile", "attack", "sanction", "ban", "evacuation",
}

_MEDIUM_SEVERITY: set[str] = {
    "delay", "congestion", "backlog", "diversion", "reroute", "queue",
    "bottleneck", "slowdown", "capacity cut", "blank sailing", "suspension",
    "shortage", "disruption", "outage", "tariff", "surcharge",
}

_LOW_SEVERITY: set[str] = {
    "forecast", "outlook", "trend", "update", "advisory", "review",
    "guidance", "report", "analysis", "monitor", "watch",
}


def _severity_weight(signals: list[Signal]) -> float:
    """Scan signal titles+content for severity keywords. Return 0.3-1.0."""
    combined = " ".join(
        f"{s.title or ''} {s.content[:200]}" for s in signals
    ).lower()

    for kw in _HIGH_SEVERITY:
        if kw in combined:
            return 1.0
    for kw in _MEDIUM_SEVERITY:
        if kw in combined:
            return 0.6
    for kw in _LOW_SEVERITY:
        if kw in combined:
            return 0.3
    return 0.5  # default: moderate


def _source_weight(signals: list[Signal]) -> float:
    """Average source weight across signals. Falls back to 0.5."""
    weights = [s.source_weight for s in signals if s.source_weight is not None]
    if not weights:
        return 0.5
    return sum(weights) / len(weights)


def _geographic_weight(event: Event) -> float:
    """Max geo-criticality across event regions."""
    if not event.regions:
        return 0.40  # unknown region → local baseline
    scores = [get_geo_criticality(r) for r in event.regions]
    return max(scores) if scores else 0.40


def _recency_weight(signals: list[Signal]) -> float:
    """Average time-decay across signals. More recent → higher weight."""
    decays = [
        compute_time_decay_from_timestamp(s.created_at)
        for s in signals
        if s.created_at
    ]
    if not decays:
        return 0.5
    return sum(decays) / len(decays)


def _multimodal_multiplier(event: Event) -> float:
    """Multiplier based on number of affected transport modes.

    1 mode → 1.0, 2 modes → 1.2, 3+ modes → 1.5
    """
    mode_count = len(event.transport_modes)
    if mode_count >= 3:
        return 1.5
    if mode_count == 2:
        return 1.2
    return 1.0


# ── Main Scorer ───────────────────────────────────────────────────────────


def compute_impact_score(event: Event, signals: list[Signal]) -> float:
    """Compute a 0-100 impact score for a fused event.

    Formula:
        raw = source_w × severity_w × geo_w × recency_w × multimodal_m × 100
        impact = clamp(raw, 0, 100)
    """
    sw = _source_weight(signals)
    sev = _severity_weight(signals)
    geo = _geographic_weight(event)
    rec = _recency_weight(signals)
    mm = _multimodal_multiplier(event)

    raw = sw * sev * geo * rec * mm * 100
    impact = round(max(0.0, min(100.0, raw)), 1)

    logger.debug(
        f"Impact score: {impact} "
        f"(source={sw:.2f} sev={sev:.2f} geo={geo:.2f} rec={rec:.2f} mm={mm:.1f})"
    )
    return impact


def score_and_classify(event: Event, signals: list[Signal]) -> Event:
    """Score an event and set its priority. Returns mutated event."""
    impact = compute_impact_score(event, signals)
    event.impact_score = impact
    event.priority = classify_priority(impact)
    return event
