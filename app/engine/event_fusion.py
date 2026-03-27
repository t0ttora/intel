"""Event Fusion Engine — cluster related signals into decision-grade events.

Algorithm:
1. Group signals by compatible time window (±12h T1, ±24h T2+)
2. Within each window, compute pairwise cosine similarity via Qdrant vectors
3. Merge if cosine > 0.78 AND same/compatible region
4. Produce EventCluster with union of transport modes
"""
from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from uuid import UUID

from qdrant_client import AsyncQdrantClient

from app.config import Settings
from app.db.event_models import Event, EventCluster, EventStatus, classify_priority
from app.db.models import Signal

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────

COSINE_THRESHOLD = 0.78
TIME_WINDOW_T1_HOURS = 12
TIME_WINDOW_DEFAULT_HOURS = 24
MIN_CLUSTER_SIZE = 2
MAX_CLUSTER_SIZE = 50
OVERLAP_DEDUP_THRESHOLD = 0.80  # 80%+ signal overlap = same event

# Regions that are "compatible" (geographically linked trade lanes)
_COMPATIBLE_REGIONS: dict[str, set[str]] = {
    "red_sea": {"suez", "mediterranean", "middle_east", "east_africa"},
    "suez": {"red_sea", "mediterranean", "middle_east"},
    "mediterranean": {"red_sea", "suez", "europe_north", "europe_south"},
    "southeast_asia": {"east_asia", "south_asia", "oceania"},
    "east_asia": {"southeast_asia", "transpacific", "north_asia"},
    "north_america_west": {"transpacific", "east_asia"},
    "north_america_east": {"transatlantic", "europe_north", "caribbean"},
    "europe_north": {"mediterranean", "transatlantic", "north_america_east"},
}


def _regions_compatible(r1: str | None, r2: str | None) -> bool:
    """Check if two regions are the same or geographically linked."""
    if not r1 or not r2:
        return True  # unknown region → always compatible
    if r1 == r2:
        return True
    return r2 in _COMPATIBLE_REGIONS.get(r1, set()) or r1 in _COMPATIBLE_REGIONS.get(r2, set())


def _time_window_hours(tier: str) -> int:
    """Return the clustering time window for a tier."""
    return TIME_WINDOW_T1_HOURS if tier in ("P0", "P1", "tier1") else TIME_WINDOW_DEFAULT_HOURS


def _cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ── Vector Retrieval ──────────────────────────────────────────────────────


async def _retrieve_vectors(
    qdrant: AsyncQdrantClient,
    collection: str,
    embedding_ids: list[str],
) -> dict[str, list[float]]:
    """Retrieve stored vectors from Qdrant by point IDs."""
    if not embedding_ids:
        return {}
    try:
        points = await qdrant.retrieve(
            collection_name=collection,
            ids=embedding_ids,
            with_vectors=True,
            with_payload=False,
        )
        return {
            str(p.id): list(p.vector)  # type: ignore[arg-type]
            for p in points
            if p.vector is not None
        }
    except Exception as exc:
        logger.warning(f"Failed to retrieve vectors: {exc}")
        return {}


# ── Clustering ────────────────────────────────────────────────────────────


