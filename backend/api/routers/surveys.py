import io
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.dependencies import get_db, get_settings
from backend.config import Settings
from backend.database.models import Detection, ProcessingJob, Report, SonarMetadata, Survey
from backend.exceptions import (
    AppException,
    FileTooLargeError,
    SurveyNotFoundError,
    UnsupportedFileTypeError,
    ValidationError,
)
from backend.storage.storage import get_storage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Surveys"], prefix="/surveys")

# --- Pydantic Models ---

class ReprocessRequest(BaseModel):
    detection_conf_threshold: float = 0.35
    nms_iou_threshold: float = 0.45
    run_segmentation: bool = True

class SurveyResponse(BaseModel):
    survey_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    status: str
    source_filename: str
    file_size_bytes: int
    created_at: datetime

# --- Routes ---

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_survey(
    request: Request,
    file: UploadFile = File(...),
    nav_csv: Optional[UploadFile] = File(None),
    channel: str = Form("starboard"),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Upload a new survey file and start processing."""
    filename = file.filename or "unknown.xtf"
    ext = os.path.splitext(filename)[1].lower()

    ext_map = {
        ".xtf": "xtf",
        ".jsf": "jsf",
        ".png": "png",
        ".tif": "tiff",
        ".tiff": "tiff",
    }

    if ext not in ext_map:
        raise UnsupportedFileTypeError(message=f"File extension '{ext}' is not supported. Supported: .xtf, .jsf, .png, .tif, .tiff")

    file_type = ext_map[ext]

    # Read file contents and check size
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if file_size > settings.max_upload_size_bytes:
        raise FileTooLargeError(message=f"File size ({file_size} bytes) exceeds limit of {settings.MAX_UPLOAD_SIZE_MB} MB.")

    survey_uuid = uuid.uuid4()
    storage = get_storage()

    # Save survey file
    saved_filename = f"{survey_uuid}{ext}"
    storage_path = storage.save_file(
        io.BytesIO(file_bytes),
        relative_path=f"surveys/{survey_uuid}",
        filename=saved_filename,
    )

    # Save nav file if supplied
    nav_storage_path = None
    if nav_csv is not None:
        nav_bytes = await nav_csv.read()
        if len(nav_bytes) > 0:
            nav_storage_path = storage.save_file(
                io.BytesIO(nav_bytes),
                relative_path=f"surveys/{survey_uuid}",
                filename="navigation.csv",
            )

    # Create Survey record
    survey = Survey(
        id=survey_uuid,
        source_filename=filename,
        storage_path=storage_path,
        file_type=file_type,
        file_size_bytes=file_size,
        status="uploaded",
        channel=channel,
    )
    db.add(survey)
    await db.flush()

    # Create Initial ProcessingJob record
    job_uuid = uuid.uuid4()
    job = ProcessingJob(
        id=job_uuid,
        survey_id=survey.id,
        status="pending",
        progress_pct=0,
        current_stage="queued",
        detection_conf_threshold=settings.DETECTION_CONF_THRESHOLD,
        nms_iou_threshold=settings.NMS_IOU_THRESHOLD,
        tile_size=settings.TILE_SIZE,
        tile_overlap=settings.TILE_OVERLAP,
    )
    db.add(job)
    await db.commit()
    await db.refresh(survey)
    await db.refresh(job)

    # Enqueue Celery task
    try:
        from backend.tasks import process_survey
        task = process_survey.delay(str(survey.id), str(job.id))
        job.celery_task_id = str(task.id)
        job.status = "running"
        survey.status = "queued"
        await db.commit()
    except Exception as e:
        logger.warning("Could not enqueue Celery task: %s", str(e))

    return {
        "success": True,
        "data": {
            "survey_id": survey.id,
            "job_id": job.id,
            "status": survey.status,
            "source_filename": survey.source_filename,
            "file_size_bytes": survey.file_size_bytes,
            "created_at": survey.created_at,
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("")
async def list_surveys(
    request: Request,
    status: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List surveys with detection counts."""
    query = select(Survey).order_by(desc(Survey.created_at)).limit(limit).offset(offset)
    if status:
        query = query.where(Survey.status == status)

    result = await db.execute(query)
    surveys = result.scalars().all()

    data = []
    for s in surveys:
        count_query = select(func.count(Detection.id)).where(Detection.survey_id == s.id)
        count_result = await db.execute(count_query)
        detection_count = count_result.scalar() or 0

        data.append({
            "id": s.id,
            "source_filename": s.source_filename,
            "status": s.status,
            "file_type": s.file_type,
            "file_size_bytes": s.file_size_bytes,
            "channel": s.channel,
            "created_at": s.created_at,
            "detection_count": detection_count,
        })

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "limit": limit,
            "offset": offset,
            "total_count": len(data),
        },
    }


