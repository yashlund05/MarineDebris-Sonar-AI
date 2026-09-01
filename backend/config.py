"""Application configuration settings module using Pydantic Settings."""

from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Core application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Project metadata
    PROJECT_NAME: str = "MarineDebris-Sonar-AI"
    PROJECT_DESCRIPTION: str = (
        "AI-Powered Automated Underwater Marine Debris and Anomaly Detection "
        "System using Side-Scan Sonar Imagery (SIH 2026 — PS26057)"
    )
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production"
    LOG_LEVEL: str = "INFO"

    # CORS — ARCHITECTURAL_BLUEPRINT.md §10
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://localhost:2671",
        "http://localhost:5039",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:2671",
        "http://127.0.0.1:5039",
    ]
    API_CORS_ORIGINS: str = "http://localhost:2671"

    # File uploads & Storage — ARCHITECTURAL_BLUEPRINT.md §10
    MAX_UPLOAD_SIZE_MB: int = 2048
    STORAGE_TYPE: str = "local"  # "local" or "minio"
    STORAGE_BACKEND: str = "local"  # alias for STORAGE_TYPE
    STORAGE_LOCAL_ROOT: str = "./data/storage"
    STORAGE_ROOT: str = "./data/storage"

    # MinIO / S3-compatible storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET: str = "marine-debris"
    MINIO_SECURE: bool = False

    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "marine_debris_sonar"
    DATABASE_URL: str = ""
    AUTO_CREATE_TABLES: bool = False

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    REDIS_URL: str = ""

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""
    CELERY_TASK_ALWAYS_EAGER: bool = False

    # Detection & Preprocessing defaults — ARCHITECTURAL_BLUEPRINT.md §10
    DETECTION_CONF_THRESHOLD: float = 0.35
    NMS_IOU_THRESHOLD: float = 0.45
    TILE_SIZE: int = 640
    TILE_OVERLAP: float = 0.2
    CALIBRATION_TEMPERATURE: float = 1.4

    # Processing — ARCHITECTURAL_BLUEPRINT.md §5, §10
    CHUNK_SIZE_PINGS: int = 2000
    DEVICE: str = "cuda"  # "cuda" or "cpu"

    # Model paths — ARCHITECTURAL_BLUEPRINT.md §9, §10
    DETECTION_MODEL_PATH: str = "models/detection/sonar_yolov8m_ghostpot_v1.pt"
    SEGMENTATION_MODEL_PATH: str = "models/segmentation/unet_shipwreck_v1.pt"
    DEFAULT_DETECTION_MODEL: str = "sonar_yolov8m_ghostpot_v1"
    DEFAULT_DETECTION_MODEL_VERSION: str = "1.0.0"

    # Preprocessing version tag
    PREPROCESSING_VERSION: str = "v1.0"

    @property
    def async_database_url(self) -> str:
        """Return async database connection URL for SQLAlchemy asyncpg."""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            return self.DATABASE_URL
        password = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def sync_database_url(self) -> str:
        """Return sync database connection URL for Alembic migrations and synchronous scripts."""
        if self.DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql+asyncpg://"):
                return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            if self.DATABASE_URL.startswith("sqlite+aiosqlite://"):
                return self.DATABASE_URL.replace("sqlite+aiosqlite://", "sqlite://", 1)
            return self.DATABASE_URL
        password = f":{self.POSTGRES_PASSWORD}" if self.POSTGRES_PASSWORD else ""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def redis_connection_url(self) -> str:
        """Return Redis connection URL."""
        if self.REDIS_URL:
            return self.REDIS_URL
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def celery_broker(self) -> str:
        """Return Celery broker URL."""
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return self.redis_connection_url

    @property
    def celery_backend(self) -> str:
        """Return Celery result backend URL."""
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return self.redis_connection_url

    @property
    def storage_root_path(self) -> str:
        """Return resolved storage root path."""
        return self.STORAGE_LOCAL_ROOT or self.STORAGE_ROOT

    @property
    def max_upload_size_bytes(self) -> int:
        """Return max upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
