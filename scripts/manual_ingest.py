"""Task 4: Manual one-shot ingestion trigger for Tier 2 + Tier 3.

Runs the ingestion pipeline directly (without Celery) to immediately
populate the air, rail, and multimodal buckets and prove the new schema works.

Run: cd intel && .venv/bin/python scripts/manual_ingest.py
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


async def run_manual_ingest():
    """Execute Tier 2 RSS + Tier 2 non-RSS + Tier 3 social ingestion."""
    # Load env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    from app.ingestion.rss import fetch_all_feeds
    from app.ingestion.scraper import scrape_all_social, scrape_tier2_non_rss
    from app.ingestion.pipeline import ingest_signals

    total_stats = {
        "tier2_rss": {},
        "tier2_non_rss": {},
        "tier3_social": {},
    }

    # ── Tier 2: RSS feeds ────────────────────────────────────────────
    print()
    print("=" * 60)
    print("PHASE 1: TIER 2 — RSS FEEDS")
    print("=" * 60)
    t0 = time.time()
    try:
        rss_signals = await fetch_all_feeds()
        logger.info(f"Fetched {len(rss_signals)} raw RSS signals")
        if rss_signals:
            stats = await ingest_signals(rss_signals, default_source_weight=0.5)
            total_stats["tier2_rss"] = stats
            print(f"  Result: {stats}")
        else:
            print("  No RSS signals fetched")
    except Exception as exc:
        logger.error(f"Tier 2 RSS failed: {exc}")
        total_stats["tier2_rss"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Tier 2: Non-RSS (NOAA JSON + UKMTO Playwright) ──────────────
    print()
    print("=" * 60)
    print("PHASE 2: TIER 2 — NON-RSS (NOAA + UKMTO)")
    print("=" * 60)
    t0 = time.time()
    try:
        non_rss_signals = await scrape_tier2_non_rss()
        logger.info(f"Fetched {len(non_rss_signals)} non-RSS signals")
        if non_rss_signals:
            stats = await ingest_signals(non_rss_signals, default_source_weight=0.5)
            total_stats["tier2_non_rss"] = stats
            print(f"  Result: {stats}")
        else:
            print("  No non-RSS signals fetched")
    except Exception as exc:
        logger.error(f"Tier 2 non-RSS failed: {exc}")
        total_stats["tier2_non_rss"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Tier 3: Social / Reddit ──────────────────────────────────────
    print()
    print("=" * 60)
    print("PHASE 3: TIER 3 — SOCIAL INTELLIGENCE (REDDIT)")
    print("=" * 60)
    t0 = time.time()
    try:
        social_signals = await scrape_all_social()
        logger.info(f"Fetched {len(social_signals)} social signals (impact-filtered)")
        if social_signals:
            stats = await ingest_signals(
                social_signals,
                default_source_weight=0.35,
                skip_keyword_filter=True,
            )
            total_stats["tier3_social"] = stats
            print(f"  Result: {stats}")
        else:
            print("  No social signals matched impact filter")
    except Exception as exc:
        logger.error(f"Tier 3 social failed: {exc}")
        total_stats["tier3_social"] = {"error": str(exc)}
    print(f"  Duration: {time.time() - t0:.1f}s")

    # ── Summary ──────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("MANUAL INGESTION COMPLETE — SUMMARY")
    print("=" * 60)

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
        print(f"  {phase:>16}: fetched={fetched} ingested={ingested} filtered={filtered} duped={duped} errors={errors}")

    print(f"\n  TOTAL: {total_fetched} fetched → {total_ingested} ingested")
    print()

    # ── Verify: Count by transport_mode in Qdrant ────────────────────
    print("=" * 60)
    print("VERIFICATION: QDRANT COUNTS BY TRANSPORT MODE")
    print("=" * 60)

    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    qdrant_url = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    collection = os.getenv("QDRANT_COLLECTION", "intel_signals")
    client = AsyncQdrantClient(url=qdrant_url, timeout=10)

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

    # Count with source_type
    print()
    for st in ["news", "official", "social", "pricing"]:
        result = await client.count(
            collection_name=collection,
            count_filter=Filter(
                must=[FieldCondition(key="source_type", match=MatchValue(value=st))]
            ),
            exact=True,
        )
        bar = "█" * min(result.count, 60)
        print(f"    {st:<12} {result.count:>5}  {bar}")

    await client.close()
    print()


if __name__ == "__main__":
    asyncio.run(run_manual_ingest())
