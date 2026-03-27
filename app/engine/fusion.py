"""Multi-event Global Risk Composite (GRC) computation."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ActiveEvent:
    """An active risk event contributing to the GRC."""

    zone: str
    risk_score: float
    label: str
    event_count: int = 1


def compute_grc(risk_scores: list[float]) -> float:
    """Compute Global Risk Composite: GRC = 1 - product(1 - Ri).

    This formula captures the compounding effect of multiple simultaneous
    risk events — even if each individual risk is moderate, the combined
    probability of at least one event impacting operations is higher.
    """
    if not risk_scores:
        return 0.0

    # Clamp scores to [0, 1)
    clamped = [max(0.0, min(0.999, r)) for r in risk_scores]
    product = math.prod(1.0 - r for r in clamped)
    return round(1.0 - product, 4)


def classify_grc_level(grc: float) -> str:
    """Classify GRC into a risk level."""
    if grc >= 0.80:
        return "CRITICAL"
    elif grc >= 0.60:
        return "HIGH"
    elif grc >= 0.40:
        return "MEDIUM"
    return "LOW"


def compute_grc_with_events(events: list[ActiveEvent]) -> dict:
    """Compute GRC and return full risk overview."""
    risk_scores = [e.risk_score for e in events]
    grc = compute_grc(risk_scores)
    level = classify_grc_level(grc)

    return {
        "grc": grc,
        "level": level,
        "active_events": [
            {
                "zone": e.zone,
                "risk": e.risk_score,
                "label": e.label,
                "event_count": e.event_count,
            }
            for e in sorted(events, key=lambda x: x.risk_score, reverse=True)
        ],
        "event_count": len(events),
    }
