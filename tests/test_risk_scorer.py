"""Tests for risk scoring engine."""
from __future__ import annotations

import pytest

from app.scoring.risk_scorer import (
    compute_risk_score,
    classify_risk_level,
    assign_tier,
    FormulaWeights,
)


class TestRiskScorer:
    """Test the NOBLE-RSM v2 risk scoring formula."""

    def test_default_weights_sum_to_one(self) -> None:
        w = FormulaWeights()
        total = w.w_anomaly + w.w_source + w.w_geo + w.w_time
        assert abs(total - 1.0) < 0.001

    def test_compute_risk_score_basic(self) -> None:
        score = compute_risk_score(
            anomaly_score=0.5,
            source_weight=0.5,
            geo_criticality=0.5,
            time_decay=0.5,
        )
        # All at 0.5 should give 0.5 with uniform inputs
        assert 0.0 <= score <= 1.0
        assert abs(score - 0.5) < 0.01

    def test_compute_risk_score_high(self) -> None:
        score = compute_risk_score(
            anomaly_score=0.9,
            source_weight=0.9,
            geo_criticality=0.9,
            time_decay=0.9,
        )
        assert score >= 0.8

    def test_compute_risk_score_low(self) -> None:
        score = compute_risk_score(
            anomaly_score=0.1,
            source_weight=0.1,
            geo_criticality=0.1,
            time_decay=0.1,
        )
        assert score <= 0.2

    def test_compute_risk_score_clamped(self) -> None:
        # Even with extreme inputs, should be 0-1
        score = compute_risk_score(
            anomaly_score=1.5,
            source_weight=1.5,
            geo_criticality=1.5,
            time_decay=1.5,
        )
        assert 0.0 <= score <= 1.0

    def test_classify_risk_level_critical(self) -> None:
        assert classify_risk_level(0.85) == "CRITICAL"

    def test_classify_risk_level_high(self) -> None:
        assert classify_risk_level(0.65) == "HIGH"

    def test_classify_risk_level_medium(self) -> None:
        assert classify_risk_level(0.45) == "MEDIUM"

    def test_classify_risk_level_low(self) -> None:
        assert classify_risk_level(0.20) == "LOW"

    def test_assign_tier(self) -> None:
        assert assign_tier(0.90) == "CRITICAL"
        assert assign_tier(0.70) == "HIGH"
        assert assign_tier(0.50) == "MEDIUM"
        assert assign_tier(0.20) == "LOW"

    def test_custom_weights(self) -> None:
        weights = FormulaWeights(w_anomaly=0.5, w_source=0.2, w_geo=0.2, w_time=0.1)
        score = compute_risk_score(
            anomaly_score=1.0,
            source_weight=0.0,
            geo_criticality=0.0,
            time_decay=0.0,
            weights=weights,
        )
        assert abs(score - 0.5) < 0.01
