"""
Diagnostic: Qdrant vector counts by transport_mode + live scraper smoke test.
Run: .venv/bin/python tests/diagnostic_vector_and_scraper.py
"""
import asyncio
import sys
import os
import json
import traceback
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# ── ensure project root on path ──
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ─────────────────────────────────────────────
# PART 1 — Qdrant Vector DB Audit
# ─────────────────────────────────────────────
async def audit_qdrant():
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333")
    COLLECTION = os.getenv("QDRANT_COLLECTION", "intel_signals")

    print("=" * 60)
    print("PART 1: QDRANT VECTOR DB AUDIT")
    print("=" * 60)
    print(f"  URL:        {QDRANT_URL}")
    print(f"  Collection: {COLLECTION}")
    print()

    try:
        client = AsyncQdrantClient(url=QDRANT_URL, timeout=10)
    except Exception as e:
        print(f"  ❌ Cannot connect to Qdrant: {e}")
        return

    # Check if collection exists
    try:
        collections = await client.get_collections()
        names = [c.name for c in collections.collections]
        if COLLECTION not in names:
            print(f"  ❌ Collection '{COLLECTION}' does not exist!")
            print(f"     Available: {names}")
            await client.close()
            return
    except Exception as e:
        print(f"  ❌ Qdrant unreachable: {e}")
        return

    # Total count
    try:
        info = await client.get_collection(COLLECTION)
        total = getattr(info, "points_count", 0)
        print(f"  Total vectors: {total}")
        print(f"  Status:        {info.status.value if info.status else 'unknown'}")
        print()
    except Exception as e:
        print(f"  ❌ Cannot get collection info: {e}")
        await client.close()
        return

    if total == 0:
        print("  ⚠️  Collection is EMPTY — no vectors ingested yet.")
        await client.close()
        return

    # Count by transport_mode
    modes = ["ocean", "air", "rail", "road", "multimodal"]
    print("  Vectors by transport_mode:")
    print("  " + "-" * 40)
    mode_counts = {}
    for mode in modes:
        try:
            result = await client.count(
                collection_name=COLLECTION,
                count_filter=Filter(
                    must=[FieldCondition(key="transport_mode", match=MatchValue(value=mode))]
                ),
                exact=True,
            )
            count = result.count
        except Exception:
            count = "error"
        mode_counts[mode] = count
        bar = "█" * (count if isinstance(count, int) else 0)
        print(f"    {mode:<12} {str(count):>5}  {bar}")

    # Count with no transport_mode (NULL / missing)
    # Scroll a sample to check for missing transport_mode
    try:
        sample = await client.scroll(
            collection_name=COLLECTION,
            limit=20,
            with_payload=True,
        )
        missing_mode = sum(1 for pt in sample[0] if not (pt.payload or {}).get("transport_mode"))
        has_source_type = sum(1 for pt in sample[0] if (pt.payload or {}).get("source_type"))
        has_reliability = sum(1 for pt in sample[0] if (pt.payload or {}).get("reliability_score") is not None)
        print()
        print(f"  Sample analysis (first {len(sample[0])} vectors):")
        print(f"    Missing transport_mode: {missing_mode}/{len(sample[0])}")
        print(f"    Has source_type:        {has_source_type}/{len(sample[0])}")
        print(f"    Has reliability_score:  {has_reliability}/{len(sample[0])}")
    except Exception as e:
        print(f"  ⚠️  Could not scroll sample: {e}")

    # Count by source_type (new metadata)
    source_types = ["news", "official", "social", "pricing"]
    print()
    print("  Vectors by source_type:")
    print("  " + "-" * 40)
    for st in source_types:
        try:
            result = await client.count(
                collection_name=COLLECTION,
                count_filter=Filter(
                    must=[FieldCondition(key="source_type", match=MatchValue(value=st))]
                ),
                exact=True,
            )
            count = result.count
        except Exception:
            count = "error"
        bar = "█" * (count if isinstance(count, int) else 0)
        print(f"    {st:<12} {str(count):>5}  {bar}")

    # Show a few sample payloads
    print()
    print("  Sample payloads (first 3 vectors):")
    print("  " + "-" * 40)
    try:
        sample = await client.scroll(
            collection_name=COLLECTION,
            limit=3,
            with_payload=True,
        )
        for i, pt in enumerate(sample[0]):
            p = pt.payload or {}
            print(f"    [{i+1}] id={pt.id}")
            print(f"        source:         {p.get('source', 'N/A')}")
            print(f"        transport_mode:  {p.get('transport_mode', 'N/A')}")
            print(f"        source_type:     {p.get('source_type', 'N/A')}")
            print(f"        reliability:     {p.get('reliability_score', 'N/A')}")
            print(f"        region:          {p.get('region', 'N/A')}")
            print(f"        risk_score:      {p.get('risk_score', 'N/A')}")
            title = (p.get("title") or "")[:80]
            print(f"        title:           {title}")
            print()
    except Exception as e:
        print(f"  ⚠️  Could not fetch sample: {e}")

    await client.close()