@router.get("/{survey_id}")
async def get_survey(
    survey_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get full survey details."""
    query = (
        select(Survey)
        .options(
            selectinload(Survey.sonar_metadata),
            selectinload(Survey.jobs),
        )
        .where(Survey.id == survey_id)
    )
    result = await db.execute(query)
    survey = result.scalar_one_or_none()

    if not survey:
        raise SurveyNotFoundError(survey_id)

    latest_job = None
    if survey.jobs:
        latest_job = sorted(survey.jobs, key=lambda j: j.created_at, reverse=True)[0]

    data = {
        "id": survey.id,
        "source_filename": survey.source_filename,
        "status": survey.status,
        "file_type": survey.file_type,
        "file_size_bytes": survey.file_size_bytes,
        "channel": survey.channel,
        "created_at": survey.created_at,
        "updated_at": survey.updated_at,
        "sonar_metadata": None,
        "latest_job": None,
    }

    if survey.sonar_metadata:
        data["sonar_metadata"] = {
            "frequency_hz": survey.sonar_metadata.frequency_hz,
            "total_pings": survey.sonar_metadata.total_pings,
            "min_latitude": survey.sonar_metadata.min_latitude,
            "max_latitude": survey.sonar_metadata.max_latitude,
            "min_longitude": survey.sonar_metadata.min_longitude,
            "max_longitude": survey.sonar_metadata.max_longitude,
        }

    if latest_job:
        data["latest_job"] = {
            "id": latest_job.id,
            "status": latest_job.status,
            "progress_pct": latest_job.progress_pct,
            "current_stage": latest_job.current_stage,
            "created_at": latest_job.created_at,
        }

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.delete("/{survey_id}")
async def delete_survey(
    survey_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Delete a survey and its related resources."""
    survey_query = select(Survey).where(Survey.id == survey_id)
    result = await db.execute(survey_query)
    survey = result.scalar_one_or_none()

    if not survey:
        raise SurveyNotFoundError(survey_id)

    storage = get_storage()
    try:
        storage.delete_file(survey.storage_path)
    except Exception:
        pass

    reports_query = select(Report).where(Report.survey_id == survey_id)
    reports_result = await db.execute(reports_query)
    for report in reports_result.scalars().all():
        try:
            storage.delete_file(report.storage_path)
        except Exception:
            pass

    await db.delete(survey)
    await db.commit()

    return {
        "success": True,
        "data": {"deleted": True},
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.post("/{survey_id}/reprocess", status_code=status.HTTP_201_CREATED)
async def reprocess_survey(
    survey_id: uuid.UUID,
    request: Request,
    payload: ReprocessRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Reprocess an existing survey with new parameters."""
    survey_query = select(Survey).where(Survey.id == survey_id)
    result = await db.execute(survey_query)
    survey = result.scalar_one_or_none()

    if not survey:
        raise SurveyNotFoundError(survey_id)

    job = ProcessingJob(
        id=uuid.uuid4(),
        survey_id=survey.id,
        status="pending",
        progress_pct=0,
        current_stage="queued",
        detection_conf_threshold=payload.detection_conf_threshold,
        nms_iou_threshold=payload.nms_iou_threshold,
        tile_size=settings.TILE_SIZE,
        tile_overlap=settings.TILE_OVERLAP,
    )
    db.add(job)
    survey.status = "queued"
    await db.commit()
    await db.refresh(job)

    try:
        from backend.tasks import process_survey
        task = process_survey.delay(str(survey.id), str(job.id))
        job.celery_task_id = str(task.id)
        job.status = "running"
        await db.commit()
    except Exception as e:
        logger.warning("Could not enqueue Celery task: %s", str(e))

    return {
        "success": True,
        "data": {
            "job_id": job.id,
            "status": job.status,
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/{survey_id}/sonar-image")
async def get_sonar_image(
    survey_id: uuid.UUID,
    request: Request,
    channel: str = Query("starboard"),
    mode: str = Query("raw"),
    max_height: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Serve the processed sonar image."""
    survey_query = select(Survey).where(Survey.id == survey_id)
    result = await db.execute(survey_query)
    survey = result.scalar_one_or_none()

    if not survey:
        raise SurveyNotFoundError(survey_id)

    storage = get_storage()
    try:
        file_bytes = storage.read_file(survey.storage_path)
        return Response(content=file_bytes, media_type="image/png")
    except Exception:
        raise AppException(message="Sonar image not found in storage.", status_code=404)
