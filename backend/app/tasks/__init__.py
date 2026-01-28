from celery import Celery
from app.config import settings

celery_app = Celery(
    "webspy",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.crawl_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "monitor-competitors-hourly": {
        "task": "app.tasks.crawl_tasks.monitor_all_competitors",
        "schedule": 3600.0,  # Every hour
    },
    "cleanup-old-scans-daily": {
        "task": "app.tasks.crawl_tasks.cleanup_old_scans",
        "schedule": 86400.0,  # Every day
    },
}
