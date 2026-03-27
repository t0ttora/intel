"""Probabilistic scenario simulation (5 intent types, p10/p50/p90)."""
from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Distribution:
    """A p10/p50/p90 distribution."""

    p10: float
    p50: float
    p90: float
    unit: str


@dataclass
class Scenario:
    """A probabilistic scenario simulation result."""

    intent: str
    reroute_probability: float
    delay_distribution: Distribution
    cost_distribution: Distribution
    description: str


# Base scenario parameters by intent type
SCENARIO_CONFIGS: dict[str, dict] = {
    "chokepoint": {
        "base_reroute_prob": 0.65,
        "delay_base": {"p10": 3, "p50": 7, "p90": 14},
        "cost_base": {"p10": 800, "p50": 1200, "p90": 2000},
        "description": "Chokepoint disruption — vessels may need to reroute via alternative passages",
    },
    "congestion": {
        "base_reroute_prob": 0.30,
        "delay_base": {"p10": 2, "p50": 5, "p90": 10},
        "cost_base": {"p10": 400, "p50": 800, "p90": 1500},
        "description": "Port/channel congestion — increased wait times and potential diversions",
    },
    "regulatory": {
        "base_reroute_prob": 0.15,
        "delay_base": {"p10": 1, "p50": 3, "p90": 7},
        "cost_base": {"p10": 200, "p50": 500, "p90": 1200},
        "description": "Regulatory change — compliance delays and potential route adjustments",
    },
    "freight": {
        "base_reroute_prob": 0.10,
        "delay_base": {"p10": 0, "p50": 1, "p90": 3},
        "cost_base": {"p10": 100, "p50": 300, "p90": 800},
        "description": "Freight market shift — rate changes affecting total shipment cost",
    },
    "carrier": {
        "base_reroute_prob": 0.25,
        "delay_base": {"p10": 2, "p50": 4, "p90": 8},
        "cost_base": {"p10": 300, "p50": 700, "p90": 1300},
        "description": "Carrier operational change — blank sailings, service restructuring",
    },
}


def simulate_scenario(
    intent: str,
    risk_score: float,
    geo_criticality: float = 0.5,
) -> Scenario:
    """Simulate a probabilistic scenario for a given intent and risk level.

    Scales the base distributions by the risk score and geo-criticality
    to produce context-aware p10/p50/p90 distributions.
    """
    config = SCENARIO_CONFIGS.get(intent, SCENARIO_CONFIGS["chokepoint"])

    # Scale factor: higher risk and geo-criticality amplify impact
    scale = 0.5 + risk_score * 0.8 + geo_criticality * 0.2

    # Reroute probability scales with risk
    reroute_prob = min(0.99, config["base_reroute_prob"] * (0.5 + risk_score))

    # Delay distribution (days)
    delay_base = config["delay_base"]
    delay = Distribution(
        p10=round(delay_base["p10"] * scale, 1),
        p50=round(delay_base["p50"] * scale, 1),
        p90=round(delay_base["p90"] * scale, 1),
        unit="days",
    )

    # Cost distribution (USD/TEU)
    cost_base = config["cost_base"]
    cost = Distribution(
        p10=round(cost_base["p10"] * scale),
        p50=round(cost_base["p50"] * scale),
        p90=round(cost_base["p90"] * scale),
        unit="USD/TEU",
    )

    return Scenario(
        intent=intent,
        reroute_probability=round(reroute_prob, 2),
        delay_distribution=delay,
        cost_distribution=cost,
        description=config["description"],
    )


def estimate_shipment_impact(
    scenario: Scenario,
    shipment_teu: int = 1,
) -> dict:
    """Estimate total cost impact for a specific shipment."""
    return {
        "delay_p50_days": scenario.delay_distribution.p50,
        "cost_p50_usd": round(scenario.cost_distribution.p50 * shipment_teu),
        "cost_p90_usd": round(scenario.cost_distribution.p90 * shipment_teu),
        "reroute_probability": scenario.reroute_probability,
    }
