"""Manual one-shot Tier 1 ingestion — live physical data, pricing, GEOINT, cyber.

Runs all Tier 1 handlers (RSS + API + Playwright) directly without Celery
to immediately populate signals from port authorities, pricing platforms,
GEOINT sources, and cyber feeds.

Run: cd intel && .venv/bin/python -m scripts.manual_ingest_tier1
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


async def run_tier1_ingest():
    """Execute Tier 1: RSS + API + Playwright ingestion."""
    # Load env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    from app.ingestion.handlers import ingest_rss, ingest_api, ingest_html_playwright
    from app.ingestion.sources import (
        get_tier1_rss_sources,
        get_tier1_playwright_sources,
        get_tier1_api_sources,
    )

    total_stats = {
        "tier1_rss": {},
        "tier1_api": {},
        "tier1_playwright": {},
    }

    rss_sources = get_tier1_rss_sources()
    pw_sources = get_tier1_playwright_sources()
    api_sources = get_tier1_api_sources()

    print()
    print("═" * 60)
    print("  TIER 1 MANUAL INGESTION — LIVE DATA")
    print("═" * 60)
    print(f"  RSS sources:        {len(rss_sources)}")
    print(f"  API sources:        {len(api_sources)}")
    print(f"  Playwright sources: {len(pw_sources)}")
    print("═" * 60)

    # ── Phase 1: RSS feeds ───────────────────────────────────────────
    print()
    print("─" * 60)
    print("  PHASE 1: TIER 1 RSS FEEDS")
    print("─" * 60)
    t0 = time.time()
    try:
        stats = await ingest_rss(rss_sources, tier=1, default_source_weight=0.8)
        total_stats["tier1_rss"] = stats
        print(f"  Result: {stats}")
    except Exception as exc:
        logger.error(f"Tier 1 RSS failed: {exc}", exc_info=True)
        total_stats["tier1_rss"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Phase 2: API endpoints ───────────────────────────────────────
    print()
    print("─" * 60)
    print("  PHASE 2: TIER 1 API ENDPOINTS")
    print("─" * 60)
    t0 = time.time()
    try:
        stats = await ingest_api(tier=1, default_source_weight=0.8)
        total_stats["tier1_api"] = stats
        print(f"  Result: {stats}")
    except Exception as exc:
        logger.error(f"Tier 1 API failed: {exc}", exc_info=True)
        total_stats["tier1_api"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Phase 3: Playwright scrapers ─────────────────────────────────
    print()
    print("─" * 60)
    print("  PHASE 3: TIER 1 PLAYWRIGHT SCRAPERS")
    print("─" * 60)
    t0 = time.time()
    try:
        stats = await ingest_html_playwright(pw_sources, tier=1, default_source_weight=0.8)
        total_stats["tier1_playwright"] = stats
        print(f"  Result: {stats}")
    except Exception as exc:
        logger.error(f"Tier 1 Playwright failed: {exc}", exc_info=True)
        total_stats["tier1_playwright"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Summary ──────────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  TIER 1 INGESTION COMPLETE — SUMMARY")
    print("═" * 60)

    total_ingested = 0
    total_fetched = 0
    for phase, stats in total_stats.items():
        fetched = stats.get("fetched", 0)
        ingested = stats.get("ingested", 0)
        filtered = stats.get("filtered", 0)
        duped = stats.get("duplicated", 0)
        errors = stats.get("errors", 0)
        total_ingested += ingested
        total_fetched += fetched
        print(f"  {phase:>18}: fetched={fetched} ingested={ingested} filtered={filtered} duped={duped} errors={errors}")

    print(f"\n  TOTAL: {total_fetched} fetched → {total_ingested} ingested")

    # ── Verify: Qdrant counts ────────────────────────────────────────
    print()
    print("═" * 60)
    print("  VERIFICATION: QDRANT COUNTS BY TRANSPORT MODE")
    print("═" * 60)

    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    collection = os.getenv("QDRANT_COLLECTION", "intel_signals")
    client = AsyncQdrantClient(url=qdrant_url, timeout=10)

    try:
        info = await client.get_collection(collection)
        total_vectors = getattr(info, "points_count", 0)
        print(f"\n  Total vectors: {total_vectors}")
        print()

        for mode in ["ocean", "air", "rail", "road", "multimodal"]:
            result = await client.count(
                collection_name=collection,
                count_filter=Filter(
                    must=[FieldCondition(key="transport_mode", match=MatchValue(value=mode))]
                ),
                exact=True,
            )
            bar = "█" * min(result.count, 60)
            print(f"    {mode:<12} {result.count:>5}  {bar}")

        print()
        for st in ["news", "official", "social", "pricing", "geoint", "cyber"]:
            result = await client.count(
                collection_name=collection,
                count_filter=Filter(
                    must=[FieldCondition(key="source_type", match=MatchValue(value=st))]
                ),
                exact=True,
            )
            bar = "█" * min(result.count, 60)
            print(f"    {st:<12} {result.count:>5}  {bar}")
    except Exception as exc:
        logger.error(f"Qdrant verification failed: {exc}")
    finally:
        await client.close()

    print()


if __name__ == "__main__":
    asyncio.run(run_tier1_ingest())
