"""Celery task: Social intelligence ingestion — Tier 3 (every 5 min).

Scrapes Reddit and other social sources with strict impact keyword
filtering. High frequency but only disruption signals pass through.
This is the "future signal" — human observations predict events
before official channels report them.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.ingestion.scraper import scrape_all_social
from app.ingestion.pipeline import ingest_signals

logger = logging.getLogger(__name__)


async def _ingest_social() -> dict:
    """Async social intelligence ingestion (Tier 3)."""
    try:
        raw_signals = await scrape_all_social()
    except Exception as exc:
        logger.error(f"Social scrape failed: {exc}")
        return {"error": str(exc), "fetched": 0, "ingested": 0}

    if not raw_signals:
        return {"fetched": 0, "ingested": 0, "note": "no impact signals found"}

    # Social sources already passed impact keyword filter in scraper.
    # Skip general keyword filter — these are pre-filtered for disruption terms.
    stats = await ingest_signals(
        raw_signals,
        default_source_weight=0.35,
        skip_keyword_filter=True,
    )
    logger.info(f"Tier 3 social ingestion complete: {stats}")
    return stats


@celery_app.task(
    name="app.tasks.ingest_social.ingest_social_task",
    bind=True,
    max_retries=3,
)
def ingest_social_task(self) -> dict:
    """Celery task wrapper for Tier 3 social intelligence ingestion."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_social())
        return result
    except Exception as exc:
        logger.error(f"Social ingest task failed: {exc}")
        self.retry(exc=exc, countdown=30)
    finally:
        loop.close()
