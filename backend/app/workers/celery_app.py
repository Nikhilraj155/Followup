from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "followup_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Celery Beat schedule for periodic tasks
    beat_schedule={
        "check-all-active-replies-every-30-mins": {
            "task": "app.workers.tasks.check_all_active_applications_reply_task",
            "schedule": 1800.0,  # every 30 mins
        },
    }
)
