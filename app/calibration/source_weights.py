"""Online source weight calibration (per resolved signal)."""
from __future__ import annotations

import logging

from psycopg import AsyncConnection

from app.db.queries import get_all_source_weights, get_source_accuracy, update_source_weight

logger = logging.getLogger(__name__)

DEFAULT_LEARNING_RATE = 0.05


def calibrate_source_weight(
    old_weight: float,
    accuracy: float,
    floor: float,
    ceiling: float,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> float:
    """Adjust source weight after outcome resolved.

    Nudges weight up if accuracy > 0.5, down if < 0.5.
    Clamped between floor and ceiling to prevent runaway calibration.
    """
    adjustment = learning_rate * (accuracy - 0.5)
    new_weight = old_weight * (1.0 + adjustment)
    return round(max(floor, min(ceiling, new_weight)), 4)


async def calibrate_all_sources(
    conn: AsyncConnection,
    *,
    days: int = 30,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> dict[str, dict]:
    """Run calibration for all sources based on recent outcomes.

    Returns a dict of {source: {old_weight, new_weight, accuracy, delta}}.
    """
    source_weights = await get_all_source_weights(conn)
    results: dict[str, dict] = {}

    for sw in source_weights:
        accuracy = await get_source_accuracy(conn, sw.source, days=days)

        new_weight = calibrate_source_weight(
            old_weight=sw.current_weight,
            accuracy=accuracy,
            floor=sw.floor_weight,
            ceiling=sw.ceiling_weight,
            learning_rate=learning_rate,
        )

        delta = round(new_weight - sw.current_weight, 4)

        if abs(delta) > 0.0001:
            await update_source_weight(
                conn,
                sw.source,
                new_weight=new_weight,
            )
            logger.info(
                f"Calibrated {sw.source}: {sw.current_weight:.4f} → {new_weight:.4f} "
                f"(accuracy={accuracy:.4f}, delta={delta:+.4f})"
            )

        results[sw.source] = {
            "old_weight": sw.current_weight,
            "new_weight": new_weight,
            "accuracy": accuracy,
            "delta": delta,
        }

    return results


async def calibrate_single_source(
    conn: AsyncConnection,
    source: str,
    accuracy: float,
    *,
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> float | None:
    """Calibrate a single source after an outcome is resolved."""
    from app.db.queries import get_source_weight

    sw = await get_source_weight(conn, source)
    if sw is None:
        logger.warning(f"Unknown source for calibration: {source}")
        return None

    new_weight = calibrate_source_weight(
        old_weight=sw.current_weight,
        accuracy=accuracy,
        floor=sw.floor_weight,
        ceiling=sw.ceiling_weight,
        learning_rate=learning_rate,
    )

    await update_source_weight(
        conn,
        source,
        new_weight=new_weight,
        total_signals=(sw.total_signals + 1),
        total_accurate=(sw.total_accurate + (1 if accuracy >= 0.5 else 0)),
    )

    return new_weight
