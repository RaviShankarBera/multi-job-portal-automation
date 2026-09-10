from celery import Celery
from celery.schedules import crontab

# Create Celery application
celery_app = Celery(
    "jobportal",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2",
)

# Celery configuration
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result settings
    result_expires=3600,  # 1 hour
    result_persistent=True,
    
    # Retry settings
    task_default_retry_delay=60,
    task_max_retries=3,
    
    # Worker settings
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Execute scheduled searches every 15 minutes
    "execute-scheduled-searches": {
        "task": "app.tasks.scheduled_searches.execute_due_searches",
        "schedule": crontab(minute="*/15"),
    },
    
    # Create daily analytics snapshots at midnight
    "create-daily-snapshots": {
        "task": "app.tasks.analytics.create_daily_snapshots",
        "schedule": crontab(hour=0, minute=0),
    },
    
    # Check follow-up reminders at 8 AM
    "check-follow-ups": {
        "task": "app.tasks.notifications.check_follow_ups",
        "schedule": crontab(hour=8, minute=0),
    },
    
    # Clean up old notifications weekly (Sunday at midnight)
    "cleanup-old-notifications": {
        "task": "app.tasks.notifications.cleanup_old_notifications",
        "schedule": crontab(hour=0, minute=0, day_of_week=0),
    },
    
    # Update user job scores daily at 2 AM
    "update-job-scores": {
        "task": "app.tasks.analytics.update_job_scores",
        "schedule": crontab(hour=2, minute=0),
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
