"""Celery task: RSS feed ingestion (runs every 5 minutes)."""
from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app
from app.config import get_settings
from app.db.pool import get_pool
from app.ingestion.rss import fetch_all_feeds, RawSignal
from app.ingestion.filters import passes_keyword_filter
from app.ingestion.sanitizer import sanitize_content, contains_injection
from app.ingestion.dedup import content_hash, is_duplicate
from app.ingestion.chunker import chunk_text
from app.scoring.risk_scorer import compute_risk_score, classify_risk_level, assign_tier
from app.scoring.anomaly import compute_text_anomaly
from app.scoring.geo_criticality import detect_geo_zone, get_geo_criticality
from app.scoring.time_decay import compute_time_decay
from app.vectordb.client import get_qdrant, upsert_vectors
from app.vectordb.embedder import embed_texts

logger = logging.getLogger(__name__)


async def _ingest_rss() -> dict:
    """Async RSS ingestion pipeline."""
    settings = get_settings()
    pool = await get_pool()
    qdrant = await get_qdrant()

    stats = {"fetched": 0, "filtered": 0, "duplicated": 0, "injected": 0, "ingested": 0, "errors": 0}

    try:
        raw_signals = await fetch_all_feeds()
        stats["fetched"] = len(raw_signals)
    except Exception as exc:
        logger.error(f"RSS fetch failed: {exc}")
        return {"error": str(exc), **stats}

    for raw in raw_signals:
        try:
            # Keyword filter
            if not passes_keyword_filter(raw.content):
                stats["filtered"] += 1
                continue

            # Injection check
            if contains_injection(raw.content):
                stats["injected"] += 1
                logger.warning(f"Injection detected in RSS signal from {raw.source_key}")
                continue

            # Sanitize
            clean_content = sanitize_content(raw.content)
            clean_title = sanitize_content(raw.title) if raw.title else None

            # Hash dedup
            hash_val = content_hash(clean_content)

            async with pool.connection() as conn:
                from app.db.queries import check_hash_exists
                if await check_hash_exists(conn, hash_val):
                    stats["duplicated"] += 1
                    continue

            # Geo zone detection
            full_text = f"{clean_title or ''} {clean_content}"
            geo_zone = detect_geo_zone(full_text)
            geo_crit = get_geo_criticality(geo_zone) if geo_zone else 0.3

            # Scoring
            anomaly = compute_text_anomaly(clean_content)
            time_decay = compute_time_decay(0.0)  # Fresh signal
            source_weight = 0.5  # Default for RSS

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

            # Embed
            chunks = chunk_text(clean_content)
            texts_to_embed = [c.text for c in chunks[:3]]
            embeddings = await embed_texts(texts_to_embed)

            # Insert into PostgreSQL
            async with pool.connection() as conn:
                from app.db.queries import insert_signal
                from app.db.models import SignalCreate
                signal_id = await insert_signal(
                    conn,
                    SignalCreate(
                        title=clean_title,
                        content=clean_content,
                        source=raw.source_key,
                        url=raw.url,
                        geo_zone=geo_zone,
                        risk_score=risk_score,
                        anomaly_score=anomaly,
                        source_weight=source_weight,
                        geo_criticality=geo_crit,
                        time_decay=time_decay,
                        tier=tier,
                        content_hash=hash_val,
                    ),
                )

            # Upsert into Qdrant
            if signal_id and embeddings:
                from qdrant_client.models import PointStruct
                for i, embedding in enumerate(embeddings):
                    if all(v == 0 for v in embedding):
                        continue
                    point_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{signal_id}_{i}"))
                    payload = {
                        "signal_id": str(signal_id),
                        "source": raw.source_key,
                        "geo_zone": geo_zone or "",
                        "risk_score": risk_score,
                        "tier": tier,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "chunk_index": i,
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
            logger.error(f"Error ingesting RSS signal: {exc}")

    logger.info(f"RSS ingestion complete: {stats}")
    return stats


@celery_app.task(name="app.tasks.ingest_rss.ingest_rss_task", bind=True, max_retries=3)
def ingest_rss_task(self) -> dict:
    """Celery task wrapper for RSS ingestion."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_ingest_rss())
        return result
    except Exception as exc:
        logger.error(f"RSS ingest task failed: {exc}")
        self.retry(exc=exc, countdown=60)
    finally:
        loop.close()
