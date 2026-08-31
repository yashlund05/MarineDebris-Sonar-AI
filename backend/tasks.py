"""Celery task definitions for background processing."""

import logging
from typing import Any, Dict
from backend.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="backend.tasks.health_ping")
def health_ping(self) -> Dict[str, Any]:
    """Trivial Celery health/ping task for Phase 0 validation."""
    logger.info("Executing Celery health_ping task id=%s", self.request.id)
    return {
        "status": "healthy",
        "task_id": self.request.id,
        "message": "Celery worker is alive and executing tasks.",
    }
