"""Celery app configuration with tiered beat schedule.

Tier 1: Every 15 min — live physical data, terminal gates, pricing APIs
Tier 2: Every 1 hour — news RSS, chokepoint status, pricing feeds
Tier 3: Every 5 min  — social intelligence (impact-filtered Reddit/forums)
Tier 4: Daily         — regulatory, customs, embargoes
"""
from __future__ import annotations

from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "noble_intel",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.ingest_tier1",
        "app.tasks.ingest_rss",
        "app.tasks.ingest_scraper",
        "app.tasks.ingest_social",
        "app.tasks.ingest_regulatory",
        "app.tasks.alert_check",
        "app.tasks.calibrate",
        "app.tasks.cleanup",
        "app.tasks.event_pipeline",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_soft_time_limit=300,
    task_time_limit=600,
)

celery_app.conf.beat_schedule = {
    # ═══════════════════════════════════════════════════════════════════════
    #  TIER 1 — Live Physical Data, Pricing, GEOINT, Cyber (every 15 min)
    # ═══════════════════════════════════════════════════════════════════════
    "tier1-live-every-15m": {
        "task": "app.tasks.ingest_tier1.ingest_tier1_task",
        "schedule": 900.0,  # 15 minutes
    },

    # ═══════════════════════════════════════════════════════════════════════
    #  TIER 2 — News, Chokepoints, Pricing RSS (every 1 hour)
    # ═══════════════════════════════════════════════════════════════════════
    "tier2-rss-every-1h": {
        "task": "app.tasks.ingest_rss.ingest_rss_task",
        "schedule": 3600.0,  # 1 hour
    },

    # ═══════════════════════════════════════════════════════════════════════
    #  TIER 3 — Social Intelligence (every 5 min, impact-filtered)
    # ═══════════════════════════════════════════════════════════════════════
    "tier3-social-every-5m": {
        "task": "app.tasks.ingest_social.ingest_social_task",
        "schedule": 300.0,  # 5 minutes
    },

    # ═══════════════════════════════════════════════════════════════════════
    #  TIER 4 — Regulatory (daily at 06:00 UTC)
    # ═══════════════════════════════════════════════════════════════════════
    "tier4-regulatory-daily": {
        "task": "app.tasks.ingest_regulatory.ingest_regulatory_task",
        "schedule": crontab(hour=6, minute=0),
    },

    # ═══════════════════════════════════════════════════════════════════════
    #  SYSTEM TASKS (unchanged)
    # ═══════════════════════════════════════════════════════════════════════

    # Alert check every minute
    "check-alerts-every-1m": {
        "task": "app.tasks.alert_check.check_alerts_task",
        "schedule": 60.0,
    },
    # Source weight calibration — weekly Monday 03:00 UTC
    "calibrate-sources-weekly": {
        "task": "app.tasks.calibrate.calibrate_sources_task",
        "schedule": crontab(hour=3, minute=0, day_of_week="monday"),
    },
    # Formula weight calibration — monthly 1st at 04:00 UTC
    "calibrate-formula-monthly": {
        "task": "app.tasks.calibrate.calibrate_formula_task",
        "schedule": crontab(hour=4, minute=0, day_of_month="1"),
    },
    # Cascade edge calibration — weekly Sunday 03:00 UTC
    "calibrate-cascade-weekly": {
        "task": "app.tasks.calibrate.calibrate_cascade_task",
        "schedule": crontab(hour=3, minute=0, day_of_week="sunday"),
    },
    # Cleanup expired signals — daily at 02:00 UTC
    "cleanup-expired-daily": {
        "task": "app.tasks.cleanup.cleanup_expired_task",
        "schedule": crontab(hour=2, minute=0),
    },

    # ═══════════════════════════════════════════════════════════════════════
    #  DECISION ENGINE — Event Fusion Pipeline (every 15 min)
    # ═══════════════════════════════════════════════════════════════════════
    "event-pipeline-every-15m": {
        "task": "app.tasks.event_pipeline.run_event_pipeline_task",
        "schedule": 900.0,  # 15 minutes — aligned with Tier 1 ingestion
    },
}
