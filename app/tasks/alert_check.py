"""Celery task: Alert checking (runs every minute)."""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.db.pool import get_pool
from app.alerts.pusher import check_and_push_alerts

logger = logging.getLogger(__name__)


async def _check_alerts() -> dict:
    """Async alert check and push."""
    pool = await get_pool()

    async with pool.connection() as conn:
        alerts = await check_and_push_alerts(conn)

    return {
        "alerts_pushed": len(alerts),
        "alert_ids": [a.id for a in alerts],
    }


@celery_app.task(name="app.tasks.alert_check.check_alerts_task", bind=True, max_retries=2)
def check_alerts_task(self) -> dict:
    """Celery task wrapper for alert checking."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_check_alerts())
        return result
    except Exception as exc:
        logger.error(f"Alert check task failed: {exc}")
        self.retry(exc=exc, countdown=30)
    finally:
        loop.close()
