"""Celery task: Regulatory ingestion — Tier 4 (daily at 06:00 UTC).

Fetches official regulatory sources (customs, embargoes, directives)
from both RSS feeds and Playwright-scraped pages. Low frequency,
high reliability — these are "the rules" signals.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.ingestion.rss import fetch_regulatory_feeds
from app.ingestion.scraper import scrape_all_regulatory
from app.ingestion.pipeline import ingest_signals

logger = logging.getLogger(__name__)


async def _ingest_regulatory() -> dict:
    """Async regulatory ingestion (Tier 4)."""
    all_signals = []

    # Phase 1: RSS-based regulatory feeds
    try:
        rss_signals = await fetch_regulatory_feeds()
        all_signals.extend(rss_signals)
    except Exception as exc:
        logger.error(f"Regulatory RSS fetch failed: {exc}")

    # Phase 2: Playwright-scraped regulatory pages
    try:
        scrape_signals = await scrape_all_regulatory()
        all_signals.extend(scrape_signals)
    except Exception as exc:
        logger.error(f"Regulatory scrape failed: {exc}")

    if not all_signals:
        return {"fetched": 0, "ingested": 0, "note": "no regulatory signals found"}

    stats = await ingest_signals(
        all_signals,
        default_source_weight=0.7,  # High weight for official sources
    )
    logger.info(f"Tier 4 regulatory ingestion complete: {stats}")
    return stats


@celery_app.task(
    name="app.tasks.ingest_regulatory.ingest_regulatory_task",
    bind=True,
    max_retries=2,
)
def ingest_regulatory_task(self) -> dict:
    """Celery task wrapper for Tier 4 regulatory ingestion."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_regulatory())
        return result
    except Exception as exc:
        logger.error(f"Regulatory ingest task failed: {exc}")
        self.retry(exc=exc, countdown=300)
    finally:
        loop.close()
