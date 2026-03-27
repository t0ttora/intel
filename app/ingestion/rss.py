"""RSS/Atom feed listener — fetches, parses, yields raw signals.

Uses the central source registry for feed configuration.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlparse

import feedparser
import httpx

from app.ingestion.sources import ALLOWED_DOMAINS, Source, get_all_rss_sources, get_tier4_rss_sources

logger = logging.getLogger(__name__)


class _HTMLStripper(HTMLParser):
    """Minimal HTML tag stripper using stdlib only."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def get_text(self) -> str:
        return " ".join(self._parts)


def strip_html(text: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    stripper = _HTMLStripper()
    stripper.feed(text)
    cleaned = stripper.get_text()
    return re.sub(r"\s+", " ", cleaned).strip()


@dataclass
class RawSignal:
    """A raw signal from an RSS feed before filtering/scoring."""

    title: str
    content: str
    url: str
    source_key: str
    feed_name: str
    published_at: datetime | None
    # New metadata from source registry
    source_type: str = "news"
    modes: list[str] | None = None
    reliability: float = 0.5


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


async def fetch_feed(source: Source, timeout: float = 30.0) -> list[RawSignal]:
    """Fetch and parse a single RSS/Atom feed using source registry metadata."""
    url = source.url
    name = source.name
    source_key = source.source_key
    signals: list[RawSignal] = []

    # Enforce domain allowlist
    hostname = urlparse(url).hostname
    if hostname and hostname not in ALLOWED_DOMAINS:
        logger.warning(f"Blocked fetch to non-allowlisted domain: {hostname}")
        return []

    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url, headers={"User-Agent": "NobleIntel/3.0"})
            response.raise_for_status()

        parsed = feedparser.parse(response.text)

        for entry in parsed.entries:
            title = strip_html(entry.get("title", ""))
            # Prefer summary over full content for initial signal
            raw_content = entry.get("summary", "") or entry.get("description", "") or ""
            content = strip_html(raw_content)
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
                    source_type=source.source_type,
                    modes=source.modes,
                    reliability=source.reliability,
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
    """Fetch all Tier 2 RSS feeds concurrently and return raw signals."""
    import asyncio

    sources = get_all_rss_sources()
    tasks = [fetch_feed(source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_signals: list[RawSignal] = []
    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.error(f"Feed {source.name} failed: {result}")
            continue
        all_signals.extend(result)

    logger.info(f"Total raw signals from {len(sources)} feeds: {len(all_signals)}")
    return all_signals


async def fetch_regulatory_feeds() -> list[RawSignal]:
    """Fetch Tier 4 regulatory RSS feeds (daily cadence)."""
    import asyncio

    sources = get_tier4_rss_sources()
    tasks = [fetch_feed(source) for source in sources]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_signals: list[RawSignal] = []
    for source, result in zip(sources, results):
        if isinstance(result, Exception):
            logger.error(f"Regulatory feed {source.name} failed: {result}")
            continue
        all_signals.extend(result)

    logger.info(f"Total regulatory signals from {len(sources)} feeds: {len(all_signals)}")
    return all_signals
