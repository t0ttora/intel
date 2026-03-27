"""Ingestion handlers — structured entry points for each ingestion method.

Each handler fetches signals from sources of a specific type (RSS, API,
Playwright, BS4) and pushes them through the shared pipeline.
All handlers enforce per-domain rate limiting and return pipeline stats.

Usage:
    stats = await ingest_rss(sources, tier=2)
    stats = await ingest_api(tier=1)
    stats = await ingest_html_playwright(sources)
    stats = await ingest_html_bs4(sources)
"""
from __future__ import annotations

import asyncio
import logging
from typing import Sequence

from app.ingestion.rss import RawSignal, fetch_feed
from app.ingestion.sources import Source, get_all_rss_sources
from app.ingestion.pipeline import ingest_signals
from app.ingestion.rate_limiter import get_tier_limiter, throttled

logger = logging.getLogger(__name__)


# ── RSS Handler ──────────────────────────────────────────────────────────


async def ingest_rss(
    sources: Sequence[Source] | None = None,
    *,
    tier: int | None = None,
    default_source_weight: float = 0.5,
) -> dict:
    """Fetch and ingest all RSS sources in parallel with rate limiting.

    Args:
        sources: Explicit list of RSS sources. If None, uses all RSS sources.
        tier: If provided, filter all RSS sources to this tier.
        default_source_weight: Fallback weight for the pipeline.

    Returns:
        Pipeline stats dict.
    """
    if sources is None:
        all_rss = get_all_rss_sources()
        if tier is not None:
            all_rss = [s for s in all_rss if s.tier == tier]
        sources = all_rss

    if not sources:
        return {"fetched": 0, "ingested": 0, "error": "No RSS sources"}

    limiter = get_tier_limiter(tier or 2)
    all_signals: list[RawSignal] = []

    async def _fetch_one(source: Source) -> list[RawSignal]:
        async with throttled(limiter, source.url):
            try:
                return await fetch_feed(source)
            except Exception as exc:
                logger.error(f"RSS fetch failed for {source.source_key}: {exc}")
                return []

    # Parallel fetch with rate limiting
    tasks = [_fetch_one(s) for s in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            all_signals.extend(result)
        elif isinstance(result, Exception):
            logger.error(f"RSS fetch exception: {result}")

    logger.info(f"RSS handler: {len(all_signals)} signals from {len(sources)} feeds")

    if not all_signals:
        return {"fetched": 0, "ingested": 0}

    return await ingest_signals(
        all_signals,
        default_source_weight=default_source_weight,
    )


# ── API Handler ──────────────────────────────────────────────────────────


async def ingest_api(
    *,
    tier: int | None = None,
    default_source_weight: float = 0.5,
) -> dict:
    """Run all API-based fetchers and push through the pipeline.

    Args:
        tier: If provided, only run API sources of this tier.
        default_source_weight: Fallback weight for the pipeline.

    Returns:
        Pipeline stats dict.
    """
    from app.ingestion.api_fetcher import fetch_all_api_sources

    signals = await fetch_all_api_sources()

    if not signals:
        return {"fetched": 0, "ingested": 0}

    logger.info(f"API handler: {len(signals)} signals")

    return await ingest_signals(
        signals,
        default_source_weight=default_source_weight,
        skip_keyword_filter=False,
    )


# ── Playwright Handler ──────────────────────────────────────────────────


async def ingest_html_playwright(
    sources: Sequence[Source] | None = None,
    *,
    tier: int | None = None,
    default_source_weight: float = 0.5,
) -> dict:
    """Scrape Playwright sources and push through the pipeline.

    Playwright sources are scraped sequentially (browser reuse is tricky)
    but with per-domain rate limiting.

    Args:
        sources: Explicit list of Playwright sources. If None, uses all
            Playwright sources from the specified tier (or all tiers).
        tier: Filter to a specific tier.
        default_source_weight: Fallback weight for the pipeline.

    Returns:
        Pipeline stats dict.
    """
    from app.ingestion.scraper import scrape_with_playwright
    from app.ingestion.sources import (
        get_tier1_playwright_sources,
        get_tier2_playwright_sources,
        get_tier4_scrape_sources,
    )

    if sources is None:
        all_pw: list[Source] = []
        if tier == 1 or tier is None:
            all_pw.extend(get_tier1_playwright_sources())
        if tier == 2 or tier is None:
            all_pw.extend(get_tier2_playwright_sources())
        if tier == 4 or tier is None:
            all_pw.extend(get_tier4_scrape_sources())
        sources = all_pw

    if not sources:
        return {"fetched": 0, "ingested": 0, "error": "No Playwright sources"}

    limiter = get_tier_limiter(tier or 2)
    all_signals: list[RawSignal] = []

    # Sequential with rate limiting (Playwright is resource-heavy)
    for source in sources:
        async with throttled(limiter, source.url):
            try:
                signals = await scrape_with_playwright(source)
                all_signals.extend(signals)
            except Exception as exc:
                logger.error(f"Playwright scrape failed for {source.source_key}: {exc}")

    logger.info(f"Playwright handler: {len(all_signals)} signals from {len(sources)} sources")

    if not all_signals:
        return {"fetched": 0, "ingested": 0}

    return await ingest_signals(
        all_signals,
        default_source_weight=default_source_weight,
    )


# ── BS4 (lightweight HTML) Handler ──────────────────────────────────────


async def ingest_html_bs4(
    sources: Sequence[Source] | None = None,
    *,
    default_source_weight: float = 0.5,
) -> dict:
    """Scrape lightweight HTML pages with httpx + BS4 (no Playwright).

    For sources that render server-side and don't need JavaScript execution.

    Args:
        sources: List of sources to scrape with BS4.
        default_source_weight: Fallback weight for the pipeline.

    Returns:
        Pipeline stats dict.
    """
    import httpx
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse

    from app.ingestion.sources import ALLOWED_DOMAINS

    if not sources:
        return {"fetched": 0, "ingested": 0, "error": "No BS4 sources provided"}

    limiter = get_tier_limiter(2)
    all_signals: list[RawSignal] = []

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={"User-Agent": "NobleIntel/3.0 (logistics intelligence bot)"},
    ) as client:
        for source in sources:
            parsed = urlparse(source.url)
            if parsed.hostname not in ALLOWED_DOMAINS:
                logger.warning(f"BS4: blocked non-allowlisted domain: {parsed.hostname}")
                continue

            async with throttled(limiter, source.url):
                try:
                    resp = await client.get(source.url)
                    resp.raise_for_status()
                    soup = BeautifulSoup(resp.text, "lxml")

                    # Generic article extraction
                    items: list[dict] = []
                    for el in soup.select("article, .news-item, .card, .list-item"):
                        title_el = el.select_one("h2, h3, h4, .title, a")
                        title = title_el.get_text(strip=True) if title_el else ""
                        content = el.get_text(separator=" ", strip=True)
                        if content and len(content) >= 20:
                            link_el = el.select_one("a[href]")
                            href = link_el.get("href", "") if link_el else ""
                            items.append({
                                "title": title or content[:60],
                                "content": content[:2000],
                                "url": href if href.startswith("http") else source.url,
                            })
                    # Fallback
                    if not items:
                        main = soup.select_one("main, .content, #content, article, body")
                        if main:
                            text = main.get_text(separator="\n", strip=True)
                            if text and len(text) > 50:
                                items = [{"title": source.name, "content": text[:5000], "url": source.url}]

                    from datetime import datetime, timezone
                    for item in items[:20]:
                        all_signals.append(
                            RawSignal(
                                title=item.get("title", source.name),
                                content=item["content"],
                                url=item.get("url", source.url),
                                source_key=source.source_key,
                                feed_name=source.name,
                                published_at=datetime.now(timezone.utc),
                                source_type=source.source_type,
                                modes=source.modes,
                                reliability=source.reliability,
                            )
                        )

                except Exception as exc:
                    logger.error(f"BS4 scrape failed for {source.source_key}: {exc}")

    logger.info(f"BS4 handler: {len(all_signals)} signals from {len(sources)} sources")

    if not all_signals:
        return {"fetched": 0, "ingested": 0}

    return await ingest_signals(
        all_signals,
        default_source_weight=default_source_weight,
    )
