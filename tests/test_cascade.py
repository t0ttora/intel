"""Tests for cascade propagation engine."""
from __future__ import annotations

import pytest

from app.engine.cascade import (
    propagate_cascade,
    GEO_GRAPH,
    CascadeResult,
)


class TestCascade:
    """Test BFS cascade propagation."""

    def test_no_propagation_below_threshold(self) -> None:
        result = propagate_cascade("suez_canal", 0.20)
        assert len(result.affected_zones) == 0

    def test_suez_propagation(self) -> None:
        result = propagate_cascade("suez_canal", 0.85)
        assert len(result.affected_zones) > 0
        # Suez should cascade to Mediterranean/Rotterdam
        zones = [n.zone for n in result.affected_zones]
        assert any("med" in z.lower() or "rotterdam" in z.lower() for z in zones)

    def test_max_depth_respected(self) -> None:
        result = propagate_cascade("suez_canal", 0.95)
        for node in result.affected_zones:
            assert node.hop <= 3  # Max depth is 3

    def test_decay_applied(self) -> None:
        result = propagate_cascade("suez_canal", 0.90)
        if len(result.affected_zones) >= 2:
            # Later hops should have lower risk
            hop1 = [n for n in result.affected_zones if n.hop == 1]
            hop2 = [n for n in result.affected_zones if n.hop == 2]
            if hop1 and hop2:
                assert max(n.propagated_risk for n in hop2) <= max(n.propagated_risk for n in hop1)

    def test_no_cycles(self) -> None:
        result = propagate_cascade("suez_canal", 0.95)
        zones = [n.zone for n in result.affected_zones]
        assert len(zones) == len(set(zones)), "Cascade should not visit same zone twice"

    def test_unknown_zone(self) -> None:
        result = propagate_cascade("nonexistent_zone", 0.90)
        assert len(result.affected_zones) == 0

    def test_minimum_risk_filter(self) -> None:
        result = propagate_cascade("suez_canal", 0.50)
        for node in result.affected_zones:
            assert node.propagated_risk >= 0.30  # Min threshold

    def test_geo_graph_connectivity(self) -> None:
        """All zones in the graph should have valid neighbors."""
        for zone, neighbors in GEO_GRAPH.items():
            for neighbor_zone, weight in neighbors:
                assert 0.0 < weight <= 1.0, f"Invalid weight for {zone} -> {neighbor_zone}"
