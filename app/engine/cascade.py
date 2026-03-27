"""Cascade propagation engine — geo-dependency graph, BFS, decay."""
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Geo-dependency graph: zone → [(downstream_zone, edge_weight), ...]
GEO_GRAPH: dict[str, list[tuple[str, float]]] = {
    "suez_canal": [
        ("rotterdam_congestion", 0.9),
        ("freight_spike_asia_eu", 0.8),
        ("cape_reroute", 0.7),
        ("singapore_overload", 0.6),
    ],
    "bab_el_mandeb": [
        ("suez_avoidance", 0.85),
        ("insurance_spike", 0.7),
        ("cape_reroute", 0.7),
    ],
    "panama_canal": [
        ("la_longbeach_delay", 0.8),
        ("freight_spike_transpacific", 0.7),
    ],
    "shanghai": [
        ("blank_sailing_wave", 0.8),
        ("la_longbeach_queue_drop", 0.7),
        ("freight_drop_transpacific", 0.6),
    ],
    "strait_of_malacca": [
        ("singapore_congestion", 0.85),
        ("china_reroute", 0.6),
    ],
    "rotterdam": [
        ("hamburg_overflow", 0.6),
        ("antwerp_diversion", 0.5),
    ],
    "suez_avoidance": [
        ("rotterdam_delay", 0.9),
        ("freight_spike_asia_eu", 0.8),
    ],
    "cape_reroute": [
        ("cape_congestion", 0.6),
    ],
}

MAX_CASCADE_DEPTH = 3
DECAY_PER_HOP = 0.85
MIN_PROPAGATED_RISK = 0.30


@dataclass
class CascadeNode:
    """A node in the cascade propagation result."""

    zone: str
    propagated_risk: float
    hop: int
    parent_zone: str | None = None


@dataclass
class CascadeResult:
    """Full cascade propagation result."""

    trigger_zone: str
    trigger_risk: float
    affected_zones: list[CascadeNode] = field(default_factory=list)
    max_depth_reached: int = 0
    pruned_branches: int = 0


def propagate_cascade(trigger_zone: str, trigger_risk: float) -> CascadeResult:
    """BFS cascade propagation through the geo-dependency graph.

    Propagation rules:
    - Max depth: 3 hops
    - Decay: 0.85 per hop
    - Pruning: propagated risk < 0.30
    - Cycle detection: each zone visited at most once
    """
    result = CascadeResult(trigger_zone=trigger_zone, trigger_risk=trigger_risk)

    queue: deque[tuple[str, float, int, str | None]] = deque()
    queue.append((trigger_zone, trigger_risk, 0, None))
    visited: set[str] = set()
    pruned = 0

    while queue:
        zone, risk, hop, parent = queue.popleft()

        if zone in visited:
            continue
        if hop > MAX_CASCADE_DEPTH:
            continue

        visited.add(zone)

        # Don't add the trigger zone itself to results
        if zone != trigger_zone:
            result.affected_zones.append(
                CascadeNode(
                    zone=zone,
                    propagated_risk=round(risk, 3),
                    hop=hop,
                    parent_zone=parent,
                )
            )
            result.max_depth_reached = max(result.max_depth_reached, hop)

        # Propagate to downstream zones
        for downstream_zone, edge_weight in GEO_GRAPH.get(zone, []):
            propagated = risk * edge_weight * DECAY_PER_HOP
            if propagated >= MIN_PROPAGATED_RISK:
                queue.append((downstream_zone, propagated, hop + 1, zone))
            else:
                pruned += 1

    result.pruned_branches = pruned
    return result


def get_downstream_zones(zone: str) -> list[tuple[str, float]]:
    """Get immediate downstream zones and edge weights."""
    return GEO_GRAPH.get(zone, [])


def get_all_zones() -> list[str]:
    """Return all zones in the geo-dependency graph."""
    zones: set[str] = set()
    for source, targets in GEO_GRAPH.items():
        zones.add(source)
        for target, _ in targets:
            zones.add(target)
    return sorted(zones)
