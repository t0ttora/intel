"""Task 3: Re-tag legacy vectors with updated metadata.

Reads all existing signals from PostgreSQL, re-runs the multimodal classifier
and region tagger, then updates both PostgreSQL and Qdrant with:
  - transport_mode (ocean, air, rail, road, multimodal)
  - source_type (based on source_key mapping)
  - reliability_score (calibrated default)
  - region (geo-tagged)

Run: cd intel && .venv/bin/python scripts/retag_legacy_signals.py
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid

# Ensure project root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Source key → metadata mapping ────────────────────────────────────────────
# For legacy signals that were ingested before the source registry existed.

LEGACY_SOURCE_MAP: dict[str, dict] = {
    "general_news": {
        "source_type": "news",
        "reliability": 0.6,
        "modes_hint": None,  # Must detect from content
    },
    "reddit": {
        "source_type": "social",
        "reliability": 0.35,
        "modes_hint": None,
    },
    "tier1_news": {
        "source_type": "news",
        "reliability": 0.8,
        "modes_hint": None,
    },
}


async def retag_all():
    """Main re-tagging pipeline."""
    # Load env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    from app.db.pool import get_pool
    from app.intelligence.signal_tagger import tag_signal
    from app.scoring.geo_criticality import detect_geo_zone
    from app.vectordb.client import get_qdrant

    from qdrant_client.models import PointStruct

    pool = await get_pool()
    qdrant = await get_qdrant()
    collection = os.getenv("QDRANT_COLLECTION", "intel_signals")

    # ── Phase 1: Read all signals from PostgreSQL ──────────────────────
    logger.info("Phase 1: Reading all signals from PostgreSQL...")
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "SELECT id, source, title, content, transport_mode, source_type, "
                "reliability_score, region, geo_zone FROM signals"
            )
            rows = await cur.fetchall()

    logger.info(f"  Found {len(rows)} signals in PostgreSQL")

    # ── Phase 2: Re-tag each signal ──────────────────────────────────
    logger.info("Phase 2: Re-tagging signals...")
    pg_updates = []
    qdrant_updates = []

    stats = {
        "total": len(rows),
        "mode_assigned": 0,
        "source_type_assigned": 0,
        "region_assigned": 0,
        "already_good": 0,
    }

    for row in rows:
        sig_id, source, title, content, current_mode, current_source_type, \
            current_reliability, current_region, current_geo_zone = row

        full_text = f"{title or ''} {content or ''}"

        # ── Transport mode ──────────────────────────────────────────
        new_mode = current_mode
        if not current_mode:
            detected_mode, detected_region = tag_signal(full_text)
            new_mode = detected_mode
            if new_mode:
                stats["mode_assigned"] += 1
        else:
            detected_mode, detected_region = None, None

        # ── Region ──────────────────────────────────────────────────
        new_region = current_region
        if not current_region:
            if detected_region is None:
                _, detected_region = tag_signal(full_text)
            new_region = detected_region
            if new_region:
                stats["region_assigned"] += 1

        # ── Source type + reliability ───────────────────────────────
        new_source_type = current_source_type
        new_reliability = current_reliability
        if not current_source_type and source in LEGACY_SOURCE_MAP:
            meta = LEGACY_SOURCE_MAP[source]
            new_source_type = meta["source_type"]
            new_reliability = meta["reliability"]
            stats["source_type_assigned"] += 1

        # ── Geo zone (re-detect if missing) ──────────────────────
        new_geo_zone = current_geo_zone
        if not current_geo_zone:
            new_geo_zone = detect_geo_zone(full_text)

        # Check if anything changed
        changed = (
            new_mode != current_mode
            or new_source_type != current_source_type
            or new_reliability != current_reliability
            or new_region != current_region
            or new_geo_zone != current_geo_zone
        )

        if not changed:
            stats["already_good"] += 1
            continue

        # Queue PostgreSQL update
        pg_updates.append((
            new_mode, new_source_type, new_reliability, new_region, new_geo_zone, sig_id
        ))

        # Queue Qdrant payload update
        qdrant_updates.append({
            "signal_id": str(sig_id),
            "transport_mode": new_mode or "",
            "source_type": new_source_type or "",
            "reliability_score": new_reliability or 0.5,
            "region": new_region or "",
            "geo_zone": new_geo_zone or "",
        })

    # ── Phase 3: Batch update PostgreSQL ──────────────────────────────
    logger.info(f"Phase 3: Updating {len(pg_updates)} rows in PostgreSQL...")
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            for update in pg_updates:
                await cur.execute(
                    """
                    UPDATE signals
                    SET transport_mode = %s,
                        source_type = %s,
                        reliability_score = %s,
                        region = %s,
                        geo_zone = %s
                    WHERE id = %s
                    """,
                    update,
                )
        await conn.commit()
    logger.info("  PostgreSQL updates committed.")

    # ── Phase 4: Update Qdrant payloads ──────────────────────────────
    logger.info(f"Phase 4: Updating {len(qdrant_updates)} vectors in Qdrant...")

    # Scroll all points to get their IDs mapped by signal_id
    all_points = []
    offset = None
    while True:
        result = await qdrant.scroll(
            collection_name=collection,
            limit=100,
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        points, next_offset = result
        all_points.extend(points)
        if next_offset is None:
            break
        offset = next_offset

    logger.info(f"  Found {len(all_points)} vectors in Qdrant")

    # Build signal_id → point_ids mapping
    signal_to_points: dict[str, list] = {}
    for pt in all_points:
        payload = pt.payload or {}
        sid = payload.get("signal_id", "")
        if sid:
            signal_to_points.setdefault(sid, []).append(pt.id)

    # Update Qdrant payloads
    updated_vectors = 0
    for update in qdrant_updates:
        sid = update["signal_id"]
        point_ids = signal_to_points.get(sid, [])
        if not point_ids:
            continue

        payload_patch = {
            "transport_mode": update["transport_mode"],
            "source_type": update["source_type"],
            "reliability_score": update["reliability_score"],
            "region": update["region"],
            "geo_zone": update["geo_zone"],
        }

        await qdrant.set_payload(
            collection_name=collection,
            payload=payload_patch,
            points=point_ids,
        )
        updated_vectors += len(point_ids)

    logger.info(f"  Updated {updated_vectors} Qdrant vectors")

    # ── Summary ──────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("RE-TAG LEGACY SIGNALS — COMPLETE")
    print("=" * 60)
    print(f"  Total signals:         {stats['total']}")
    print(f"  Mode assigned:         {stats['mode_assigned']}")
    print(f"  Source type assigned:   {stats['source_type_assigned']}")
    print(f"  Region assigned:       {stats['region_assigned']}")
    print(f"  Already correct:       {stats['already_good']}")
    print(f"  PG rows updated:       {len(pg_updates)}")
    print(f"  Qdrant vectors updated:{updated_vectors}")
    print()

    await qdrant.close()


if __name__ == "__main__":
    asyncio.run(retag_all())
