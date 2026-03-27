"""NOBLE-RSM v2 — composite risk score calculation."""
from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default formula weights (adaptive — loaded from DB when available)
DEFAULT_W_ANOMALY = 0.4
DEFAULT_W_SOURCE = 0.2
DEFAULT_W_GEO = 0.2
DEFAULT_W_TIME = 0.2


@dataclass
class FormulaWeights:
    """Weights for the NOBLE-RSM risk score formula."""

    w_anomaly: float = DEFAULT_W_ANOMALY
    w_source: float = DEFAULT_W_SOURCE
    w_geo: float = DEFAULT_W_GEO
    w_time: float = DEFAULT_W_TIME


@dataclass
class RiskComponents:
    """Individual components of a risk score calculation."""

    anomaly_score: float
    source_weight: float
    geo_criticality: float
    time_decay: float
    risk_score: float
    risk_level: str


# Risk thresholds
CRITICAL_THRESHOLD = 0.80
HIGH_THRESHOLD = 0.60
MEDIUM_THRESHOLD = 0.40


def classify_risk_level(score: float) -> str:
    """Classify a risk score into a risk level."""
    if score >= CRITICAL_THRESHOLD:
        return "CRITICAL"
    elif score >= HIGH_THRESHOLD:
        return "HIGH"
    elif score >= MEDIUM_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def compute_risk_score(
    anomaly_score: float,
    source_weight: float,
    geo_criticality: float,
    time_decay_val: float,
    weights: FormulaWeights | None = None,
) -> RiskComponents:
    """Compute the composite risk score using NOBLE-RSM v2.

    RISK_SCORE = (
        anomaly_score   * w_anomaly +
        source_weight   * w_source  +
        geo_criticality * w_geo     +
        time_decay      * w_time
    )
    """
    if weights is None:
        weights = FormulaWeights()

    # Clamp inputs to [0, 1]
    anomaly_score = max(0.0, min(1.0, anomaly_score))
    source_weight = max(0.0, min(1.0, source_weight))
    geo_criticality = max(0.0, min(1.0, geo_criticality))
    time_decay_val = max(0.0, min(1.0, time_decay_val))

    risk_score = (
        anomaly_score * weights.w_anomaly
        + source_weight * weights.w_source
        + geo_criticality * weights.w_geo
        + time_decay_val * weights.w_time
    )

    risk_score = round(max(0.0, min(1.0, risk_score)), 4)
    risk_level = classify_risk_level(risk_score)

    return RiskComponents(
        anomaly_score=anomaly_score,
        source_weight=source_weight,
        geo_criticality=geo_criticality,
        time_decay=time_decay_val,
        risk_score=risk_score,
        risk_level=risk_level,
    )


def assign_tier(risk_score: float, source: str) -> str:
    """Assign a priority tier based on risk score and source authority.

    P0: CRITICAL events from authoritative sources
    P1: HIGH or any CRITICAL from lower-authority sources
    P2: MEDIUM
    P3: LOW
    """
    authoritative_sources = {"imo", "ukmto", "carrier_direct", "ais"}

    if risk_score >= CRITICAL_THRESHOLD:
        return "P0" if source in authoritative_sources else "P1"
    elif risk_score >= HIGH_THRESHOLD:
        return "P1"
    elif risk_score >= MEDIUM_THRESHOLD:
        return "P2"
    return "P3"
