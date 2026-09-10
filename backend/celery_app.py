from app.core.config import settings

# Only configure Celery if Redis is available
if settings.REDIS_URL:
    from celery import Celery
    from celery.schedules import crontab

    celery_app = Celery(
        "jobportal",
        broker=settings.REDIS_URL,
        backend=settings.REDIS_URL,
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_time_limit=300,
        task_soft_time_limit=240,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        result_expires=3600,
        task_default_retry_delay=60,
        task_max_retries=3,
    )

    celery_app.conf.beat_schedule = {
        "execute-scheduled-searches": {
            "task": "app.tasks.scheduled_searches.execute_due_searches",
            "schedule": crontab(minute="*/15"),
        },
        "create-daily-snapshots": {
            "task": "app.tasks.analytics.create_daily_snapshots",
            "schedule": crontab(hour=0, minute=0),
        },
        "check-follow-ups": {
            "task": "app.tasks.notifications.check_follow_ups",
            "schedule": crontab(hour=8, minute=0),
        },
    }

    celery_app.autodiscover_tasks(["app.tasks"])
else:
    celery_app = None
    print("WARNING: Redis not configured. Celery tasks disabled. Set REDIS_URL in .env to enable.")
