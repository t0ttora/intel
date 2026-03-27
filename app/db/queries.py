"""All SQL queries as typed async functions — no raw SQL in routes."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.db.models import (
    Alert,
    AlertCreate,
    Outcome,
    OutcomeCreate,
    Signal,
    SignalCreate,
    SourceWeight,
)

logger = logging.getLogger(__name__)


# ── Signals ───────────────────────────────────────────────────────────────


async def insert_signal(conn: AsyncConnection, signal: SignalCreate) -> UUID:
    """Insert a new signal and return its ID."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO signals (source, tier, geo_zone, title, content, url,
                                 risk_score, anomaly_score, source_weight,
                                 geo_criticality, time_decay, embedding_id, expires_at)
            VALUES (%(source)s, %(tier)s, %(geo_zone)s, %(title)s, %(content)s, %(url)s,
                    %(risk_score)s, %(anomaly_score)s, %(source_weight)s,
                    %(geo_criticality)s, %(time_decay)s, %(embedding_id)s, %(expires_at)s)
            RETURNING id
            """,
            signal.model_dump(),
        )
        row = await cur.fetchone()
        await conn.commit()
        return row[0]  # type: ignore[index]


async def get_signal_by_id(conn: AsyncConnection, signal_id: UUID) -> Signal | None:
    """Fetch a single signal by ID."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            "SELECT * FROM signals WHERE id = %s",
            (signal_id,),
        )
        row = await cur.fetchone()
        return Signal(**row) if row else None


async def get_signals(
    conn: AsyncConnection,
    *,
    tier: str | None = None,
    geo_zone: str | None = None,
    min_risk_score: float | None = None,
    last_hours: float | None = None,
    limit: int = 50,
) -> list[Signal]:
    """Fetch signals with optional filters."""
    conditions: list[str] = []
    params: dict[str, Any] = {"limit": limit}

    if tier:
        conditions.append("tier = %(tier)s")
        params["tier"] = tier
    if geo_zone:
        conditions.append("geo_zone = %(geo_zone)s")
        params["geo_zone"] = geo_zone
    if min_risk_score is not None:
        conditions.append("risk_score >= %(min_risk_score)s")
        params["min_risk_score"] = min_risk_score
    if last_hours is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=last_hours)
        conditions.append("created_at >= %(cutoff)s")
        params["cutoff"] = cutoff

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    query = f"SELECT * FROM signals {where} ORDER BY created_at DESC LIMIT %(limit)s"

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(query, params)
        rows = await cur.fetchall()
        return [Signal(**row) for row in rows]


async def get_signal_count(conn: AsyncConnection, *, last_hours: float = 24) -> int:
    """Count signals in the given time window."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=last_hours)
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT count(*) FROM signals WHERE created_at >= %s",
            (cutoff,),
        )
        row = await cur.fetchone()
        return row[0] if row else 0  # type: ignore[index]


async def get_signal_stats(conn: AsyncConnection, *, last_hours: float = 24) -> dict[str, Any]:
    """Get signal volume breakdown by source and tier."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=last_hours)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                count(*) as total,
                count(*) FILTER (WHERE tier = 'P0') as p0_count,
                count(*) FILTER (WHERE tier = 'P1') as p1_count,
                count(*) FILTER (WHERE tier = 'P2') as p2_count,
                count(*) FILTER (WHERE tier = 'P3') as p3_count
            FROM signals
            WHERE created_at >= %s
            """,
            (cutoff,),
        )
        row = await cur.fetchone()
        return dict(row) if row else {"total": 0}


async def update_signal_scores(
    conn: AsyncConnection,
    signal_id: UUID,
    *,
    risk_score: float,
    anomaly_score: float,
    source_weight: float,
    geo_criticality: float,
    time_decay_val: float,
    embedding_id: str | None = None,
) -> None:
    """Update scoring fields on a signal."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            UPDATE signals
            SET risk_score = %(risk_score)s,
                anomaly_score = %(anomaly_score)s,
                source_weight = %(source_weight)s,
                geo_criticality = %(geo_criticality)s,
                time_decay = %(time_decay_val)s,
                embedding_id = %(embedding_id)s
            WHERE id = %(signal_id)s
            """,
            {
                "signal_id": signal_id,
                "risk_score": risk_score,
                "anomaly_score": anomaly_score,
                "source_weight": source_weight,
                "geo_criticality": geo_criticality,
                "time_decay_val": time_decay_val,
                "embedding_id": embedding_id,
            },
        )
        await conn.commit()


async def check_hash_exists(conn: AsyncConnection, content_hash: str) -> bool:
    """Check if a signal with this content hash already exists."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT EXISTS(
                SELECT 1 FROM signals
                WHERE md5(lower(regexp_replace(content, '\\s+', ' ', 'g'))) = %s
            )
            """,
            (content_hash,),
        )
        row = await cur.fetchone()
        return bool(row and row[0])


async def expire_old_signals(conn: AsyncConnection) -> int:
    """Delete expired signals. Returns count of deleted rows."""
    async with conn.cursor() as cur:
        await cur.execute(
            "DELETE FROM signals WHERE expires_at IS NOT NULL AND expires_at < now()"
        )
        count = cur.rowcount
        await conn.commit()
        return count


# ── Source Weights ────────────────────────────────────────────────────────


async def get_all_source_weights(conn: AsyncConnection) -> list[SourceWeight]:
    """Fetch all source weights."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM source_weights ORDER BY current_weight DESC")
        rows = await cur.fetchall()
        return [SourceWeight(**row) for row in rows]