# ─────────────────────────────────────────────
# PART 2 — Live Scraper / Feed Smoke Test
# ─────────────────────────────────────────────
def test_feed(name, url, timeout=15):
    """Try to fetch a URL and report status."""
    req = Request(url, headers={"User-Agent": "NobleIntel/1.0 (diagnostic)"})
    try:
        resp = urlopen(req, timeout=timeout)
        code = resp.getcode()
        content_type = resp.headers.get("Content-Type", "unknown")
        body = resp.read(2048).decode("utf-8", errors="replace")
        size = len(body)
        # Quick sanity: does it look like RSS/XML or JSON?
        looks_like = "unknown"
        if "<rss" in body.lower() or "<feed" in body.lower() or "<channel" in body.lower():
            looks_like = "RSS/Atom XML"
        elif body.strip().startswith("{") or body.strip().startswith("["):
            looks_like = "JSON"
        elif "<html" in body.lower():
            looks_like = "HTML (not a feed!)"
        return {
            "status": code,
            "content_type": content_type[:40],
            "format": looks_like,
            "size": size,
            "error": None,
        }
    except HTTPError as e:
        return {"status": e.code, "error": str(e.reason), "content_type": None, "format": None, "size": 0}
    except URLError as e:
        return {"status": None, "error": str(e.reason), "content_type": None, "format": None, "size": 0}
    except Exception as e:
        return {"status": None, "error": str(e)[:80], "content_type": None, "format": None, "size": 0}


def smoke_test_scrapers():
    print()
    print("=" * 60)
    print("PART 2: LIVE FEED / SCRAPER SMOKE TEST")
    print("=" * 60)
    print()

    # Key feeds to test — one from each category
    test_targets = [
        # Tier 2 — News RSS
        ("gCaptain RSS", "https://gcaptain.com/feed/"),
        ("Air Cargo News RSS", "https://www.aircargonews.net/feed/"),
        ("The Loadstar RSS", "https://theloadstar.com/feed/"),
        ("Freightwaves RSS", "https://www.freightwaves.com/feed"),
        ("Railway Age RSS", "https://www.railwayage.com/feed/"),
        ("Supply Chain Dive RSS", "https://www.supplychaindive.com/feeds/news/"),
        # Tier 2 — Chokepoints
        ("UKMTO Warnings", "https://www.ukmto.org/indian-ocean/latest-warnings"),
        ("NOAA Active Alerts", "https://alerts.weather.gov/cap/us.php?x=0"),
        # Tier 2 — Pricing
        ("Freightos FBX", "https://fbx.freightos.com/api/lane-explorer"),
        # Tier 3 — Reddit (JSON API)
        ("Reddit r/logistics", "https://www.reddit.com/r/logistics/new.json?limit=5"),
        ("Reddit r/shipping", "https://www.reddit.com/r/shipping/new.json?limit=5"),
        ("Reddit r/truckers", "https://www.reddit.com/r/Truckers/new.json?limit=5"),
        # Tier 4 — Regulatory
        ("IMO News RSS", "https://www.imo.org/en/MediaCentre/LatestNews/Pages/default.aspx"),
        ("IATA Cargo RSS", "https://www.iata.org/en/programs/cargo/"),
        ("US Federal Register", "https://www.federalregister.gov/api/v1/documents.json?conditions%5Bagencies%5D%5B%5D=customs-and-border-protection&per_page=5"),
    ]

    ok = 0
    fail = 0
    for name, url in test_targets:
        result = test_feed(name, url)
        status = result["status"]
        if status and 200 <= status < 400:
            icon = "OK"
            ok += 1
            detail = f"  {result['format']}"
        else:
            icon = "FAIL"
            fail += 1
            detail = f"  {result['error'] or f'HTTP {status}'}"

        print(f"  [{icon:>4}] {status or '---':>3}  {name:<28} {detail}")

    print()
    print(f"  Results: {ok} OK, {fail} FAILED out of {len(test_targets)} targets")

    if fail > 0:
        print()
        print("  Common issues:")
        print("    403 Forbidden  → Site blocks bot User-Agent or requires auth")
        print("    429 Too Many   → Rate limited, need backoff/proxy")
        print("    HTML response  → URL is a webpage, not a feed endpoint")
        print("    Timeout        → Site slow or blocking; may need Playwright")


