"""Celery task: Web scraper ingestion — backward compat (runs every 30 minutes).

This task is kept for backward compatibility. New tiered tasks
(ingest_social, ingest_regulatory) are preferred. This task now
delegates to the shared pipeline.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.ingestion.scraper import scrape_all_sources
from app.ingestion.pipeline import ingest_signals

logger = logging.getLogger(__name__)


async def _ingest_scraper() -> dict:
    """Async scraper ingestion pipeline."""
    try:
        raw_signals = await scrape_all_sources()
    except Exception as exc:
        logger.error(f"Scraper fetch failed: {exc}")
        return {"error": str(exc), "fetched": 0, "ingested": 0}

    # Social sources already passed impact filter, skip general keyword filter
    stats = await ingest_signals(
        raw_signals,
        default_source_weight=0.35,
        skip_keyword_filter=True,
    )
    logger.info(f"Scraper ingestion complete: {stats}")
    return stats


@celery_app.task(name="app.tasks.ingest_scraper.ingest_scraper_task", bind=True, max_retries=3)
def ingest_scraper_task(self) -> dict:
    """Celery task wrapper for scraper ingestion."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_scraper())
        return result
    except Exception as exc:
        logger.error(f"Scraper ingest task failed: {exc}")
        self.retry(exc=exc, countdown=120)
    finally:
        loop.close()
