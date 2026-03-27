"""Anomaly score computation (statistical deviation from baseline)."""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class BaselineStats:
    """Baseline statistics for a metric."""

    mean: float
    std_dev: float
    p95: float


# Default baselines per metric type (bootstrapped values)
DEFAULT_BASELINES: dict[str, BaselineStats] = {
    "dwell_time": BaselineStats(mean=6.0, std_dev=2.5, p95=11.0),
    "route_deviation_km": BaselineStats(mean=50.0, std_dev=30.0, p95=110.0),
    "freight_index_delta_pct": BaselineStats(mean=1.5, std_dev=2.0, p95=5.5),
    "vessel_count_delta": BaselineStats(mean=5.0, std_dev=3.0, p95=11.0),
    "queue_length": BaselineStats(mean=8.0, std_dev=4.0, p95=16.0),
}


def compute_anomaly_score(
    observed_value: float,
    metric_type: str,
    baseline: BaselineStats | None = None,
) -> float:
    """Compute anomaly score as normalized z-score deviation from baseline.

    Returns a value in [0, 1]:
    - 0.0: value is at or below the baseline mean
    - 0.5: value is ~2 std devs above mean
    - 1.0: extreme deviation (>= 4 std devs)
    """
    if baseline is None:
        baseline = DEFAULT_BASELINES.get(metric_type)
        if baseline is None:
            # Unknown metric — return moderate anomaly
            return 0.5

    if baseline.std_dev <= 0:
        return 0.5

    z_score = (observed_value - baseline.mean) / baseline.std_dev

    if z_score <= 0:
        return 0.0

    # Sigmoid-based normalization: maps z-score to [0, 1]
    # z=2 → ~0.5, z=4 → ~0.88, z=6 → ~0.95
    anomaly = 1.0 / (1.0 + math.exp(-0.8 * (z_score - 2.5)))

    return round(max(0.0, min(1.0, anomaly)), 4)


# Maritime/logistics keywords for density-based anomaly detection
_ANOMALY_KEYWORDS = {
    "disruption", "closure", "blockage", "delay", "congestion", "grounding",
    "collision", "attack", "warning", "alert", "emergency", "sanctions",
    "detention", "seizure", "piracy", "storm", "typhoon", "hurricane",
    "strike", "port", "canal", "strait", "embargo", "shortage", "surge",
    "diversion", "reroute", "idle", "backlog", "incident", "accident",
}


def _compute_keyword_density(text: str) -> float:
    """Compute keyword density as fraction of words matching anomaly keywords."""
    words = text.lower().split()
    if not words:
        return 0.0
    matches = sum(1 for w in words if w.strip(".,;:!?()\"'") in _ANOMALY_KEYWORDS)
    return matches / len(words)


def compute_text_anomaly(text: str, avg_density: float = 0.02) -> float:
    """Compute anomaly score for text-based signals based on keyword density.

    Higher keyword density relative to average = more anomalous/relevant.
    """
    keyword_density = _compute_keyword_density(text)

    if avg_density <= 0:
        return 0.5

    ratio = keyword_density / avg_density if avg_density > 0 else 0.0

    if ratio <= 1.0:
        return 0.1

    # Logarithmic scaling: ratio 2x → ~0.4, 5x → ~0.7, 10x → ~0.85
    return round(min(1.0, 0.3 * math.log2(ratio)), 4)
