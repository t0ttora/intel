"""Verify Celery task imports and beat schedule."""
from app.tasks.celery_app import celery_app

print("Celery Beat Schedule:")
for name, config in celery_app.conf.beat_schedule.items():
    task = config["task"]
    schedule = config["schedule"]
    print(f"  {name}: {task} @ {schedule}")

print(f"\nTotal scheduled tasks: {len(celery_app.conf.beat_schedule)}")

print("\nIncluded task modules:")
for mod in celery_app.conf.get("include", []):
    print(f"  {mod}")
