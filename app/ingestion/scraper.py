"""Multi-source scraper — Reddit JSON, NOAA JSON API, Playwright + BeautifulSoup.

Uses central source registry. Tier 3 social sources get keyword-filtered
to capture only high-impact signals at high frequency.

Tier 2 chokepoint sources (UKMTO, Freightos FBX) and Tier 4 regulatory
sources (IMO, IATA, WCO, UP Rail, BNSF) use Playwright + BeautifulSoup
for structured HTML extraction.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse

from app.ingestion.rss import RawSignal
from app.ingestion.sources import (
    ALLOWED_DOMAINS,
    SOCIAL_IMPACT_KEYWORDS,
    Source,
    get_noaa_source,
    get_social_sources,
    get_tier2_playwright_sources,
    get_tier4_scrape_sources,
)

logger = logging.getLogger(__name__)

# Compiled impact keyword filter for Tier 3 social sources
_IMPACT_RE = re.compile(SOCIAL_IMPACT_KEYWORDS)


def passes_impact_filter(text: str) -> bool:
    """Return True if text contains a high-impact disruption keyword."""
    return bool(_IMPACT_RE.search(text))


async def scrape_reddit_json(source: Source) -> list[RawSignal]:
    """Scrape Reddit via JSON API with source registry metadata."""
    import httpx

    url = source.url
    name = source.name
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

            # Tier 3 impact keyword gate — only ingest signals with disruption keywords
            if source.requires_keyword_filter and not passes_impact_filter(content):
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
                    source_key=source.source_key,
                    feed_name=name,
                    published_at=published_at,
                    source_type=source.source_type,
                    modes=source.modes,
                    reliability=source.reliability,
                )
            )

        logger.info(f"Scraped {len(signals)} posts from {name} (filtered from {len(children)})")

    except Exception as exc:
        logger.error(f"Error scraping {name}: {exc}")

    return signals


async def scrape_with_playwright(source: Source, selector: str = "body") -> list[RawSignal]:
    """Scrape a JS-rendered page using Playwright + BeautifulSoup.

    Uses source-specific extraction strategies for known high-value targets.
    Falls back to generic body text extraction for unknown sources.
    """
    from bs4 import BeautifulSoup
    from playwright.async_api import async_playwright

    url = source.url
    parsed = urlparse(url)
    if parsed.hostname not in ALLOWED_DOMAINS:
        logger.warning(f"Blocked scrape attempt to non-allowlisted domain: {parsed.hostname}")
        return []

    signals: list[RawSignal] = []
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) NobleIntel/3.0",
            )
            await page.goto(url, timeout=45000, wait_until="networkidle")
            html = await page.content()
            await browser.close()

        soup = BeautifulSoup(html, "lxml")

        # ── Source-specific extraction via dispatch table ───────────────
        key = source.source_key
        items: list[dict] = []

        extractor = _PLAYWRIGHT_EXTRACTORS.get(key)
        if extractor:
            items = extractor(soup, url)
        else:
            # Generic fallback: extract all text from main content area
            main = soup.select_one("main, article, .content, #content, body")
            text = main.get_text(separator="\n", strip=True) if main else ""
            if text:
                items = [{"title": source.name, "content": text[:5000], "url": url}]

        for item in items:
            signals.append(
                RawSignal(
                    title=item.get("title", source.name),
                    content=item["content"],
                    url=item.get("url", url),
                    source_key=source.source_key,
                    feed_name=source.name,
                    published_at=item.get("published_at", datetime.now(timezone.utc)),
                    source_type=source.source_type,
                    modes=source.modes,
                    reliability=source.reliability,
                )
            )

        logger.info(f"Playwright scraped {len(signals)} items from {source.name}")

    except Exception as exc:
        logger.error(f"Playwright scrape error for {source.name}: {exc}")

    return signals


# ── Source-specific BS4 extractors ──────────────────────────────────────────


def _extract_imo(soup, base_url: str) -> list[dict]:
    """Extract IMO News/WhatsNew items."""
    items = []
    # IMO uses SharePoint-style list items
    for el in soup.select(".ms-rtestate-field a, .dfwp-item a, .news-item a, article a"):
        title = el.get_text(strip=True)
        href = el.get("href", "")
        if not title or len(title) < 10:
            continue
        if href and not href.startswith("http"):
            href = f"https://www.imo.org{href}"
        # Get surrounding text as content
        parent = el.find_parent(["li", "div", "article", "tr"])
        content = parent.get_text(separator=" ", strip=True) if parent else title
        items.append({"title": title, "content": content[:2000], "url": href or base_url})
    # Fallback: grab the main content block
    if not items:
        main = soup.select_one("main, #content, .ms-rtestate-field, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "IMO Latest Updates", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_iata(soup, base_url: str) -> list[dict]:
    """Extract IATA Cargo program updates."""
    items = []
    # IATA Cargo page has sections with updates, links, content blocks
    for section in soup.select(".content-block, .card, article, .news-item, .accordion-item"):
        title_el = section.select_one("h2, h3, h4, .title, .card-title")
        title = title_el.get_text(strip=True) if title_el else ""
        content = section.get_text(separator=" ", strip=True)
        if not content or len(content) < 30:
            continue
        link_el = section.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.iata.org{href}"
        items.append({
            "title": title or "IATA Cargo Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    # Fallback
    if not items:
        main = soup.select_one("main, .main-content, article, #content")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "IATA Cargo Programs", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_freightos(soup, base_url: str) -> list[dict]:
    """Extract Freightos FBX pricing data."""
    items = []
    # FBX Lane Explorer — look for pricing tables/data
    for row in soup.select("table tr, .lane-row, .data-row, .index-card"):
        text = row.get_text(separator=" | ", strip=True)
        if not text or len(text) < 10:
            continue
        items.append({
            "title": f"FBX Index: {text[:60]}",
            "content": text[:1000],
            "url": base_url,
        })
    # Fallback: grab summary from main content
    if not items:
        main = soup.select_one("main, .content, #app, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            # Filter out navigation noise
            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 20]
            content = "\n".join(lines[:50])
            if content:
                items.append({"title": "Freightos FBX Index Update", "content": content[:5000], "url": base_url})
    return items[:30]


def _extract_ukmto(soup, base_url: str) -> list[dict]:
    """Extract UKMTO recent incidents from their Next.js rendered page."""
    items = []
    # UKMTO renders incident cards/rows
    for el in soup.select(".incident, .card, article, tr, .list-item, [class*='incident']"):
        text = el.get_text(separator=" | ", strip=True)
        if not text or len(text) < 15:
            continue
        # Try to find a date
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.ukmto.org{href}"
        items.append({
            "title": f"UKMTO Incident: {text[:80]}",
            "content": text[:2000],
            "url": href or base_url,
        })
    # Fallback: grab everything from main
    if not items:
        main = soup.select_one("main, #__next, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]
            if lines:
                items.append({
                    "title": "UKMTO Recent Incidents",
                    "content": "\n".join(lines[:30])[:5000],
                    "url": base_url,
                })
    return items[:20]


def _extract_rail_alerts(soup, base_url: str, source_key: str) -> list[dict]:
    """Extract service alerts from UP/BNSF."""
    items = []
    for el in soup.select(".alert, .service-alert, article, .announcement, tr, li"):
        text = el.get_text(separator=" ", strip=True)
        if not text or len(text) < 20:
            continue
        label = "UP" if source_key == "up_rail" else "BNSF"
        items.append({
            "title": f"{label} Alert: {text[:80]}",
            "content": text[:2000],
            "url": base_url,
        })
    if not items:
        main = soup.select_one("main, .content, #content, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": f"{source_key} Service Alerts", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_news_list(soup, base_url: str) -> list[dict]:
    """Generic news list extractor for WCO, EU DG TAXUD etc."""
    items = []
    for el in soup.select("article, .news-item, .list-item, .card, .views-row"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 20:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        items.append({
            "title": title or content[:60],
            "content": content[:2000],
            "url": href if href.startswith("http") else base_url,
        })
    if not items:
        main = soup.select_one("main, #content, .content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text:
                items.append({"title": "Regulatory Update", "content": text[:5000], "url": base_url})
    return items[:20]


# ── v2.0 Playwright Extractors ──────────────────────────────────────────


def _extract_alphaliner(soup, base_url: str) -> list[dict]:
    """Extract Alphaliner fleet/capacity data."""
    items = []
    for row in soup.select("table tr, .data-row, .fleet-row"):
        text = row.get_text(separator=" | ", strip=True)
        if not text or len(text) < 15:
            continue
        items.append({
            "title": f"Alphaliner: {text[:80]}",
            "content": text[:2000],
            "url": base_url,
        })
    if not items:
        main = soup.select_one("main, .content, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "Alphaliner Fleet Update", "content": text[:5000], "url": base_url})
    return items[:30]


def _extract_bimco(soup, base_url: str) -> list[dict]:
    """Extract BIMCO market analysis articles."""
    items = []
    for el in soup.select("article, .news-card, .card, .content-item, .list-item"):
        title_el = el.select_one("h2, h3, h4, .title, .card-title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 30:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.bimco.org{href}"
        items.append({
            "title": title or "BIMCO Market Analysis",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .main-content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "BIMCO Update", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_sea_intelligence(soup, base_url: str) -> list[dict]:
    """Extract Sea-Intelligence press releases."""
    items = []
    for el in soup.select("article, .press-release, .news-item, .card, .post"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 30:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://sea-intelligence.com{href}"
        items.append({
            "title": title or "Sea-Intelligence Analysis",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "Sea-Intelligence Press Release", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_tac_index(soup, base_url: str) -> list[dict]:
    """Extract TAC Index air cargo pricing data."""
    items = []
    for row in soup.select("table tr, .index-row, .data-card, .lane-data"):
        text = row.get_text(separator=" | ", strip=True)
        if not text or len(text) < 10:
            continue
        items.append({
            "title": f"TAC Index: {text[:80]}",
            "content": text[:1000],
            "url": base_url,
        })
    if not items:
        main = soup.select_one("main, .content, #app, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 15]
            if lines:
                items.append({"title": "TAC Index Update", "content": "\n".join(lines[:50])[:5000], "url": base_url})
    return items[:30]


def _extract_dat_freight(soup, base_url: str) -> list[dict]:
    """Extract DAT Freight & Analytics trendline data."""
    items = []
    for el in soup.select(".trend-card, .data-point, .chart-legend, table tr, article"):
        text = el.get_text(separator=" | ", strip=True)
        if not text or len(text) < 15:
            continue
        items.append({
            "title": f"DAT Trendline: {text[:80]}",
            "content": text[:1500],
            "url": base_url,
        })
    if not items:
        main = soup.select_one("main, .content, #content, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "DAT Freight Trendlines", "content": text[:5000], "url": base_url})
    return items[:30]


def _extract_iru(soup, base_url: str) -> list[dict]:
    """Extract IRU (International Road Transport Union) news."""
    items = []
    for el in soup.select("article, .news-item, .card, .teaser, .list-item"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 30:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.iru.org{href}"
        items.append({
            "title": title or "IRU Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "IRU News", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_port_shanghai(soup, base_url: str) -> list[dict]:
    """Extract Port of Shanghai (SIPG) news."""
    items = []
    for el in soup.select("article, .news-item, .list-item, .news-list li, .content-item"):
        title_el = el.select_one("h2, h3, h4, a, .title")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 20:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.portshanghai.com.cn{href}"
        items.append({
            "title": title or "Port of Shanghai Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, #content, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "Port of Shanghai News", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_uic(soup, base_url: str) -> list[dict]:
    """Extract UIC (International Union of Railways) news."""
    items = []
    for el in soup.select("article, .news-item, .card, .list-item, .enews-item"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 20:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://uic.org{href}"
        items.append({
            "title": title or "UIC Railway Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "UIC News", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_baltic_exchange(soup, base_url: str) -> list[dict]:
    """Extract Baltic Exchange market information."""
    items = []
    for el in soup.select("table tr, .market-data, .index-card, .data-row"):
        text = el.get_text(separator=" | ", strip=True)
        if not text or len(text) < 10:
            continue
        items.append({
            "title": f"Baltic Exchange: {text[:80]}",
            "content": text[:1500],
            "url": base_url,
        })
    if not items:
        main = soup.select_one("main, .content, #content, body")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "Baltic Exchange Update", "content": text[:5000], "url": base_url})
    return items[:30]


def _extract_icao(soup, base_url: str) -> list[dict]:
    """Extract ICAO (International Civil Aviation Organization) news."""
    items = []
    for el in soup.select("article, .news-item, .card, .list-item, .ms-rteElement-P"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 20:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.icao.int{href}"
        items.append({
            "title": title or "ICAO Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, article, #content")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "ICAO News", "content": text[:5000], "url": base_url})
    return items[:20]


def _extract_era(soup, base_url: str) -> list[dict]:
    """Extract ERA (EU Agency for Railways) press releases."""
    items = []
    for el in soup.select("article, .news-item, .card, .list-item, .views-row"):
        title_el = el.select_one("h2, h3, h4, .title, a")
        title = title_el.get_text(strip=True) if title_el else ""
        content = el.get_text(separator=" ", strip=True)
        if not content or len(content) < 20:
            continue
        link_el = el.select_one("a[href]")
        href = link_el.get("href", "") if link_el else ""
        if href and not href.startswith("http"):
            href = f"https://www.era.europa.eu{href}"
        items.append({
            "title": title or "ERA Update",
            "content": content[:2000],
            "url": href or base_url,
        })
    if not items:
        main = soup.select_one("main, .content, article")
        if main:
            text = main.get_text(separator="\n", strip=True)
            if text and len(text) > 50:
                items.append({"title": "ERA Press Release", "content": text[:5000], "url": base_url})
    return items[:20]


# Source key → extractor dispatch table (v2.0 expanded)
_PLAYWRIGHT_EXTRACTORS: dict[str, callable] = {
    "imo": lambda soup, url: _extract_imo(soup, url),
    "iata_cargo": lambda soup, url: _extract_iata(soup, url),
    "freightos_fbx_live": lambda soup, url: _extract_freightos(soup, url),
    "ukmto": lambda soup, url: _extract_ukmto(soup, url),
    "up_rail": lambda soup, url: _extract_rail_alerts(soup, url, "up_rail"),
    "bnsf_rail": lambda soup, url: _extract_rail_alerts(soup, url, "bnsf_rail"),
    "csx_rail": lambda soup, url: _extract_rail_alerts(soup, url, "csx_rail"),
    "ns_rail": lambda soup, url: _extract_rail_alerts(soup, url, "ns_rail"),
    "wco": lambda soup, url: _extract_news_list(soup, url),
    "eu_dg_taxud": lambda soup, url: _extract_news_list(soup, url),
    "alphaliner": lambda soup, url: _extract_alphaliner(soup, url),
    "bimco": lambda soup, url: _extract_bimco(soup, url),
    "sea_intelligence": lambda soup, url: _extract_sea_intelligence(soup, url),
    "tac_index": lambda soup, url: _extract_tac_index(soup, url),
    "dat_freight": lambda soup, url: _extract_dat_freight(soup, url),
    "iru": lambda soup, url: _extract_iru(soup, url),
    "port_shanghai": lambda soup, url: _extract_port_shanghai(soup, url),
    "uic": lambda soup, url: _extract_uic(soup, url),
    "baltic_exchange": lambda soup, url: _extract_baltic_exchange(soup, url),
    "icao": lambda soup, url: _extract_icao(soup, url),
    "eu_era": lambda soup, url: _extract_era(soup, url),
}


# ── NOAA JSON API fetcher ───────────────────────────────────────────────────


async def fetch_noaa_alerts() -> list[RawSignal]:
    """Fetch NOAA weather alerts via the api.weather.gov JSON API.

    Filters for transport-relevant event types (hurricanes, storms, fog, etc.)
    """
    import httpx

    source = get_noaa_source()
    if not source:
        logger.warning("NOAA source not found in registry")
        return []

    TRANSPORT_RELEVANT_EVENTS = {
        "Hurricane Warning", "Hurricane Watch", "Tropical Storm Warning",
        "Tropical Storm Watch", "Storm Warning", "Gale Warning",
        "Dense Fog Advisory", "Freezing Rain Advisory", "Winter Storm Warning",
        "Blizzard Warning", "Ice Storm Warning", "High Wind Warning",
        "Tornado Warning", "Severe Thunderstorm Warning", "Flood Warning",
        "Coastal Flood Warning", "Tsunami Warning", "Tsunami Watch",
        "Special Marine Warning", "Marine Weather Statement",
    }

    signals: list[RawSignal] = []
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(
                source.url,
                headers={"User-Agent": "(NobleIntel, contact@nobleverse.io)"},
            )
            response.raise_for_status()
            data = response.json()

        features = data.get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            event = props.get("event", "")
            headline = props.get("headline", "")
            description = props.get("description", "")

            # Only ingest transport-relevant weather events
            if event not in TRANSPORT_RELEVANT_EVENTS:
                continue

            content = f"{headline}\n\n{description}" if description else headline
            if not content:
                continue

            signals.append(
                RawSignal(
                    title=headline or event,
                    content=content[:3000],
                    url=props.get("@id", source.url),
                    source_key=source.source_key,
                    feed_name=source.name,
                    published_at=datetime.now(timezone.utc),
                    source_type=source.source_type,
                    modes=source.modes,
                    reliability=source.reliability,
                )
            )

        logger.info(f"NOAA: {len(signals)} transport-relevant alerts from {len(features)} total")

    except Exception as exc:
        logger.error(f"Error fetching NOAA alerts: {exc}")

    return signals


async def scrape_all_social() -> list[RawSignal]:
    """Scrape all Tier 3 social intelligence sources (Reddit)."""
    all_signals: list[RawSignal] = []

    for source in get_social_sources():
        signals = await scrape_reddit_json(source)
        all_signals.extend(signals)

    logger.info(f"Total social signals (impact-filtered): {len(all_signals)}")
    return all_signals


async def scrape_tier2_non_rss() -> list[RawSignal]:
    """Scrape Tier 2 sources that need Playwright or JSON APIs (UKMTO, NOAA)."""
    all_signals: list[RawSignal] = []

    # NOAA JSON API
    noaa_signals = await fetch_noaa_alerts()
    all_signals.extend(noaa_signals)

    # Playwright sources (UKMTO etc.)
    for source in get_tier2_playwright_sources():
        signals = await scrape_with_playwright(source)
        all_signals.extend(signals)

    logger.info(f"Total Tier 2 non-RSS signals: {len(all_signals)}")
    return all_signals


async def scrape_tier1_playwright() -> list[RawSignal]:
    """Scrape all Tier 1 sources that need Playwright (ports, pricing)."""
    from app.ingestion.sources import get_tier1_playwright_sources

    all_signals: list[RawSignal] = []
    for source in get_tier1_playwright_sources():
        signals = await scrape_with_playwright(source)
        all_signals.extend(signals)

    logger.info(f"Total Tier 1 Playwright signals: {len(all_signals)}")
    return all_signals


async def scrape_all_regulatory() -> list[RawSignal]:
    """Scrape all Tier 4 regulatory sources that need Playwright."""
    all_signals: list[RawSignal] = []

    for source in get_tier4_scrape_sources():
        signals = await scrape_with_playwright(source)
        all_signals.extend(signals)

    logger.info(f"Total regulatory scrape signals: {len(all_signals)}")
    return all_signals


# Backward compat alias — the old scraper just did Reddit
async def scrape_all_sources() -> list[RawSignal]:
    """Scrape all social sources (backward compat)."""
    return await scrape_all_social()
