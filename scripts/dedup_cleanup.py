#!/usr/bin/env python3
"""Cleanup duplicate vectors in Qdrant.

Strategy:
1. Scroll all vectors in the collection.
2. Group by URL payload field.
3. For each URL, keep only the vector with the latest created_at per chunk_index.
4. Delete the rest.
5. Re-ID survivors to deterministic md5(url::chunk_index) IDs via upsert + delete old.

Usage:
    cd /Users/tora/nobleverse/docs/infrastructure/intel
    python -m scripts.dedup_cleanup [--dry-run]
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import sys
from collections import defaultdict

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger(__name__)

COLLECTION = "intel_signals"
QDRANT_URL = "http://localhost:6333"
SCROLL_BATCH = 100


def deterministic_id(url: str, chunk_index: int) -> str:
    """Same logic as dedup.url_vector_id — md5(url::chunk_index)."""
    key = f"{url.strip()}::{chunk_index}"
    return hashlib.md5(key.encode()).hexdigest()


async def main(dry_run: bool = False) -> None:
    client = AsyncQdrantClient(url=QDRANT_URL, timeout=60)

    # ── Step 1: Scroll all points ─────────────────────────────────────────
    logger.info("Scrolling all vectors...")
    all_points: list[dict] = []
    offset = None
    while True:
        results, next_offset = await client.scroll(
            collection_name=COLLECTION,
            limit=SCROLL_BATCH,
            offset=offset,
            with_payload=True,
            with_vectors=True,
        )
        for pt in results:
            all_points.append({
                "id": pt.id,
                "payload": pt.payload or {},
                "vector": pt.vector,
            })
        if next_offset is None:
            break
        offset = next_offset

    logger.info(f"Total vectors found: {len(all_points)}")

    # ── Step 2: Group by (url, chunk_index) ───────────────────────────────
    # Key: (url, chunk_index) → list of points
    groups: dict[tuple[str, int], list[dict]] = defaultdict(list)
    no_url_count = 0

    for pt in all_points:
        url = pt["payload"].get("url", "")
        chunk_idx = pt["payload"].get("chunk_index", 0)
        if not url:
            # Fallback: group by signal_id + chunk_index
            signal_id = pt["payload"].get("signal_id", str(pt["id"]))
            groups[(f"__signal__{signal_id}", chunk_idx)].append(pt)
            no_url_count += 1
        else:
            groups[(url, chunk_idx)].append(pt)

    if no_url_count:
        logger.info(f"  {no_url_count} vectors have no URL payload (legacy data)")

    # ── Step 3: Find duplicates ───────────────────────────────────────────
    to_delete: list[str] = []
    to_re_id: list[tuple[dict, str]] = []  # (point, new_id)

    for (key, chunk_idx), pts in groups.items():
        if key.startswith("__signal__"):
            # Legacy points without URL — keep all, can't dedup
            continue

        # Sort by created_at descending, keep newest
        pts.sort(
            key=lambda p: p["payload"].get("created_at", ""),
            reverse=True,
        )
        winner = pts[0]
        new_id = deterministic_id(key, chunk_idx)

        # Mark the winner for re-ID (if its current ID differs)
        if str(winner["id"]) != new_id:
            to_re_id.append((winner, new_id))

        # Mark losers for deletion
        for loser in pts[1:]:
            to_delete.append(str(loser["id"]))

    dup_count = len(to_delete)
    re_id_count = len(to_re_id)
    logger.info(f"Duplicate vectors to delete: {dup_count}")
    logger.info(f"Vectors to re-ID to deterministic IDs: {re_id_count}")

    if dry_run:
        logger.info("[DRY RUN] No changes made.")
        if to_delete[:10]:
            logger.info(f"  Sample deletes: {to_delete[:10]}")
        await client.close()
        return

    # ── Step 4: Delete duplicates ─────────────────────────────────────────
    if to_delete:
        # Delete in batches of 100
        for i in range(0, len(to_delete), 100):
            batch = to_delete[i : i + 100]
            await client.delete(
                collection_name=COLLECTION,
                points_selector=batch,
            )
            logger.info(f"  Deleted batch {i // 100 + 1}: {len(batch)} vectors")

    # ── Step 5: Re-ID winners to deterministic IDs ────────────────────────
    if to_re_id:
        for pt, new_id in to_re_id:
            new_point = PointStruct(
                id=new_id,
                vector=pt["vector"],
                payload=pt["payload"],
            )
            await client.upsert(
                collection_name=COLLECTION,
                points=[new_point],
            )
            # Delete old ID if different
            old_id = str(pt["id"])
            if old_id != new_id:
                await client.delete(
                    collection_name=COLLECTION,
                    points_selector=[old_id],
                )
        logger.info(f"  Re-IDed {re_id_count} vectors to deterministic IDs")

    # ── Final stats ───────────────────────────────────────────────────────
    info = await client.get_collection(COLLECTION)
    logger.info(f"Final vector count: {info.points_count}")

    await client.close()
    logger.info("Done.")


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    asyncio.run(main(dry_run=dry))
