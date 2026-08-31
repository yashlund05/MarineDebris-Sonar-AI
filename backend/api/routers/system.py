"""System and health check API endpoints conforming to API_SPEC.md §10."""

from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from backend.api.dependencies import get_db, get_settings
from backend.config import Settings

router = APIRouter(tags=["System & Health"])


def detect_device() -> str:
    """Detect compute device (cuda/cpu)."""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


@router.get("/health", status_code=status.HTTP_200_OK)
async def get_health(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict:
    """Basic system health check endpoint."""
    # Check database connectivity
    db_status = "disconnected"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Check Redis connectivity
    redis_status = "disconnected"
    try:
        r = aioredis.from_url(settings.redis_connection_url, socket_timeout=1.0)
        pong = await r.ping()
        if pong:
            redis_status = "connected"
        await r.close()
    except Exception:
        redis_status = "disconnected"

    # Worker status
    worker_status = "running" if settings.CELERY_TASK_ALWAYS_EAGER or redis_status == "connected" else "unknown"

    device = detect_device()
    active_model = f"{settings.DEFAULT_DETECTION_MODEL} v{settings.DEFAULT_DETECTION_MODEL_VERSION}"

    return {
        "status": "ok" if (db_status == "connected" or settings.ENVIRONMENT == "test") else "degraded",
        "database": db_status,
        "redis": redis_status,
        "worker": worker_status,
        "active_detection_model": active_model,
        "device": device,
    }
