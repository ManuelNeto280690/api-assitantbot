"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab
from app.config import settings

# Create Celery app
celery_app = Celery(
    "saas_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Task routing
celery_app.conf.task_routes = {
    "app.workers.campaign_scheduler.*": {"queue": "scheduler"},
    "app.workers.smart_dispatcher.*": {"queue": "dispatcher"},
    "app.workers.automation_engine.*": {"queue": "automation"},
}

# Periodic tasks (Celery Beat schedule)
celery_app.conf.beat_schedule = {
    "campaign-scheduler-every-minute": {
        "task": "app.workers.campaign_scheduler.process_pending_targets",
        "schedule": 60.0,  # Every 60 seconds
    },
    "automation-scheduler-every-minute": {
        "task": "app.workers.automation_engine.process_scheduled_automations",
        "schedule": 60.0,
    },
}

# Auto-discover tasks
celery_app.autodiscover_tasks([
    "app.workers",
])