# ─────────────────────────────────────────────
# PART 3 — PostgreSQL signal counts
# ─────────────────────────────────────────────
def audit_postgres():
    print()
    print("=" * 60)
    print("PART 3: POSTGRESQL SIGNAL COUNTS")
    print("=" * 60)
    print()

    try:
        import psycopg2
    except ImportError:
        # Try psycopg (v3)
        try:
            import psycopg
            conn = psycopg.connect(os.getenv("DATABASE_URL", "postgresql://noble@127.0.0.1:5432/noble_intel"))
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM signals")
            total = cur.fetchone()[0]
            print(f"  Total signals: {total}")

            cur.execute("SELECT transport_mode, COUNT(*) FROM signals GROUP BY transport_mode ORDER BY COUNT(*) DESC")
            rows = cur.fetchall()
            print()
            print("  By transport_mode:")
            print("  " + "-" * 40)
            for mode, cnt in rows:
                bar = "█" * min(cnt, 50)
                print(f"    {(mode or 'NULL'):<12} {cnt:>5}  {bar}")

            cur.execute("SELECT source_type, COUNT(*) FROM signals GROUP BY source_type ORDER BY COUNT(*) DESC")
            rows = cur.fetchall()
            print()
            print("  By source_type:")
            print("  " + "-" * 40)
            for st, cnt in rows:
                bar = "█" * min(cnt, 50)
                print(f"    {(st or 'NULL'):<12} {cnt:>5}  {bar}")

            cur.execute("SELECT source_name, COUNT(*) FROM signals GROUP BY source_name ORDER BY COUNT(*) DESC LIMIT 15")
            rows = cur.fetchall()
            print()
            print("  Top sources:")
            print("  " + "-" * 40)
            for src, cnt in rows:
                print(f"    {(src or 'unknown'):<35} {cnt:>5}")

            conn.close()
            return
        except ImportError:
            pass

        # Fallback to psql CLI
        print("  (Using psql CLI fallback)")
        import subprocess
        db_url = os.getenv("DATABASE_URL", "postgresql://noble@127.0.0.1:5432/noble_intel")
        queries = [
            ("Total signals", "SELECT COUNT(*) FROM signals;"),
            ("By transport_mode", "SELECT transport_mode, COUNT(*) FROM signals GROUP BY transport_mode ORDER BY COUNT(*) DESC;"),
            ("By source_type", "SELECT source_type, COUNT(*) FROM signals GROUP BY source_type ORDER BY COUNT(*) DESC;"),
            ("Top sources", "SELECT source_name, COUNT(*) FROM signals GROUP BY source_name ORDER BY COUNT(*) DESC LIMIT 15;"),
        ]
        for label, sql in queries:
            print(f"\n  {label}:")
            try:
                out = subprocess.check_output(
                    ["psql", db_url, "-t", "-A", "-c", sql],
                    stderr=subprocess.STDOUT, timeout=10
                ).decode().strip()
                for line in out.split("\n"):
                    print(f"    {line}")
            except Exception as e:
                print(f"    ❌ {e}")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
async def main():
    # Load .env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    await audit_qdrant()
    smoke_test_scrapers()
    audit_postgres()

    print()
    print("=" * 60)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
