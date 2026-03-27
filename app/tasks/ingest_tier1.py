"""Celery task: Tier 1 live ingestion — every 15 minutes.

Fetches real-time data from three ingestion methods in parallel:
  1. RSS feeds (port authorities, pricing)
  2. API endpoints (NASA FIRMS, OpenSky, etc.)
  3. Playwright scrapers (dynamic JS-rendered dashboards)

Tier 1 sources are the highest-priority physical-world and pricing
signals — they fire every 15 min with aggressive rate limiting.
"""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.ingestion.handlers import (
    ingest_api,
    ingest_html_playwright,
    ingest_rss,
)
from app.ingestion.sources import (
    get_tier1_api_sources,
    get_tier1_playwright_sources,
    get_tier1_rss_sources,
)

logger = logging.getLogger(__name__)


async def _ingest_tier1() -> dict:
    """Async Tier 1 ingestion — RSS + API + Playwright in parallel."""
    rss_sources = get_tier1_rss_sources()
    pw_sources = get_tier1_playwright_sources()

    # Run all three ingestion methods concurrently
    rss_task = ingest_rss(rss_sources, tier=1, default_source_weight=0.8)
    api_task = ingest_api(tier=1, default_source_weight=0.8)
    pw_task = ingest_html_playwright(pw_sources, tier=1, default_source_weight=0.8)

    results = await asyncio.gather(rss_task, api_task, pw_task, return_exceptions=True)

    combined = {"rss": {}, "api": {}, "playwright": {}, "total_ingested": 0, "total_fetched": 0}
    labels = ["rss", "api", "playwright"]

    for label, result in zip(labels, results):
        if isinstance(result, Exception):
            logger.error(f"Tier 1 {label} failed: {result}")
            combined[label] = {"error": str(result)}
        elif isinstance(result, dict):
            combined[label] = result
            combined["total_ingested"] += result.get("ingested", 0)
            combined["total_fetched"] += result.get("fetched", 0)
        else:
            combined[label] = {"error": "unexpected result type"}

    logger.info(
        f"Tier 1 ingestion complete: "
        f"{combined['total_fetched']} fetched, "
        f"{combined['total_ingested']} ingested"
    )
    return combined


@celery_app.task(
    name="app.tasks.ingest_tier1.ingest_tier1_task",
    bind=True,
    max_retries=3,
)
def ingest_tier1_task(self) -> dict:
    """Celery task wrapper for Tier 1 live ingestion (every 15 min)."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_tier1())
        return result
    except Exception as exc:
        logger.error(f"Tier 1 ingest task failed: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        loop.close()
