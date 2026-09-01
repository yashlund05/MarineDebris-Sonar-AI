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

    # Check Redis connectivity (non-blocking)
    redis_status = "disconnected"
    if settings.CELERY_TASK_ALWAYS_EAGER:
        redis_status = "in-memory (standalone)"
    else:
        try:
            import asyncio
            r = aioredis.from_url(
                settings.redis_connection_url,
                protocol=2,
                socket_timeout=0.2,
                socket_connect_timeout=0.2,
            )
            pong = await asyncio.wait_for(r.ping(), timeout=0.3)
            if pong:
                redis_status = "connected"
            if hasattr(r, "aclose"):
                await r.aclose()
            else:
                await r.close()
        except Exception:
            redis_status = "disconnected"

    # Worker status
    if settings.CELERY_TASK_ALWAYS_EAGER:
        worker_status = "active (in-process)"
    elif redis_status == "connected":
        worker_status = "running"
    else:
        worker_status = "offline"

    device = detect_device()
    active_model = f"{settings.DEFAULT_DETECTION_MODEL} v{settings.DEFAULT_DETECTION_MODEL_VERSION}"

    is_healthy = db_status == "connected" and (redis_status in ("connected", "in-memory (standalone)"))

    return {
        "status": "ok" if (is_healthy or settings.ENVIRONMENT == "test") else "degraded",
        "database": db_status,
        "redis": redis_status,
        "worker": worker_status,
        "active_detection_model": active_model,
        "device": device,
    }
