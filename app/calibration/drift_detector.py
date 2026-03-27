"""Drift detection + alerting when source weight delta > 0.20 from base."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from psycopg import AsyncConnection

from app.db.queries import get_all_source_weights

logger = logging.getLogger(__name__)

DRIFT_THRESHOLD = 0.20


@dataclass
class DriftAlert:
    """Alert when a source weight has drifted significantly from its base."""

    source: str
    current_weight: float
    base_weight: float
    delta: float
    direction: str  # "up" or "down"


async def detect_drifts(conn: AsyncConnection) -> list[DriftAlert]:
    """Check all sources for weight drift beyond threshold."""
    source_weights = await get_all_source_weights(conn)
    drifts: list[DriftAlert] = []

    for sw in source_weights:
        delta = sw.current_weight - sw.base_weight

        if abs(delta) >= DRIFT_THRESHOLD:
            direction = "up" if delta > 0 else "down"
            alert = DriftAlert(
                source=sw.source,
                current_weight=sw.current_weight,
                base_weight=sw.base_weight,
                delta=round(delta, 4),
                direction=direction,
            )
            drifts.append(alert)
            logger.warning(
                f"Source drift detected: {sw.source} "
                f"{sw.base_weight:.3f} → {sw.current_weight:.3f} "
                f"(delta={delta:+.3f}, direction={direction})"
            )

    return drifts


def check_single_drift(
    current_weight: float,
    base_weight: float,
) -> DriftAlert | None:
    """Check a single source for drift."""
    delta = current_weight - base_weight
    if abs(delta) >= DRIFT_THRESHOLD:
        direction = "up" if delta > 0 else "down"
        return DriftAlert(
            source="",  # Caller should set this
            current_weight=current_weight,
            base_weight=base_weight,
            delta=round(delta, 4),
            direction=direction,
        )
    return None
