"""Functional verification of Decision Engine v1.0 core modules."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.db.event_models import Event, EventStatus, Priority, classify_priority
from app.db.models import Signal
from app.engine.decision_generator import generate_cascade_predictions, generate_decisions
from app.engine.noise_control import filter_noise
from app.scoring.impact_scorer import compute_impact_score


def make_signal(
    i: int,
    source: str = "src",
    title: str = "Signal",
    risk: float = 0.5,
    sw: float = 0.7,
    mode: str = "ocean",
    region: str = "suez_canal",
) -> Signal:
    return Signal(
        id=uuid4(),
        source=f"{source}_{i}",
        tier="P1",
        content=f"Content for {title} {i}",
        title=f"{title} {i}",
        risk_score=risk,
        source_weight=sw,
        geo_criticality=0.9,
        transport_mode=mode,
        region=region,
        created_at=datetime.now(timezone.utc),
    )


def test_noise_control() -> None:
    print("=== TEST: Noise Control ===")
    signals = [
        make_signal(i, risk=0.3 + i * 0.15) for i in range(5)
    ]
    # Add noise: low risk
    signals.append(Signal(
        id=uuid4(), source="reddit_shipping", tier="P3",
        content="Random noise", title="Random discussion",
        risk_score=0.15, source_weight=0.3,
        created_at=datetime.now(timezone.utc),
    ))
    # Add noise: duplicate title
    signals.append(Signal(
        id=uuid4(), source="dup", tier="P2",
        content="Duplicate", title="Signal 0",  # same as first
        risk_score=0.4, source_weight=0.6,
        created_at=datetime.now(timezone.utc),
    ))

    clean = filter_noise(signals)
    print(f"  Input: {len(signals)} signals")
    print(f"  Output: {len(clean)} signals (filtered {len(signals) - len(clean)})")
    assert len(clean) < len(signals), "Should filter some signals"
    assert all((s.risk_score or 0) >= 0.20 for s in clean), "No low-risk signals"
    print("  PASSED\n")


def test_impact_scoring() -> None:
    print("=== TEST: Impact Scoring v2 ===")
    signals = [
        make_signal(i, title="Red Sea chokepoint blockage", risk=0.6 + i * 0.1, sw=0.8)
        for i in range(3)
    ]

    # Single mode
    event_single = Event(
        title="Red Sea chokepoint blockage",
        summary="Multiple reports of vessel diversions",
        impact_score=0, priority=Priority.LOW,
        transport_modes=["ocean"], regions=["suez_canal"],
        confidence=0.75, signal_ids=[s.id for s in signals],
        signal_count=3, source_diversity=3, status=EventStatus.ACTIVE,
    )
    score_1 = compute_impact_score(event_single, signals)

    # Multi-mode (should get 1.2x multiplier)
    event_multi = Event(
        title="Red Sea chokepoint blockage",
        summary="Multiple reports of vessel diversions",
        impact_score=0, priority=Priority.LOW,
        transport_modes=["ocean", "air"], regions=["suez_canal"],
        confidence=0.75, signal_ids=[s.id for s in signals],
        signal_count=3, source_diversity=3, status=EventStatus.ACTIVE,
    )
    score_2 = compute_impact_score(event_multi, signals)

    print(f"  Single mode (ocean): {score_1:.1f}")
    print(f"  Multi mode (ocean+air): {score_2:.1f}")
    print(f"  Multiplier effect: {score_2/score_1:.2f}x (expected ~1.2x)")
    assert score_2 > score_1, "Multi-modal should score higher"
    assert 1.15 <= score_2 / score_1 <= 1.25, "Should be ~1.2x"
    assert classify_priority(score_2) in (Priority.CRITICAL, Priority.HIGH), "Should be HIGH+"
    print("  PASSED\n")


def test_decision_generator() -> None:
    print("=== TEST: Decision Generator ===")
    signals = [
        make_signal(i, title="Suez Canal blockage vessel grounding")
        for i in range(3)
    ]
    event = Event(
        title="Suez Canal blockage — vessel grounding",
        summary="Vessel grounded in Suez Canal causing blockage",
        impact_score=85, priority=Priority.CRITICAL,
        transport_modes=["ocean"], regions=["suez_canal"],
        confidence=0.9, signal_ids=[s.id for s in signals],
        signal_count=3, source_diversity=3, status=EventStatus.ACTIVE,
    )

    decisions = generate_decisions(event, signals)
    print(f"  Decisions generated: {len(decisions)}")
    for d in decisions:
        print(f"    [{d.urgency.upper()}] {d.decision[:80]}")
    assert len(decisions) > 0, "Should generate at least 1 decision"
    assert any("reroute" in d.decision.lower() or "cape" in d.decision.lower() for d in decisions), \
        "Should suggest reroute for chokepoint"
    print("  PASSED\n")


def test_cascade_predictions() -> None:
    print("=== TEST: Cascade Predictions ===")
    event = Event(
        title="Suez Canal disruption",
        summary="Major disruption at Suez Canal",
        impact_score=85, priority=Priority.CRITICAL,
        transport_modes=["ocean"], regions=["suez_canal"],
        confidence=0.9, signal_ids=[], signal_count=3,
        source_diversity=3, status=EventStatus.ACTIVE,
    )

    cascades = generate_cascade_predictions(event)
    print(f"  Cascade effects: {len(cascades)}")
    for c in cascades:
        print(f"    {c.zone} (hop {c.hop}, risk {c.propagated_risk:.2f}, {c.time_horizon_hours})")
    assert len(cascades) > 0, "Suez should have downstream cascade effects"
    zones = {c.zone for c in cascades}
    print(f"  Affected zones: {zones}")
    print("  PASSED\n")


def test_priority_classification() -> None:
    print("=== TEST: Priority Classification ===")
    assert classify_priority(85) == Priority.CRITICAL
    assert classify_priority(70) == Priority.HIGH
    assert classify_priority(50) == Priority.MEDIUM
    assert classify_priority(30) == Priority.LOW
    print("  All thresholds correct")
    print("  PASSED\n")


if __name__ == "__main__":
    test_noise_control()
    test_impact_scoring()
    test_decision_generator()
    test_cascade_predictions()
    test_priority_classification()
    print("=" * 50)
    print("ALL TESTS PASSED — Decision Engine v1.0 verified")
    print("=" * 50)
