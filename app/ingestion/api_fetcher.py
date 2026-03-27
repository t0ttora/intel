"""API-based signal fetchers — JSON/REST endpoints for structured data.

Handles sources that expose JSON APIs rather than RSS or HTML:
- NASA FIRMS (active fire detection)
- OpenSky Network (ADS-B flight tracking)
- Hacker News Algolia (tech/logistics discussions)
- NOAA (weather alerts — already exists, re-exported here)
- UN Comtrade (trade statistics)
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

import httpx

from app.ingestion.rss import RawSignal
from app.ingestion.sources import (
    Source,
    get_api_sources,
)
from app.ingestion.rate_limiter import get_tier_limiter, throttled

logger = logging.getLogger(__name__)

# Re-export NOAA fetcher from scraper (it predates this module)
from app.ingestion.scraper import fetch_noaa_alerts  # noqa: F401

_DEFAULT_TIMEOUT = 30.0
_USER_AGENT = "NobleIntel/3.0 (contact@nobleverse.io)"


def _get_source_by_key(key: str) -> Source | None:
    """Find a source by source_key from the API sources list."""
    for s in get_api_sources():
        if s.source_key == key:
            return s
    return None


# ── NASA FIRMS — Active Fire Data ────────────────────────────────────────


async def fetch_nasa_firms() -> list[RawSignal]:
    """Fetch active fire hotspots near major ports/corridors from NASA FIRMS.

    Uses MODIS/VIIRS data. Filters to transport-relevant areas.
    """
    source = _get_source_by_key("nasa_firms")
    if not source:
        logger.warning("NASA FIRMS source not found in registry")
        return []

    api_key = os.environ.get(source.api_key_env or "NASA_FIRMS_API_KEY", "")
    if not api_key:
        logger.warning("NASA_FIRMS_API_KEY not set, skipping FIRMS fetch")
        return []

    # Bounding boxes for major transport corridors
    # Format: west,south,east,north
    CORRIDOR_BOXES = {
        "suez": "32.0,29.5,33.5,31.5",
        "panama": "-80.0,8.5,-79.0,9.5",
        "malacca": "99.0,0.5,105.0,4.5",
        "uswc_ports": "-122.0,32.0,-117.0,38.0",
        "usec_ports": "-82.0,25.0,-70.0,42.0",
    }

    signals: list[RawSignal] = []
    limiter = get_tier_limiter(1)

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        for corridor_name, bbox in CORRIDOR_BOXES.items():
            url = (
                f"https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
                f"{api_key}/VIIRS_SNPP_NRT/{bbox}/1"
            )
            try:
                async with throttled(limiter, url):
                    resp = await client.get(
                        url,
                        headers={"User-Agent": _USER_AGENT},
                    )
                    resp.raise_for_status()

                lines = resp.text.strip().split("\n")
                if len(lines) <= 1:
                    continue

                # Parse CSV: latitude,longitude,brightness,...
                header = lines[0].split(",")
                for line in lines[1:51]:  # Cap at 50 hotspots per corridor
                    fields = line.split(",")
                    if len(fields) < 6:
                        continue
                    lat, lon = fields[0], fields[1]
                    brightness = fields[2] if len(fields) > 2 else "N/A"
                    confidence = fields[8] if len(fields) > 8 else "N/A"

                    title = f"Fire hotspot near {corridor_name}: {lat},{lon} (brightness={brightness})"
                    content = (
                        f"Active fire detection via VIIRS satellite near {corridor_name} corridor. "
                        f"Location: {lat}°N, {lon}°E. Brightness: {brightness}. "
                        f"Confidence: {confidence}. This may affect nearby transport "
                        f"infrastructure, port operations, or air corridors."
                    )
                    signals.append(
                        RawSignal(
                            title=title,
                            content=content,
                            url=f"https://firms.modaps.eosdis.nasa.gov/map/#{lat},{lon}",
                            source_key=source.source_key,
                            feed_name=source.name,
                            published_at=datetime.now(timezone.utc),
                            source_type=source.source_type,
                            modes=source.modes,
                            reliability=source.reliability,
                        )
                    )

            except httpx.HTTPStatusError as exc:
                logger.error(f"NASA FIRMS {corridor_name}: HTTP {exc.response.status_code}")
            except Exception as exc:
                logger.error(f"NASA FIRMS {corridor_name}: {exc}")

    logger.info(f"NASA FIRMS: {len(signals)} fire hotspots near transport corridors")
    return signals


# ── OpenSky Network — ADS-B Flight Tracking ──────────────────────────────


async def fetch_opensky_disruptions() -> list[RawSignal]:
    """Fetch anomalous flight patterns from OpenSky Network.

    Looks for unusual concentrations of aircraft (holding patterns)
    or airspace closures inferred from ADS-B absence.
    """
    source = _get_source_by_key("opensky")
    if not source:
        logger.warning("OpenSky source not found in registry")
        return []

    signals: list[RawSignal] = []
    limiter = get_tier_limiter(1)

    # Major cargo airport bounding boxes: lat_min, lat_max, lon_min, lon_max
    CARGO_AIRPORTS = {
        "MEM": (34.8, 35.2, -90.2, -89.8),  # Memphis (FedEx)
        "SDF": (38.0, 38.3, -86.0, -85.5),  # Louisville (UPS)
        "HKG": (22.2, 22.4, 113.8, 114.0),  # Hong Kong
        "PVG": (30.9, 31.3, 121.6, 121.9),  # Shanghai Pudong
        "ANC": (61.1, 61.3, -150.1, -149.8),  # Anchorage (cargo hub)
        "LEJ": (51.3, 51.5, 12.2, 12.5),  # Leipzig (DHL)
        "DXB": (25.2, 25.3, 55.3, 55.4),  # Dubai
    }

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        for apt_code, (lat_min, lat_max, lon_min, lon_max) in CARGO_AIRPORTS.items():
            url = (
                f"https://opensky-network.org/api/states/all"
                f"?lamin={lat_min}&lamax={lat_max}&lomin={lon_min}&lomax={lon_max}"
            )
            try:
                async with throttled(limiter, url):
                    resp = await client.get(
                        url,
                        headers={"User-Agent": _USER_AGENT},
                    )
                    resp.raise_for_status()

                data = resp.json()
                states = data.get("states", [])
                aircraft_count = len(states)

                # Only signal if unusual concentration (>50 aircraft in small box)
                if aircraft_count > 50:
                    title = f"Unusual air traffic near {apt_code}: {aircraft_count} aircraft"
                    content = (
                        f"OpenSky ADS-B data shows {aircraft_count} aircraft in the "
                        f"vicinity of {apt_code}. This concentration may indicate "
                        f"holding patterns, congestion, or diversions affecting "
                        f"cargo operations at this hub."
                    )
                    signals.append(
                        RawSignal(
                            title=title,
                            content=content,
                            url=f"https://opensky-network.org/network/explorer?lat={lat_min}&lon={lon_min}",
                            source_key=source.source_key,
                            feed_name=source.name,
                            published_at=datetime.now(timezone.utc),
                            source_type=source.source_type,
                            modes=source.modes,
                            reliability=source.reliability,
                        )
                    )

            except httpx.HTTPStatusError as exc:
                logger.error(f"OpenSky {apt_code}: HTTP {exc.response.status_code}")
            except Exception as exc:
                logger.error(f"OpenSky {apt_code}: {exc}")

    logger.info(f"OpenSky: {len(signals)} anomalous air traffic signals")
    return signals


# ── Hacker News Algolia — Tech/Logistics Intelligence ────────────────────


async def fetch_hackernews() -> list[RawSignal]:
    """Search Hacker News for logistics/supply-chain discussions.

    Uses the Algolia search API to find recent stories matching
    supply chain keywords.
    """
    source = _get_source_by_key("hackernews")
    if not source:
        logger.warning("Hacker News source not found in registry")
        return []

    # Search terms — logistics/supply chain relevant
    SEARCH_QUERIES = [
        "supply chain disruption",
        "shipping container",
        "port congestion",
        "freight rates",
        "logistics cyberattack",
        "trade war tariff",
        "rail derailment",
        "trucking shortage",
    ]

    signals: list[RawSignal] = []
    seen_ids: set[str] = set()
    limiter = get_tier_limiter(3)

    async with httpx.AsyncClient(timeout=_DEFAULT_TIMEOUT) as client:
        for query in SEARCH_QUERIES:
            url = "https://hn.algolia.com/api/v1/search_by_date"
            params = {
                "query": query,
                "tags": "story",
                "numericFilters": "points>5",
                "hitsPerPage": 10,
            }
            try:
                async with throttled(limiter, url):
                    resp = await client.get(
                        url,
                        params=params,
                        headers={"User-Agent": _USER_AGENT},
                    )
                    resp.raise_for_status()

                data = resp.json()
                for hit in data.get("hits", []):
                    object_id = hit.get("objectID", "")
                    if object_id in seen_ids:
                        continue
                    seen_ids.add(object_id)

                    title = hit.get("title", "")
                    story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}"
                    points = hit.get("points", 0)
                    num_comments = hit.get("num_comments", 0)
                    created_at_str = hit.get("created_at", "")

                    content = (
                        f"{title}. "
                        f"HN discussion: {points} points, {num_comments} comments. "
                        f"Source: {story_url}"
                    )

                    pub_at = datetime.now(timezone.utc)
                    if created_at_str:
                        try:
                            pub_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        except (ValueError, TypeError):
                            pass

                    signals.append(
                        RawSignal(
                            title=title,
                            content=content,
                            url=story_url,
                            source_key=source.source_key,
                            feed_name=source.name,
                            published_at=pub_at,
                            source_type=source.source_type,
                            modes=source.modes,
                            reliability=source.reliability,
                        )
                    )

            except httpx.HTTPStatusError as exc:
                logger.error(f"HN Algolia '{query}': HTTP {exc.response.status_code}")
            except Exception as exc:
                logger.error(f"HN Algolia '{query}': {exc}")

    logger.info(f"Hacker News: {len(signals)} logistics-relevant stories")
    return signals


# ── Aggregate API Fetcher ────────────────────────────────────────────────


async def fetch_all_api_sources() -> list[RawSignal]:
    """Run all API-based fetchers and return combined signals.

    Dispatches by source_key to the appropriate fetcher function.
    Sources without a dedicated fetcher are skipped (logged as warning).
    """
    all_signals: list[RawSignal] = []

    # Dispatch table for dedicated API fetchers
    fetchers = {
        "nasa_firms": fetch_nasa_firms,
        "opensky": fetch_opensky_disruptions,
        "hackernews": fetch_hackernews,
        "noaa_alerts": fetch_noaa_alerts,
    }

    for key, fetcher in fetchers.items():
        try:
            signals = await fetcher()
            all_signals.extend(signals)
            logger.info(f"API fetch {key}: {len(signals)} signals")
        except Exception as exc:
            logger.error(f"API fetch {key} failed: {exc}")

    logger.info(f"Total API signals: {len(all_signals)}")
    return all_signals
