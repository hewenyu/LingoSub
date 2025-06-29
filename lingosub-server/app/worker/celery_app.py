from celery import Celery
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create a Celery instance
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],  # List of modules to import when the worker starts
)

logger.info("Celery app initialized.")

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
)
logger.info("Celery app configuration updated.")