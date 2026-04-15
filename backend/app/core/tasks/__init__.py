"""Celery tasks for background processing."""
from app.core.celery_config import celery_app
from app.core.tasks.report_processor import process_pending_reports

# Create Celery task with the app
celery_app.task(
    "process_pending_reports",
    bind=True,
)(process_pending_reports)