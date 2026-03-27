"""Celery tasks: Calibration (source weights weekly, formula monthly, cascade weekly)."""
from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.db.pool import get_pool
from app.calibration.source_weights import calibrate_all_sources
from app.calibration.formula_weights import recalibrate_formula
from app.calibration.cascade_edges import calibrate_cascade_edges
from app.calibration.drift_detector import detect_drifts

logger = logging.getLogger(__name__)


# ── Source Weight Calibration (Weekly) ────────────────────────────────────


async def _calibrate_sources() -> dict:
    pool = await get_pool()
    async with pool.connection() as conn:
        results = await calibrate_all_sources(conn)
        drifts = await detect_drifts(conn)

    drift_alerts = [
        {"source": d.source_key, "delta": round(d.delta, 4), "severity": d.severity}
        for d in drifts
    ]

    return {
        "sources_calibrated": len(results),
        "results": results,
        "drift_alerts": drift_alerts,
    }


@celery_app.task(name="app.tasks.calibrate.calibrate_sources_task", bind=True, max_retries=2)
def calibrate_sources_task(self) -> dict:
    """Weekly source weight calibration."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_calibrate_sources())
        logger.info(f"Source calibration complete: {result['sources_calibrated']} sources")
        return result
    except Exception as exc:
        logger.error(f"Source calibration failed: {exc}")
        self.retry(exc=exc, countdown=300)
    finally:
        loop.close()


# ── Formula Weight Calibration (Monthly) ──────────────────────────────────


async def _calibrate_formula() -> dict:
    pool = await get_pool()
    async with pool.connection() as conn:
        result = await recalibrate_formula(conn)
    return result


@celery_app.task(name="app.tasks.calibrate.calibrate_formula_task", bind=True, max_retries=2)
def calibrate_formula_task(self) -> dict:
    """Monthly formula weight recalibration using Pearson correlation."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_calibrate_formula())
        logger.info(f"Formula calibration complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"Formula calibration failed: {exc}")
        self.retry(exc=exc, countdown=300)
    finally:
        loop.close()


# ── Cascade Edge Calibration (Weekly) ─────────────────────────────────────


async def _calibrate_cascade() -> dict:
    pool = await get_pool()
    async with pool.connection() as conn:
        result = await calibrate_cascade_edges(conn)
    return result


@celery_app.task(name="app.tasks.calibrate.calibrate_cascade_task", bind=True, max_retries=2)
def calibrate_cascade_task(self) -> dict:
    """Weekly cascade edge weight calibration."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_calibrate_cascade())
        logger.info(f"Cascade calibration complete: {result}")
        return result
    except Exception as exc:
        logger.error(f"Cascade calibration failed: {exc}")
        self.retry(exc=exc, countdown=300)
    finally:
        loop.close()
