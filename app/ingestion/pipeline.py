"""Shared ingestion pipeline — common processing for all signal sources.

Extracts the shared logic from ingest_rss and ingest_scraper into a single
reusable pipeline that handles: filtering, sanitization, dedup, tagging,
scoring, embedding, DB insert, and Qdrant upsert.

Every source type (RSS, social, regulatory, pricing) flows through this
pipeline with the same metadata enrichment guarantees.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from app.config import get_settings
from app.db.pool import get_pool
from app.ingestion.rss import RawSignal
from app.ingestion.filters import passes_keyword_filter
from app.ingestion.sanitizer import sanitize_content, contains_injection
from app.ingestion.dedup import content_hash, url_vector_id
from app.ingestion.chunker import chunk_text
from app.scoring.risk_scorer import compute_risk_score, assign_tier
from app.scoring.anomaly import compute_text_anomaly
from app.scoring.geo_criticality import detect_geo_zone, get_geo_criticality
from app.scoring.time_decay import compute_time_decay
from app.intelligence.signal_tagger import tag_signal
from app.vectordb.client import get_qdrant, upsert_vectors
from app.vectordb.embedder import embed_texts

logger = logging.getLogger(__name__)


async def ingest_signals(
    raw_signals: list[RawSignal],
    *,
    default_source_weight: float = 0.5,
    skip_keyword_filter: bool = False,
) -> dict:
    """Process a batch of raw signals through the full ingestion pipeline.

    Args:
        raw_signals: Pre-fetched signals (from RSS, Reddit, scraper, etc.)
        default_source_weight: Fallback weight if no calibrated weight in DB.
        skip_keyword_filter: If True, skip the keyword gate (e.g., social
            sources already passed impact filter).

    Returns:
        Stats dict: fetched, filtered, duplicated, injected, ingested, errors.
    """
    settings = get_settings()
    pool = await get_pool()
    qdrant = await get_qdrant()

    stats = {
        "fetched": len(raw_signals),
        "filtered": 0,
        "duplicated": 0,
        "injected": 0,
        "ingested": 0,
        "errors": 0,
    }

    for raw in raw_signals:
        try:
            # ── Keyword filter ───────────────────────────────────────────
            if not skip_keyword_filter and not passes_keyword_filter(raw.content):
                stats["filtered"] += 1
                continue

            # ── Injection check ──────────────────────────────────────────
            if contains_injection(raw.content):
                stats["injected"] += 1
                logger.warning(f"Injection detected in signal from {raw.source_key}")
                continue

            # ── Sanitize ─────────────────────────────────────────────────
            clean_content = sanitize_content(raw.content)
            clean_title = sanitize_content(raw.title) if raw.title else None

            # ── Hash dedup (content hash + URL dedup) ────────────────────
            hash_val = content_hash(clean_content)

            async with pool.connection() as conn:
                from app.db.queries import check_hash_exists, check_url_exists
                if await check_hash_exists(conn, hash_val):
                    stats["duplicated"] += 1
                    continue
                # URL-level dedup: same URL ⇒ skip even if content changed
                if raw.url and await check_url_exists(conn, raw.url):
                    stats["duplicated"] += 1
                    continue

            # ── Geo zone detection ───────────────────────────────────────
            full_text = f"{clean_title or ''} {clean_content}"
            geo_zone = detect_geo_zone(full_text)
            geo_crit = get_geo_criticality(geo_zone) if geo_zone else 0.3

            # ── Transport mode & region tagging ──────────────────────────
            # Use source registry modes as hint, but signal_tagger detects
            # from content for accuracy
            transport_mode, region = tag_signal(full_text)

            # If tagger returns None but source has a single mode, use it
            if transport_mode is None and raw.modes and len(raw.modes) == 1:
                transport_mode = raw.modes[0]

            # ── Scoring ──────────────────────────────────────────────────
            anomaly = compute_text_anomaly(clean_content)
            time_decay = compute_time_decay(0.0)  # Fresh signal
            source_weight = default_source_weight

            # Get adaptive source weight from DB
            async with pool.connection() as conn:
                from app.db.queries import get_source_weight
                sw = await get_source_weight(conn, raw.source_key)
                if sw:
                    source_weight = sw.current_weight

            risk_components = compute_risk_score(
                anomaly_score=anomaly,
                source_weight=source_weight,
                geo_criticality=geo_crit,
                time_decay_val=time_decay,
            )
            risk_score = risk_components.risk_score
            tier = assign_tier(risk_score, raw.source_key)

            # ── Embed ────────────────────────────────────────────────────
            chunks = chunk_text(clean_content)
            texts_to_embed = [c.text for c in chunks[:3]]
            embeddings = await embed_texts(texts_to_embed)

            # ── Insert into PostgreSQL ───────────────────────────────────
            async with pool.connection() as conn:
                from app.db.queries import insert_signal
                from app.db.models import SignalCreate
                signal_id = await insert_signal(
                    conn,
                    SignalCreate(
                        title=clean_title,
                        content=clean_content,
                        source=raw.source_key,
                        tier=tier,
                        source_type=raw.source_type,
                        url=raw.url,
                        geo_zone=geo_zone,
                        risk_score=risk_score,
                        anomaly_score=anomaly,
                        source_weight=source_weight,
                        geo_criticality=geo_crit,
                        time_decay=time_decay,
                        reliability_score=raw.reliability,
                        content_hash=hash_val,
                        transport_mode=transport_mode,
                        region=region,
                    ),
                )

            # ── Upsert into Qdrant (deterministic URL-based vector IDs) ────
            if signal_id and embeddings:
                from qdrant_client.models import PointStruct
                for i, embedding in enumerate(embeddings):
                    if all(v == 0 for v in embedding):
                        continue
                    # Deterministic ID: md5(url::chunk_index)
                    # Same URL always maps to the same vector → upsert = dedup
                    point_id = url_vector_id(raw.url, i) if raw.url else str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{signal_id}_{i}"))
                    payload = {
                        "signal_id": str(signal_id),
                        "source": raw.source_key,
                        "source_type": raw.source_type,
                        "geo_zone": geo_zone or "",
                        "risk_score": risk_score,
                        "tier": tier,
                        "transport_mode": transport_mode or "",
                        "region": region or "",
                        "reliability_score": raw.reliability,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "chunk_index": i,
                        "url": raw.url or "",
                    }
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload,
                    )
                    await upsert_vectors(
                        qdrant,
                        settings.qdrant_collection,
                        [point],
                    )

            stats["ingested"] += 1

        except Exception as exc:
            stats["errors"] += 1
            logger.error(f"Error ingesting signal from {raw.source_key}: {exc}")

    return stats
