"""Decision Generator — produce actionable decisions and cascade predictions for events.

Rule-based decision matrix: maps event intent + transport mode combinations to
concrete operational recommendations. No LLM — deterministic and auditable.
"""
from __future__ import annotations

import logging
import re

from app.db.event_models import CascadeEffect, Event, EventDecision
from app.db.models import Signal
from app.engine.cascade import CascadeResult, propagate_cascade
from app.scoring.geo_criticality import detect_geo_zone

logger = logging.getLogger(__name__)

# ── Intent Detection (re-use pattern matching from intent_classifier) ─────

_INTENT_KEYWORDS: dict[str, list[str]] = {
    "chokepoint": [
        "suez", "panama", "malacca", "hormuz", "bab el mandeb", "strait",
        "canal", "blockage", "grounding", "houthi", "reroute", "red sea",
    ],
    "congestion": [
        "congestion", "delay", "queue", "dwell", "backlog", "bottleneck",
        "overcrowded", "berth", "anchorage", "blank sailing",
    ],
    "labor": [
        "strike", "union", "walkout", "lockout", "dock worker", "longshore",
        "picket", "work stoppage", "industrial action",
    ],
    "cyber": [
        "cyber", "ransomware", "hack", "data breach", "malware", "it outage",
        "system failure",
    ],
    "freight": [
        "freight rate", "rate spike", "surcharge", "capacity cut", "gri",
        "bunker", "peak season", "rate increase",
    ],
    "regulatory": [
        "tariff", "sanction", "embargo", "ban", "regulation", "customs",
        "inspection", "imo", "emission", "ets",
    ],
    "weather": [
        "typhoon", "hurricane", "cyclone", "storm", "fog", "flood",
        "drought", "ice", "freeze",
    ],
}


def _detect_intents(event: Event, signals: list[Signal]) -> list[str]:
    """Detect all matching intents from event title + signal content."""
    combined = event.title.lower() + " " + event.summary.lower()
    for s in signals[:5]:
        combined += " " + (s.title or "").lower() + " " + s.content[:150].lower()

    matched: list[str] = []
    for intent, keywords in _INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                matched.append(intent)
                break
    return matched or ["general"]


def _has_mode(event: Event, mode: str) -> bool:
    """Check if event affects a specific transport mode."""
    return mode in event.transport_modes


# ── Decision Rules ────────────────────────────────────────────────────────

# Each rule: (condition_fn, decision_text, urgency)
_DECISION_RULES: list[tuple[str, ...]] = []  # populated below via _generate_for_intent


