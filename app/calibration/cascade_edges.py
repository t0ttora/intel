"""Weekly cascade edge weight calibration."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.engine.cascade import GEO_GRAPH

logger = logging.getLogger(__name__)


@dataclass
class EdgeCalibration:
    """Result of calibrating a single cascade edge."""

    source_zone: str
    target_zone: str
    old_weight: float
    new_weight: float
    evidence_count: int


async def get_cascade_accuracy(
    conn: AsyncConnection,
    source_zone: str,
    target_zone: str,
    *,
    days: int = 30,
) -> tuple[float, int]:
    """Get accuracy of cascade predictions between two zones.

    Returns (accuracy, sample_count).
    """
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT count(*) as total,
                   count(*) FILTER (WHERE o.accuracy_score >= 0.5) as accurate
            FROM outcomes o
            JOIN signals s ON o.signal_id = s.id
            JOIN alerts a ON a.signal_id = s.id
            WHERE s.geo_zone = %s
              AND a.cascade_data::text LIKE %s
              AND o.created_at >= now() - interval '%s days'
            """,
            (source_zone, f"%{target_zone}%", days),
        )
        row = await cur.fetchone()

    if not row or row["total"] == 0:
        return 0.5, 0

    accuracy = row["accurate"] / row["total"]
    return round(accuracy, 4), row["total"]


async def calibrate_cascade_edges(
    conn: AsyncConnection,
    *,
    days: int = 30,
    learning_rate: float = 0.03,
    min_edge_weight: float = 0.20,
    max_edge_weight: float = 0.95,
) -> list[EdgeCalibration]:
    """Run weekly cascade edge calibration based on outcome data.

    Adjusts edge weights based on how accurately cascades predicted
    downstream effects.
    """
    calibrations: list[EdgeCalibration] = []

    for source_zone, edges in GEO_GRAPH.items():
        for i, (target_zone, old_weight) in enumerate(edges):
            accuracy, count = await get_cascade_accuracy(
                conn, source_zone, target_zone, days=days
            )

            if count < 3:
                # Not enough data — skip calibration
                continue

            # Nudge edge weight toward observed accuracy
            adjustment = learning_rate * (accuracy - 0.5)
            new_weight = old_weight * (1.0 + adjustment)
            new_weight = round(max(min_edge_weight, min(max_edge_weight, new_weight)), 3)

            if abs(new_weight - old_weight) > 0.001:
                # Update in-memory graph (persisted on restart via config)
                GEO_GRAPH[source_zone][i] = (target_zone, new_weight)

                calibrations.append(
                    EdgeCalibration(
                        source_zone=source_zone,
                        target_zone=target_zone,
                        old_weight=old_weight,
                        new_weight=new_weight,
                        evidence_count=count,
                    )
                )

                logger.info(
                    f"Cascade edge {source_zone} → {target_zone}: "
                    f"{old_weight:.3f} → {new_weight:.3f} "
                    f"(accuracy={accuracy:.3f}, n={count})"
                )

    return calibrations
