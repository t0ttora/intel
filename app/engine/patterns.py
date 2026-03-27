"""AIS pattern detection — cluster, dark fleet, reroute, blank sailing."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    """Types of detectable shipping patterns."""

    VESSEL_CLUSTER = "vessel_cluster"
    DARK_FLEET = "dark_fleet"
    REROUTE = "reroute"
    BLANK_SAILING = "blank_sailing"
    CONGESTION = "congestion"
    DWELL_ANOMALY = "dwell_anomaly"


@dataclass
class DetectedPattern:
    """A detected shipping pattern."""

    pattern_type: PatternType
    zone: str
    confidence: float
    description: str
    vessel_count: int = 0
    anomaly_score: float = 0.0


def detect_vessel_cluster(
    zone: str,
    current_count: int,
    baseline_count: float,
    std_dev: float,
) -> DetectedPattern | None:
    """Detect abnormal vessel clustering in a zone.

    Triggers when current count exceeds baseline + 2 * std_dev.
    """
    if std_dev <= 0:
        return None

    z_score = (current_count - baseline_count) / std_dev

    if z_score < 2.0:
        return None

    confidence = min(1.0, z_score / 5.0)

    return DetectedPattern(
        pattern_type=PatternType.VESSEL_CLUSTER,
        zone=zone,
        confidence=round(confidence, 3),
        description=(
            f"Abnormal vessel cluster in {zone}: {current_count} vessels "
            f"(baseline: {baseline_count:.0f} ± {std_dev:.1f})"
        ),
        vessel_count=current_count,
        anomaly_score=round(min(1.0, (z_score - 2.0) / 3.0), 4),
    )


def detect_dwell_anomaly(
    zone: str,
    current_dwell_hours: float,
    baseline_hours: float,
    p95_hours: float,
) -> DetectedPattern | None:
    """Detect abnormal dwell times (vessels waiting longer than usual)."""
    if current_dwell_hours <= p95_hours:
        return None

    ratio = current_dwell_hours / baseline_hours if baseline_hours > 0 else 5.0
    confidence = min(1.0, (ratio - 1.0) / 3.0)

    return DetectedPattern(
        pattern_type=PatternType.DWELL_ANOMALY,
        zone=zone,
        confidence=round(confidence, 3),
        description=(
            f"Dwell time anomaly in {zone}: {current_dwell_hours:.1f}h "
            f"(baseline: {baseline_hours:.1f}h, p95: {p95_hours:.1f}h)"
        ),
        anomaly_score=round(min(1.0, (ratio - 1.5) / 2.5), 4),
    )


def detect_reroute_pattern(
    zone: str,
    rerouted_vessels: int,
    total_vessels: int,
) -> DetectedPattern | None:
    """Detect mass rerouting (e.g., Cape of Good Hope instead of Suez)."""
    if total_vessels <= 0:
        return None

    reroute_ratio = rerouted_vessels / total_vessels

    if reroute_ratio < 0.15:  # Less than 15% rerouting = normal
        return None

    confidence = min(1.0, reroute_ratio / 0.5)

    return DetectedPattern(
        pattern_type=PatternType.REROUTE,
        zone=zone,
        confidence=round(confidence, 3),
        description=(
            f"Reroute pattern in {zone}: {rerouted_vessels}/{total_vessels} vessels "
            f"({reroute_ratio:.0%}) taking alternative routes"
        ),
        vessel_count=rerouted_vessels,
        anomaly_score=round(min(1.0, reroute_ratio * 1.5), 4),
    )


def detect_blank_sailing(
    route: str,
    cancelled_sailings: int,
    total_scheduled: int,
) -> DetectedPattern | None:
    """Detect blank sailing patterns (carriers cancelling scheduled services)."""
    if total_scheduled <= 0:
        return None

    cancel_ratio = cancelled_sailings / total_scheduled

    if cancel_ratio < 0.10:  # Less than 10% = normal operations
        return None

    confidence = min(1.0, cancel_ratio / 0.3)

    return DetectedPattern(
        pattern_type=PatternType.BLANK_SAILING,
        zone=route,
        confidence=round(confidence, 3),
        description=(
            f"Blank sailing wave on {route}: {cancelled_sailings}/{total_scheduled} "
            f"sailings cancelled ({cancel_ratio:.0%})"
        ),
        anomaly_score=round(min(1.0, cancel_ratio * 2.0), 4),
    )


def detect_dark_fleet(
    zone: str,
    ais_off_vessels: int,
    total_vessels: int,
) -> DetectedPattern | None:
    """Detect dark fleet activity (vessels with AIS transponders off)."""
    if total_vessels <= 0:
        return None

    dark_ratio = ais_off_vessels / total_vessels

    if dark_ratio < 0.05:  # Less than 5% = normal
        return None

    confidence = min(1.0, dark_ratio / 0.2)

    return DetectedPattern(
        pattern_type=PatternType.DARK_FLEET,
        zone=zone,
        confidence=round(confidence, 3),
        description=(
            f"Dark fleet activity in {zone}: {ais_off_vessels}/{total_vessels} "
            f"vessels with AIS off ({dark_ratio:.0%})"
        ),
        vessel_count=ais_off_vessels,
        anomaly_score=round(min(1.0, dark_ratio * 3.0), 4),
    )
