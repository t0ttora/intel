"""Celery task: Cleanup expired signals (runs daily at 02:00 UTC)."""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.db.pool import get_pool
from app.db.queries import expire_old_signals

logger = logging.getLogger(__name__)

DEFAULT_RETENTION_DAYS = 30


async def _cleanup_expired() -> dict:
    """Delete signals older than retention period."""
    pool = await get_pool()

    async with pool.connection() as conn:
        deleted_count = await expire_old_signals(conn, days=DEFAULT_RETENTION_DAYS)

    logger.info(f"Cleaned up {deleted_count} expired signals (>{DEFAULT_RETENTION_DAYS} days old)")
    return {
        "deleted": deleted_count,
        "retention_days": DEFAULT_RETENTION_DAYS,
    }


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_task", bind=True, max_retries=2)
def cleanup_expired_task(self) -> dict:
    """Daily cleanup of expired signals."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_cleanup_expired())
        return result
    except Exception as exc:
        logger.error(f"Cleanup task failed: {exc}")
        self.retry(exc=exc, countdown=300)
    finally:
        loop.close()
