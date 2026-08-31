"""Celery application factory and configuration."""

from celery import Celery
from backend.config import get_settings

settings = get_settings()

celery_app = Celery(
    "marine_debris_sonar_worker",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
    include=["backend.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_always_eager=settings.CELERY_TASK_ALWAYS_EAGER,
    result_expires=86400,  # 24 hours
)
