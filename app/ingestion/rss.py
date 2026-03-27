"""RSS/Atom feed listener — fetches, parses, yields raw signals."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncGenerator

import feedparser
import httpx

logger = logging.getLogger(__name__)

RSS_FEEDS: list[dict[str, str]] = [
    {"name": "Lloyd's List", "url": "https://lloydslist.maritimeintelligence.informa.com/rss", "source_key": "tier1_news"},
    {"name": "TradeWinds", "url": "https://www.tradewindsnews.com/rss", "source_key": "tier1_news"},
    {"name": "Freightos Blog", "url": "https://www.freightos.com/blog/feed/", "source_key": "freight_index"},
    {"name": "IMO News", "url": "https://www.imo.org/en/MediaCentre/Pages/WhatsNew.aspx", "source_key": "imo"},
    {"name": "UKMTO", "url": "https://www.ukmto.org/indian-ocean/rss", "source_key": "ukmto"},
    {"name": "gCaptain", "url": "https://gcaptain.com/feed/", "source_key": "tier1_news"},
    {"name": "Splash247", "url": "https://splash247.com/feed/", "source_key": "general_news"},
    {"name": "Maritime Executive", "url": "https://maritime-executive.com/rss", "source_key": "general_news"},
    {"name": "Hellenic Shipping News", "url": "https://www.hellenicshippingnews.com/feed/", "source_key": "general_news"},
    {"name": "Seatrade Maritime", "url": "https://www.seatrade-maritime.com/rss.xml", "source_key": "general_news"},
]

# Allowlisted domains for URL fetching — security: never follow arbitrary URLs
ALLOWED_DOMAINS: set[str] = {
    "lloydslist.maritimeintelligence.informa.com",
    "www.tradewindsnews.com",
    "www.freightos.com",
    "www.imo.org",
    "www.ukmto.org",
    "gcaptain.com",
    "splash247.com",
    "maritime-executive.com",
    "www.hellenicshippingnews.com",
    "www.seatrade-maritime.com",
}


@dataclass
class RawSignal:
    """A raw signal from an RSS feed before filtering/scoring."""

    title: str
    content: str
    url: str
    source_key: str
    feed_name: str
    published_at: datetime | None


def _parse_published(entry: dict) -> datetime | None:
    """Parse published date from a feedparser entry."""
    published_parsed = entry.get("published_parsed")
    if published_parsed:
        try:
            from time import mktime
            return datetime.fromtimestamp(mktime(published_parsed), tz=timezone.utc)
        except (ValueError, OverflowError):
            pass
    return None


async def fetch_feed(feed: dict[str, str], timeout: float = 30.0) -> list[RawSignal]:
    """Fetch and parse a single RSS/Atom feed."""
    url = feed["url"]
    name = feed["name"]
    source_key = feed["source_key"]
    signals: list[RawSignal] = []

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "NobleIntel/3.0"})
            response.raise_for_status()

        parsed = feedparser.parse(response.text)

        for entry in parsed.entries:
            title = entry.get("title", "").strip()
            # Prefer summary over full content for initial signal
            content = entry.get("summary", "") or entry.get("description", "") or ""
            content = content.strip()
            entry_url = entry.get("link", "")

            if not content:
                continue

            signals.append(
                RawSignal(
                    title=title,
                    content=content,
                    url=entry_url,
                    source_key=source_key,
                    feed_name=name,
                    published_at=_parse_published(entry),
                )
            )

        logger.info(f"Fetched {len(signals)} entries from {name}")

    except httpx.HTTPStatusError as exc:
        logger.warning(f"HTTP error fetching {name}: {exc.response.status_code}")
    except httpx.RequestError as exc:
        logger.warning(f"Request error fetching {name}: {exc}")
    except Exception as exc:
        logger.error(f"Unexpected error fetching {name}: {exc}")

    return signals


async def fetch_all_feeds() -> list[RawSignal]:
    """Fetch all configured RSS feeds and return raw signals."""
    all_signals: list[RawSignal] = []

    for feed in RSS_FEEDS:
        signals = await fetch_feed(feed)
        all_signals.extend(signals)

    logger.info(f"Total raw signals from all feeds: {len(all_signals)}")
    return all_signals
