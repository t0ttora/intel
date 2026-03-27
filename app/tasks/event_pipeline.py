"""Celery task: Event pipeline (runs every 15 minutes)."""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.db.pool import get_pool
from app.vectordb.client import get_qdrant

logger = logging.getLogger(__name__)


async def _run_pipeline() -> dict:
    """Async event pipeline execution."""
    from app.engine.event_orchestrator import run_event_pipeline

    settings = get_settings()
    pool = await get_pool()
    qdrant = await get_qdrant()

    async with pool.connection() as conn:
        stats = await run_event_pipeline(conn, qdrant, settings)

    return stats


@celery_app.task(
    name="app.tasks.event_pipeline.run_event_pipeline_task",
    bind=True,
    max_retries=2,
    soft_time_limit=240,
    time_limit=300,
)
def run_event_pipeline_task(self) -> dict:
    """Celery task wrapper for the event pipeline."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run_pipeline())
        logger.info(f"Event pipeline task completed: {result}")
        return result
    except Exception as exc:
        logger.error(f"Event pipeline task failed: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        loop.close()
