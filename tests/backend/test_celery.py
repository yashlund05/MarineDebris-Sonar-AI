"""Tests for Celery application configuration and task execution."""

from backend.celery_app import celery_app
from backend.tasks import health_ping


def test_celery_configuration():
    """Verify Celery app initialization and broker configuration."""
    assert celery_app.main == "marine_debris_sonar_worker"
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.accept_content == ["json"]


def test_health_ping_task_execution():
    """Verify that the Phase 0 health_ping task executes successfully."""
    result = health_ping.apply()
    assert result.successful()
    output = result.get()
    assert output["status"] == "healthy"
    assert "Celery worker is alive" in output["message"]
