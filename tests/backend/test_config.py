"""Tests for application configuration loading and URL building."""

from backend.config import Settings


def test_default_settings():
    """Verify default configuration values."""
    settings = Settings(DATABASE_URL="", REDIS_URL="", CELERY_BROKER_URL="", CELERY_RESULT_BACKEND="")
    assert settings.PROJECT_NAME == "MarineDebris-Sonar-AI"
    assert settings.API_V1_STR == "/api/v1"
    assert settings.MAX_UPLOAD_SIZE_MB == 2048
    assert settings.DETECTION_CONF_THRESHOLD == 0.35
    assert settings.NMS_IOU_THRESHOLD == 0.45
    assert settings.TILE_SIZE == 640
    assert settings.TILE_OVERLAP == 0.2
    assert settings.DEFAULT_DETECTION_MODEL == "production_fls_yolov8n"


def test_database_url_generation():
    """Verify generated database URLs for async and sync engines."""
    settings = Settings(
        DATABASE_URL="",
        POSTGRES_USER="testuser",
        POSTGRES_PASSWORD="testpassword",
        POSTGRES_HOST="dbhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="testdb",
    )
    assert settings.async_database_url == "postgresql+asyncpg://testuser:testpassword@dbhost:5432/testdb"
    assert settings.sync_database_url == "postgresql+psycopg2://testuser:testpassword@dbhost:5432/testdb"


def test_redis_url_generation():
    """Verify generated Redis and Celery broker URLs."""
    settings = Settings(
        REDIS_URL="",
        REDIS_HOST="redishost",
        REDIS_PORT=6379,
        REDIS_DB=1,
    )
    assert settings.redis_connection_url == "redis://redishost:6379/1"
    assert settings.celery_broker == "redis://redishost:6379/1"
