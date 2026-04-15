"""Celery configuration for background tasks."""
import os
from celery import Celery

# Get Redis URL from environment or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery application
celery_app = Celery(
    "trustbond",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.core.tasks.report_processor",
    ],
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_concurrency=2,
    beat_schedule={
        "process-pending-reports-every-5-minutes": {
            "task": "app.core.tasks.report_processor.process_pending_reports",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)