async def get_source_weight(conn: AsyncConnection, source: str) -> SourceWeight | None:
    """Fetch weight for a specific source."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute("SELECT * FROM source_weights WHERE source = %s", (source,))
        row = await cur.fetchone()
        return SourceWeight(**row) if row else None


async def update_source_weight(
    conn: AsyncConnection,
    source: str,
    *,
    new_weight: float,
    total_signals: int | None = None,
    total_accurate: int | None = None,
) -> None:
    """Update a source's current weight and counters."""
    sets = ["current_weight = %(new_weight)s", "last_calibrated_at = now()"]
    params: dict[str, Any] = {"source": source, "new_weight": new_weight}

    if total_signals is not None:
        sets.append("total_signals = %(total_signals)s")
        params["total_signals"] = total_signals
    if total_accurate is not None:
        sets.append("total_accurate = %(total_accurate)s")
        params["total_accurate"] = total_accurate

    set_clause = ", ".join(sets)
    async with conn.cursor() as cur:
        await cur.execute(
            f"UPDATE source_weights SET {set_clause} WHERE source = %(source)s",
            params,
        )
        await conn.commit()


# ── Alerts ────────────────────────────────────────────────────────────────


async def insert_alert(conn: AsyncConnection, alert: AlertCreate) -> UUID:
    """Insert a new alert and return its ID."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO alerts (signal_id, risk_level, risk_score, cascade_data)
            VALUES (%(signal_id)s, %(risk_level)s, %(risk_score)s, %(cascade_data)s)
            RETURNING id
            """,
            {
                **alert.model_dump(),
                "cascade_data": json.dumps(alert.cascade_data) if alert.cascade_data else None,
            },
        )
        row = await cur.fetchone()
        await conn.commit()
        return row[0]  # type: ignore[index]


async def get_active_alerts(conn: AsyncConnection, *, limit: int = 20) -> list[Alert]:
    """Fetch recent alerts not yet pushed to Supabase."""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM alerts
            WHERE pushed_to_supabase = false
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = await cur.fetchall()
        return [Alert(**row) for row in rows]


async def get_alerts(
    conn: AsyncConnection,
    *,
    active_only: bool = True,
    limit: int = 20,
) -> list[Alert]:
    """Fetch alerts with optional active-only filter."""
    where = "WHERE pushed_to_supabase = false" if active_only else ""
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            f"SELECT * FROM alerts {where} ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
        rows = await cur.fetchall()
        return [Alert(**row) for row in rows]


async def mark_alert_pushed(conn: AsyncConnection, alert_id: UUID) -> None:
    """Mark an alert as pushed to Supabase."""
    async with conn.cursor() as cur:
        await cur.execute(
            "UPDATE alerts SET pushed_to_supabase = true, pushed_at = now() WHERE id = %s",
            (alert_id,),
        )
        await conn.commit()


# ── Outcomes ──────────────────────────────────────────────────────────────


async def insert_outcome(conn: AsyncConnection, outcome: OutcomeCreate) -> UUID:
    """Record a signal outcome."""
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO outcomes (signal_id, predicted_impact, actual_outcome,
                                  accuracy_score, lead_time_hours)
            VALUES (%(signal_id)s, %(predicted_impact)s, %(actual_outcome)s,
                    %(accuracy_score)s, %(lead_time_hours)s)
            RETURNING id
            """,
            outcome.model_dump(),
        )
        row = await cur.fetchone()
        await conn.commit()
        return row[0]  # type: ignore[index]


async def get_recent_outcomes(
    conn: AsyncConnection, *, days: int = 30, limit: int = 100
) -> list[Outcome]:
    """Fetch outcomes from the last N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT * FROM outcomes
            WHERE created_at >= %s
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (cutoff, limit),
        )
        rows = await cur.fetchall()
        return [Outcome(**row) for row in rows]


async def get_accuracy_stats(
    conn: AsyncConnection, *, days: int = 30
) -> dict[str, Any]:
    """Get aggregated accuracy stats for the calibration dashboard."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT
                count(*) as total_outcomes,
                avg(accuracy_score) as avg_accuracy,
                avg(lead_time_hours) as avg_lead_time,
                count(*) FILTER (WHERE accuracy_score >= 0.5) as accurate_count,
                count(*) FILTER (WHERE accuracy_score < 0.5) as inaccurate_count
            FROM outcomes
            WHERE created_at >= %s AND accuracy_score IS NOT NULL
            """,
            (cutoff,),
        )
        row = await cur.fetchone()
        if not row or row["total_outcomes"] == 0:
            return {
                "total_outcomes": 0,
                "avg_accuracy": 0.0,
                "avg_lead_time": 0.0,
                "false_positive_rate": 0.0,
            }
        total = row["total_outcomes"]
        inaccurate = row["inaccurate_count"] or 0
        return {
            "total_outcomes": total,
            "avg_accuracy": round(float(row["avg_accuracy"] or 0), 4),
            "avg_lead_time": round(float(row["avg_lead_time"] or 0), 1),
            "false_positive_rate": round(inaccurate / total, 4) if total > 0 else 0.0,
        }


async def get_source_accuracy(
    conn: AsyncConnection, source: str, *, days: int = 30
) -> float:
    """Get accuracy for a specific source over N days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT avg(o.accuracy_score)
            FROM outcomes o
            JOIN signals s ON o.signal_id = s.id
            WHERE s.source = %s AND o.created_at >= %s AND o.accuracy_score IS NOT NULL
            """,
            (source, cutoff),
        )
        row = await cur.fetchone()
        return round(float(row[0]), 4) if row and row[0] is not None else 0.5