def _generate_for_intent(
    intent: str, event: Event, signals: list[Signal]
) -> list[EventDecision]:
    """Generate decisions for a specific intent + event context."""

    decisions: list[EventDecision] = []

    if intent == "chokepoint":
        if _has_mode(event, "ocean"):
            decisions.append(EventDecision(
                decision="Evaluate Cape of Good Hope reroute or sea-air conversion via Dubai DWC/Jebel Ali",
                reason=f"Chokepoint disruption detected: {event.title}",
                urgency="critical",
                confidence=event.confidence,
            ))
        if _has_mode(event, "air"):
            decisions.append(EventDecision(
                decision="Pre-position air charter capacity for sea-air conversion demand surge",
                reason="Chokepoint closure will drive ocean-to-air modal shift within 48-72h",
                urgency="high",
                confidence=event.confidence,
            ))
        if not event.transport_modes or len(event.transport_modes) > 1:
            decisions.append(EventDecision(
                decision="Activate multi-modal contingency: review all shipments routing through affected corridor",
                reason=f"Multi-modal impact expected from {event.title}",
                urgency="critical",
                confidence=event.confidence,
            ))

    elif intent == "congestion":
        decisions.append(EventDecision(
            decision="Pre-book alternate port berth; consider inland routing via rail/barge",
            reason=f"Port congestion event: {event.title}",
            urgency="high",
            confidence=event.confidence,
        ))
        if _has_mode(event, "ocean"):
            decisions.append(EventDecision(
                decision="Contact carrier for schedule update; evaluate blank sailing risk on affected service loop",
                reason="Congestion may trigger carrier schedule adjustments within 24-48h",
                urgency="medium",
                confidence=event.confidence * 0.9,
            ))

    elif intent == "labor":
        decisions.append(EventDecision(
            decision="Divert vessels to alternate port; pre-position chassis at secondary terminals",
            reason=f"Labor disruption: {event.title}",
            urgency="critical",
            confidence=event.confidence,
        ))
        decisions.append(EventDecision(
            decision="Accelerate cargo clearance at unaffected ports before strike deadline",
            reason="Pre-strike window: move cargo through while operations continue",
            urgency="high",
            confidence=event.confidence * 0.85,
        ))

    elif intent == "cyber":
        decisions.append(EventDecision(
            decision="Switch to manual customs processing; prepare paper documentation backup",
            reason=f"Cyber incident: {event.title}. Expect 3-5 day processing delays",
            urgency="high",
            confidence=event.confidence,
        ))
        decisions.append(EventDecision(
            decision="Route urgent cargo through unaffected terminals; verify EDI connectivity with alternate carriers",
            reason="System outage may cascade to connected ports within 12-24h",
            urgency="high",
            confidence=event.confidence * 0.8,
        ))

    elif intent == "freight":
        if _has_mode(event, "air"):
            decisions.append(EventDecision(
                decision="Pre-book air charter capacity within 48h before rate ceiling",
                reason=f"Air freight rate pressure: {event.title}",
                urgency="high",
                confidence=event.confidence,
            ))
        if _has_mode(event, "ocean"):
            decisions.append(EventDecision(
                decision="Lock in contract rates; consider spot booking window before next GRI",
                reason=f"Ocean freight rate movement: {event.title}",
                urgency="medium",
                confidence=event.confidence,
            ))

    elif intent == "regulatory":
        decisions.append(EventDecision(
            decision="Review compliance documentation for affected trade lane; consult customs broker",
            reason=f"Regulatory change: {event.title}",
            urgency="medium",
            confidence=event.confidence,
        ))

    elif intent == "weather":
        decisions.append(EventDecision(
            decision="Reroute shipments around affected area; extend ETAs by 24-72h for impacted vessels",
            reason=f"Weather event: {event.title}",
            urgency="high",
            confidence=event.confidence,
        ))

    else:  # general
        decisions.append(EventDecision(
            decision="Monitor situation; prepare contingency plan for affected trade lanes",
            reason=f"Developing situation: {event.title}",
            urgency="medium",
            confidence=event.confidence * 0.7,
        ))

    return decisions


# ── Cascade Predictions ───────────────────────────────────────────────────

_TIME_HORIZONS: dict[int, str] = {
    1: "12-24h",   # direct port impact
    2: "24-72h",   # trade lane ripple
    3: "48-168h",  # modal shift demand
}


def generate_cascade_predictions(event: Event) -> list[CascadeEffect]:
    """Generate cascade predictions by running the existing cascade engine.

    Maps cascade zones to human-readable predictions with time horizons.
    """
    # Find the trigger zone from event content
    trigger_zone = None
    for region in event.regions:
        trigger_zone = region
        break

    if not trigger_zone:
        # Try to detect from title
        trigger_zone = detect_geo_zone(event.title + " " + event.summary)

    if not trigger_zone:
        return []

    # Run the cascade engine
    risk = event.impact_score / 100.0  # normalize to 0-1
    cascade_result: CascadeResult = propagate_cascade(trigger_zone, risk)

    effects: list[CascadeEffect] = []
    for node in cascade_result.affected_zones:
        effects.append(CascadeEffect(
            zone=node.zone,
            description=f"Cascade from {trigger_zone}: {node.zone} affected (hop {node.hop})",
            propagated_risk=node.propagated_risk,
            hop=node.hop,
            time_horizon_hours=_TIME_HORIZONS.get(node.hop, "72-168h"),
        ))

    logger.info(
        f"Cascade for '{trigger_zone}' (risk={risk:.2f}): "
        f"{len(effects)} downstream effects, max depth {cascade_result.max_depth_reached}"
    )
    return effects


# ── Main Entry Point ──────────────────────────────────────────────────────


def generate_decisions(event: Event, signals: list[Signal]) -> list[EventDecision]:
    """Generate all decisions for an event based on detected intents."""
    intents = _detect_intents(event, signals)
    all_decisions: list[EventDecision] = []

    for intent in intents:
        all_decisions.extend(_generate_for_intent(intent, event, signals))

    # Deduplicate by decision text
    seen: set[str] = set()
    unique: list[EventDecision] = []
    for d in all_decisions:
        if d.decision not in seen:
            seen.add(d.decision)
            unique.append(d)

    logger.info(
        f"Generated {len(unique)} decisions for event '{event.title[:50]}' "
        f"(intents: {intents})"
    )
    return unique
