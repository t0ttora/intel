"""Celery task: Tier 2 ingestion — RSS feeds + NOAA JSON + Playwright scrapers.

Fetches all Tier 2 news, chokepoint, and pricing sources via the
central source registry, then processes through the shared pipeline.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.ingestion.rss import fetch_all_feeds
from app.ingestion.scraper import scrape_tier2_non_rss
from app.ingestion.pipeline import ingest_signals

logger = logging.getLogger(__name__)


async def _ingest_tier2() -> dict:
    """Async Tier 2 ingestion — RSS + NOAA JSON + Playwright sources."""
    all_signals = []

    # Phase 1: RSS feeds (news, pricing, some chokepoints)
    try:
        rss_signals = await fetch_all_feeds()
        all_signals.extend(rss_signals)
        logger.info(f"Tier 2 RSS: {len(rss_signals)} raw signals")
    except Exception as exc:
        logger.error(f"RSS fetch failed: {exc}")

    # Phase 2: Non-RSS sources (NOAA JSON API, UKMTO Playwright)
    try:
        non_rss_signals = await scrape_tier2_non_rss()
        all_signals.extend(non_rss_signals)
        logger.info(f"Tier 2 non-RSS: {len(non_rss_signals)} raw signals")
    except Exception as exc:
        logger.error(f"Non-RSS scrape failed: {exc}")

    if not all_signals:
        return {"error": "No signals from any Tier 2 source", "fetched": 0, "ingested": 0}

    stats = await ingest_signals(all_signals, default_source_weight=0.5)
    logger.info(f"Tier 2 ingestion complete: {stats}")
    return stats


@celery_app.task(name="app.tasks.ingest_rss.ingest_rss_task", bind=True, max_retries=3)
def ingest_rss_task(self) -> dict:
    """Celery task wrapper for Tier 2 ingestion."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_tier2())
        return result
    except Exception as exc:
        logger.error(f"Tier 2 ingest task failed: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        loop.close()
