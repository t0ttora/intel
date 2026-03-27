"""Tests for GRC fusion engine."""
from __future__ import annotations

import pytest

from app.engine.fusion import (
    ActiveEvent,
    compute_grc,
    classify_grc_level,
    compute_grc_with_events,
)


class TestFusion:
    """Test Global Risk Composite calculation."""

    def test_grc_no_events(self) -> None:
        grc = compute_grc([])
        assert grc == 0.0

    def test_grc_single_event(self) -> None:
        grc = compute_grc([0.5])
        assert abs(grc - 0.5) < 0.01

    def test_grc_multiple_events(self) -> None:
        # GRC = 1 - Π(1-Ri) = 1 - (1-0.5)(1-0.5) = 1 - 0.25 = 0.75
        grc = compute_grc([0.5, 0.5])
        assert abs(grc - 0.75) < 0.01

    def test_grc_high_risk(self) -> None:
        grc = compute_grc([0.9, 0.9, 0.9])
        assert grc > 0.95

    def test_grc_low_risk(self) -> None:
        grc = compute_grc([0.1, 0.1])
        # 1 - (0.9)(0.9) = 1 - 0.81 = 0.19
        assert abs(grc - 0.19) < 0.01

    def test_grc_bounded(self) -> None:
        grc = compute_grc([1.0, 1.0])
        assert grc <= 1.0
        grc = compute_grc([0.0, 0.0])
        assert grc >= 0.0

    def test_classify_grc_critical(self) -> None:
        assert classify_grc_level(0.85) == "CRITICAL"

    def test_classify_grc_low(self) -> None:
        assert classify_grc_level(0.10) == "LOW"

    def test_compute_grc_with_events(self) -> None:
        events = [
            ActiveEvent(zone="suez_canal", risk_score=0.8, label="Suez"),
            ActiveEvent(zone="panama_canal", risk_score=0.6, label="Panama"),
        ]
        result = compute_grc_with_events(events)
        assert "grc" in result
        assert result["grc"] > 0.8  # Should be very high
        assert "level" in result
