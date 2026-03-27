"""Monthly formula weight recalibration (Pearson correlation)."""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.scoring.risk_scorer import FormulaWeights

logger = logging.getLogger(__name__)


@dataclass
class CorrelationResult:
    """Pearson correlation between a factor and outcome accuracy."""

    factor: str
    correlation: float
    sample_size: int


def _pearson_correlation(x: list[float], y: list[float]) -> float:
    """Compute Pearson correlation coefficient between two lists."""
    n = len(x)
    if n < 3:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))

    if denom_x == 0 or denom_y == 0:
        return 0.0

    return numerator / (denom_x * denom_y)


async def compute_factor_correlations(
    conn: AsyncConnection,
    *,
    days: int = 90,
) -> list[CorrelationResult]:
    """Compute Pearson correlation between each risk factor and outcome accuracy."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT s.anomaly_score, s.source_weight, s.geo_criticality, s.time_decay,
                   o.accuracy_score
            FROM outcomes o
            JOIN signals s ON o.signal_id = s.id
            WHERE o.accuracy_score IS NOT NULL
              AND o.created_at >= now() - interval '%s days'
              AND s.anomaly_score IS NOT NULL
              AND s.source_weight IS NOT NULL
              AND s.geo_criticality IS NOT NULL
              AND s.time_decay IS NOT NULL
            """,
            (days,),
        )
        rows = await cur.fetchall()

    if len(rows) < 10:
        logger.warning(f"Insufficient data for formula recalibration: {len(rows)} rows")
        return []

    accuracies = [float(r["accuracy_score"]) for r in rows]
    factors = {
        "anomaly": [float(r["anomaly_score"]) for r in rows],
        "source": [float(r["source_weight"]) for r in rows],
        "geo": [float(r["geo_criticality"]) for r in rows],
        "time": [float(r["time_decay"]) for r in rows],
    }

    results: list[CorrelationResult] = []
    for factor_name, values in factors.items():
        corr = _pearson_correlation(values, accuracies)
        results.append(
            CorrelationResult(
                factor=factor_name,
                correlation=round(corr, 4),
                sample_size=len(rows),
            )
        )

    return results


def rebalance_weights(correlations: list[CorrelationResult]) -> FormulaWeights:
    """Rebalance formula weights based on correlation strengths.

    Higher correlation with accuracy → higher weight.
    Weights are normalized to sum to 1.0.
    Minimum weight is 0.10 to prevent any factor from being zeroed out.
    """
    MIN_WEIGHT = 0.10

    if not correlations:
        return FormulaWeights()

    # Use absolute correlation (direction doesn't matter for weight)
    raw_weights: dict[str, float] = {}
    for cr in correlations:
        raw_weights[cr.factor] = max(MIN_WEIGHT, abs(cr.correlation))

    # Normalize to sum to 1.0
    total = sum(raw_weights.values())
    if total == 0:
        return FormulaWeights()

    normalized = {k: round(v / total, 4) for k, v in raw_weights.items()}

    return FormulaWeights(
        w_anomaly=normalized.get("anomaly", 0.4),
        w_source=normalized.get("source", 0.2),
        w_geo=normalized.get("geo", 0.2),
        w_time=normalized.get("time", 0.2),
    )


async def recalibrate_formula(
    conn: AsyncConnection,
    *,
    days: int = 90,
) -> FormulaWeights:
    """Run full formula recalibration and return new weights."""
    correlations = await compute_factor_correlations(conn, days=days)

    if not correlations:
        logger.info("No correlation data — keeping current formula weights")
        return FormulaWeights()

    new_weights = rebalance_weights(correlations)

    logger.info(
        f"Formula recalibrated: anomaly={new_weights.w_anomaly}, "
        f"source={new_weights.w_source}, geo={new_weights.w_geo}, "
        f"time={new_weights.w_time}"
    )

    return new_weights
