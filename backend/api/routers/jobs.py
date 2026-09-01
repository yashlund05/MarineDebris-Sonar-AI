import uuid
from typing import Any
from fastapi import APIRouter, Depends, Path, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from backend.api.dependencies import get_db
from backend.database.models import ProcessingJob
from backend.exceptions import JobNotFoundError

router = APIRouter(tags=["Jobs"])

@router.get("/jobs/{job_id}")
async def get_job(
    job_id: uuid.UUID = Path(..., description="The ID of the processing job"),
    request: Request = None,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get the status and details of a processing job."""
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if not job:
        raise JobNotFoundError(job_id)

    job_data = {
        "id": str(job.id),
        "survey_id": str(job.survey_id),
        "celery_task_id": job.celery_task_id,
        "status": job.status,
        "progress_pct": job.progress_pct,
        "current_stage": job.current_stage,
        "preprocessing_version": job.preprocessing_version,
        "detection_model": job.detection_model,
        "detection_model_version": job.detection_model_version,
        "segmentation_model": job.segmentation_model,
        "detection_conf_threshold": job.detection_conf_threshold,
        "nms_iou_threshold": job.nms_iou_threshold,
        "tile_size": job.tile_size,
        "tile_overlap": job.tile_overlap,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }

    request_id = getattr(request.state, "request_id", "") if request and hasattr(request, "state") else ""

    return {
        "success": True,
        "data": job_data,
        "meta": {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
