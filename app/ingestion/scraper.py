"""Playwright scraper — Reddit, Drewry WCI, SCFI (Phase 2)."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

from app.ingestion.rss import RawSignal

logger = logging.getLogger(__name__)

# Allowlisted scrape targets — security: never scrape arbitrary URLs
SCRAPE_TARGETS: list[dict[str, str]] = [
    {
        "name": "Reddit r/logistics",
        "url": "https://www.reddit.com/r/logistics/hot.json",
        "source_key": "reddit",
    },
    {
        "name": "Reddit r/shipping",
        "url": "https://www.reddit.com/r/shipping/hot.json",
        "source_key": "reddit",
    },
    {
        "name": "Reddit r/supplychain",
        "url": "https://www.reddit.com/r/supplychain/hot.json",
        "source_key": "reddit",
    },
]

ALLOWED_SCRAPE_DOMAINS: set[str] = {
    "www.reddit.com",
    "old.reddit.com",
}


async def scrape_reddit_json(target: dict[str, str]) -> list[RawSignal]:
    """Scrape Reddit via JSON API (no browser needed for Phase 1)."""
    import httpx

    url = target["url"]
    name = target["name"]
    source_key = target["source_key"]
    signals: list[RawSignal] = []

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "NobleIntel/3.0 (logistics intelligence bot)",
            },
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        children = data.get("data", {}).get("children", [])
        for child in children:
            post = child.get("data", {})
            title = post.get("title", "").strip()
            selftext = post.get("selftext", "").strip()
            permalink = post.get("permalink", "")

            content = f"{title}\n\n{selftext}" if selftext else title
            if not content:
                continue

            created_utc = post.get("created_utc")
            published_at = (
                datetime.fromtimestamp(created_utc, tz=timezone.utc)
                if created_utc
                else None
            )

            signals.append(
                RawSignal(
                    title=title,
                    content=content,
                    url=f"https://www.reddit.com{permalink}" if permalink else "",
                    source_key=source_key,
                    feed_name=name,
                    published_at=published_at,
                )
            )

        logger.info(f"Scraped {len(signals)} posts from {name}")

    except Exception as exc:
        logger.error(f"Error scraping {name}: {exc}")

    return signals


async def scrape_with_playwright(url: str, selector: str = "body") -> str:
    """Scrape a page using Playwright (for JS-rendered content)."""
    from playwright.async_api import async_playwright

    # Validate URL against allowlist
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_SCRAPE_DOMAINS:
        logger.warning(f"Blocked scrape attempt to non-allowlisted domain: {parsed.hostname}")
        return ""

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(url, timeout=30000)
            content = await page.inner_text(selector)
            await browser.close()
            return content.strip()
    except Exception as exc:
        logger.error(f"Playwright scrape error for {url}: {exc}")
        return ""


async def scrape_all_sources() -> list[RawSignal]:
    """Scrape all configured sources and return raw signals."""
    all_signals: list[RawSignal] = []

    for target in SCRAPE_TARGETS:
        signals = await scrape_reddit_json(target)
        all_signals.extend(signals)

    logger.info(f"Total scraped signals: {len(all_signals)}")
    return all_signals
