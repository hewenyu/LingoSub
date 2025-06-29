from celery import Celery
from app.core.config import settings

# Create a Celery instance
celery_app = Celery(
    "worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.worker.tasks"],  # List of modules to import when the worker starts
)

# Optional configuration
celery_app.conf.update(
    task_track_started=True,
) 