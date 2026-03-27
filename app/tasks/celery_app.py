"""Celery app configuration with beat schedule."""
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
        "app.tasks.ingest_rss",
        "app.tasks.ingest_scraper",
        "app.tasks.alert_check",
        "app.tasks.calibrate",
        "app.tasks.cleanup",
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
    # RSS ingestion every 5 minutes
    "ingest-rss-every-5m": {
        "task": "app.tasks.ingest_rss.ingest_rss_task",
        "schedule": 300.0,  # 5 minutes
    },
    # Scraper every 30 minutes
    "ingest-scraper-every-30m": {
        "task": "app.tasks.ingest_scraper.ingest_scraper_task",
        "schedule": 1800.0,  # 30 minutes
    },
    # Alert check every minute
    "check-alerts-every-1m": {
        "task": "app.tasks.alert_check.check_alerts_task",
        "schedule": 60.0,  # 1 minute
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
}
