"""Tests for scenario simulation."""
from __future__ import annotations

import pytest

from app.engine.scenarios import simulate_scenario, estimate_shipment_impact, SCENARIO_CONFIGS


class TestScenarios:
    """Test scenario simulation and impact estimation."""

    def test_all_intents_have_config(self) -> None:
        expected_intents = ["chokepoint", "congestion", "regulatory", "freight", "carrier"]
        for intent in expected_intents:
            assert intent in SCENARIO_CONFIGS

    def test_simulate_chokepoint(self) -> None:
        scenario = simulate_scenario("chokepoint", risk_score=0.8, geo_criticality=0.9)
        assert 0.0 <= scenario.reroute_probability <= 1.0
        assert scenario.delay_distribution.p10 <= scenario.delay_distribution.p50
        assert scenario.delay_distribution.p50 <= scenario.delay_distribution.p90
        assert scenario.cost_distribution.p10 <= scenario.cost_distribution.p50
        assert scenario.cost_distribution.p50 <= scenario.cost_distribution.p90

    def test_simulate_congestion(self) -> None:
        scenario = simulate_scenario("congestion", risk_score=0.6, geo_criticality=0.7)
        assert scenario.delay_distribution.unit == "days"
        assert scenario.cost_distribution.unit == "USD/TEU"

    def test_higher_risk_higher_impact(self) -> None:
        low = simulate_scenario("chokepoint", risk_score=0.3, geo_criticality=0.5)
        high = simulate_scenario("chokepoint", risk_score=0.9, geo_criticality=0.9)
        assert high.delay_distribution.p50 >= low.delay_distribution.p50

    def test_shipment_impact_scales_with_teu(self) -> None:
        scenario = simulate_scenario("chokepoint", risk_score=0.7, geo_criticality=0.8)
        impact_1 = estimate_shipment_impact(scenario, teu=1)
        impact_10 = estimate_shipment_impact(scenario, teu=10)
        assert impact_10["cost_p50_usd"] > impact_1["cost_p50_usd"]

    def test_unknown_intent_fallback(self) -> None:
        # Should not crash, should use some default
        scenario = simulate_scenario("unknown_intent", risk_score=0.5, geo_criticality=0.5)
        assert scenario is not None

    def test_scenario_distributions_positive(self) -> None:
        for intent in SCENARIO_CONFIGS:
            scenario = simulate_scenario(intent, risk_score=0.5, geo_criticality=0.5)
            assert scenario.delay_distribution.p10 >= 0
            assert scenario.cost_distribution.p10 >= 0
