"""Push CRITICAL alerts (risk >= 0.80) to Supabase logistics_alerts table."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from psycopg import AsyncConnection

from app.config import get_settings
from app.db.models import Alert, Signal
from app.db.queries import get_signals, insert_alert, mark_alert_pushed

logger = logging.getLogger(__name__)

CRITICAL_THRESHOLD = 0.80


async def _signal_already_alerted(conn: AsyncConnection, signal_id) -> bool:
    """Check if an alert already exists for this signal (dedup)."""
    async with conn.cursor() as cur:
        await cur.execute(
            "SELECT EXISTS(SELECT 1 FROM alerts WHERE signal_id = %s)",
            (signal_id,),
        )
        row = await cur.fetchone()
        return row[0] if row else False


async def check_and_push_alerts(conn: AsyncConnection) -> list[Alert]:
    """Check for new critical signals and push them as alerts.

    1. Query signals with risk_score >= 0.80 from last 2 hours
    2. For each, create a local alert record
    3. Push to Supabase logistics_alerts table
    4. Mark as pushed
    """
    settings = get_settings()
    new_alerts: list[Alert] = []

    # Get critical signals from last 2 hours
    critical_signals = await get_signals(
        conn,
        min_risk_score=CRITICAL_THRESHOLD,
        last_hours=2,
        limit=50,
    )

    if not critical_signals:
        logger.debug("No critical signals found for alerting")
        return []

    for signal in critical_signals:
        try:
            # Dedup: skip if we already alerted on this signal
            if await _signal_already_alerted(conn, signal.id):
                logger.debug(f"Skipping already-alerted signal {signal.id}")
                continue

            # Create local alert record
            alert = await insert_alert(
                conn,
                signal_id=signal.id,
                alert_type="CRITICAL",
                risk_score=signal.risk_score or CRITICAL_THRESHOLD,
                title=_build_alert_title(signal),
                summary=_build_alert_summary(signal),
                geo_zone=signal.geo_zone,
            )

            if alert is None:
                continue

            # Push to Supabase
            pushed = await _push_to_supabase(settings, signal, alert)

            if pushed:
                await mark_alert_pushed(conn, alert.id)
                new_alerts.append(alert)
                logger.info(f"Pushed alert for signal {signal.id}: {alert.title}")

        except Exception as exc:
            logger.error(f"Error processing alert for signal {signal.id}: {exc}")
            continue

    logger.info(f"Pushed {len(new_alerts)} new alerts")
    return new_alerts


async def _push_to_supabase(settings: Any, signal: Signal, alert: Alert) -> bool:
    """Push an alert to the Supabase logistics_alerts table."""
    url = f"{settings.supabase_url}/rest/v1/logistics_alerts"
    headers = {
        "apikey": settings.supabase_service_key,
        "Authorization": f"Bearer {settings.supabase_service_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    payload = {
        "type": "CRITICAL",
        "title": alert.title,
        "summary": alert.summary,
        "risk_score": signal.risk_score,
        "geo_zone": signal.geo_zone,
        "source": signal.source,
        "signal_url": signal.url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "is_read": False,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return True
    except httpx.HTTPStatusError as exc:
        logger.warning(f"Supabase push failed ({exc.response.status_code}): {exc.response.text}")
        return False
    except httpx.RequestError as exc:
        logger.warning(f"Supabase push error: {exc}")
        return False


def _build_alert_title(signal: Signal) -> str:
    """Build a concise alert title from a signal."""
    zone = (signal.geo_zone or "global").replace("_", " ").title()
    tier = signal.tier or "CRITICAL"
    return f"[{tier}] {zone}: {signal.title or signal.content[:60]}"


def _build_alert_summary(signal: Signal) -> str:
    """Build an alert summary from a signal."""
    parts: list[str] = []

    if signal.risk_score:
        parts.append(f"Risk Score: {signal.risk_score:.2f}")
    if signal.geo_zone:
        parts.append(f"Zone: {signal.geo_zone.replace('_', ' ').title()}")
    if signal.source:
        parts.append(f"Source: {signal.source}")

    summary = " | ".join(parts)
    content_preview = signal.content[:200] if signal.content else ""

    return f"{summary}\n{content_preview}"