async def cluster_signals(
    signals: list[Signal],
    qdrant: AsyncQdrantClient,
    settings: Settings,
) -> list[EventCluster]:
    """Cluster signals into related groups using semantic similarity + time + region.

    Uses Union-Find for efficient merging.
    """
    if len(signals) < MIN_CLUSTER_SIZE:
        return []

    # Retrieve vectors for similarity computation
    embedding_ids = [s.embedding_id for s in signals if s.embedding_id]
    vectors = await _retrieve_vectors(qdrant, settings.qdrant_collection, embedding_ids)

    # Build lookup: signal index → vector
    sig_vectors: dict[int, list[float]] = {}
    for i, s in enumerate(signals):
        if s.embedding_id and s.embedding_id in vectors:
            sig_vectors[i] = vectors[s.embedding_id]

    # Union-Find
    parent = list(range(len(signals)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Pairwise comparison (only between signals with vectors)
    indexed = list(sig_vectors.keys())
    for ii in range(len(indexed)):
        i = indexed[ii]
        si = signals[i]
        vi = sig_vectors[i]
        window_h = _time_window_hours(si.tier)

        for jj in range(ii + 1, len(indexed)):
            j = indexed[jj]
            sj = signals[j]

            # Time window check
            if si.created_at and sj.created_at:
                delta = abs((si.created_at - sj.created_at).total_seconds()) / 3600
                if delta > max(window_h, _time_window_hours(sj.tier)):
                    continue

            # Region compatibility
            if not _regions_compatible(si.region, sj.region):
                continue

            # Cosine similarity
            sim = _cosine_similarity(vi, sig_vectors[j])
            if sim >= COSINE_THRESHOLD:
                union(i, j)

    # Group by cluster root
    clusters_map: dict[int, list[int]] = {}
    for i in range(len(signals)):
        root = find(i)
        clusters_map.setdefault(root, []).append(i)

    # Build EventCluster objects (only clusters with >= MIN_CLUSTER_SIZE)
    clusters: list[EventCluster] = []
    for indices in clusters_map.values():
        if len(indices) < MIN_CLUSTER_SIZE:
            continue
        if len(indices) > MAX_CLUSTER_SIZE:
            indices = sorted(indices, key=lambda i: signals[i].risk_score or 0, reverse=True)[
                :MAX_CLUSTER_SIZE
            ]

        sigs = [signals[i] for i in indices]
        risk_scores = [s.risk_score or 0 for s in sigs]
        modes: set[str] = set()
        regions: set[str] = set()
        sources: set[str] = set()
        titles: list[str] = []

        for s in sigs:
            if s.transport_mode:
                modes.add(s.transport_mode)
            if s.region:
                regions.add(s.region)
            sources.add(s.source)
            if s.title:
                titles.append(s.title)

        timestamps = [s.created_at for s in sigs if s.created_at]

        clusters.append(
            EventCluster(
                signal_ids=[s.id for s in sigs],
                titles=titles,
                sources=list(sources),
                transport_modes=sorted(modes),
                regions=sorted(regions),
                avg_risk_score=sum(risk_scores) / len(risk_scores),
                max_risk_score=max(risk_scores),
                earliest=min(timestamps) if timestamps else datetime.now(timezone.utc),
                latest=max(timestamps) if timestamps else datetime.now(timezone.utc),
            )
        )

    logger.info(
        f"Clustered {len(signals)} signals into {len(clusters)} event clusters"
    )
    return clusters


# ── Event Construction ────────────────────────────────────────────────────


def merge_into_event(cluster: EventCluster) -> Event:
    """Convert an EventCluster into an Event (pre-scoring, pre-decisions).

    Confidence: base 0.5, +0.1 per independent source (cap 0.95).
    """
    # Title: highest-ranked signal title
    title = cluster.titles[0] if cluster.titles else "Unnamed event"

    # Summary: top 3 distinct titles
    unique_titles = list(dict.fromkeys(cluster.titles))[:3]
    summary = " | ".join(unique_titles)

    # Confidence: base 0.5, +0.1 per independent source, cap 0.95
    source_count = len(set(cluster.sources))
    confidence = min(0.95, 0.5 + (source_count - 1) * 0.10)

    return Event(
        title=title,
        summary=summary,
        impact_score=0.0,  # set by impact scorer
        priority=classify_priority(0),
        transport_modes=cluster.transport_modes,
        regions=cluster.regions,
        confidence=round(confidence, 2),
        signal_ids=cluster.signal_ids,
        signal_count=len(cluster.signal_ids),
        source_diversity=source_count,
        status=EventStatus.ACTIVE,
        start_time=cluster.earliest,
    )


# ── Deduplication ─────────────────────────────────────────────────────────


def deduplicate_events(
    new_events: list[Event], existing_events: list[Event]
) -> tuple[list[Event], list[tuple[Event, Event]]]:
    """Separate new events into truly-new and updates to existing events.

    Returns (new, updates) where updates is [(new_event, matched_existing)].
    An event is considered a duplicate if >80% of its signal IDs overlap
    with an existing active event.
    """
    truly_new: list[Event] = []
    updates: list[tuple[Event, Event]] = []

    for new_ev in new_events:
        new_sids = set(new_ev.signal_ids)
        matched = False

        for existing in existing_events:
            existing_sids = set(existing.signal_ids)
            if not new_sids or not existing_sids:
                continue
            overlap = len(new_sids & existing_sids) / len(new_sids | existing_sids)
            if overlap >= OVERLAP_DEDUP_THRESHOLD:
                updates.append((new_ev, existing))
                matched = True
                break

        if not matched:
            truly_new.append(new_ev)

    logger.info(
        f"Dedup: {len(truly_new)} new events, {len(updates)} updates to existing"
    )
    return truly_new, updates
