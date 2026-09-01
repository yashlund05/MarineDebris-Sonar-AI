import io
import os
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, get_settings
from backend.database.models import Detection, ProcessingJob, Report, Survey
from backend.exceptions import (
    AppException,
    NotFoundError,
    SurveyNotFoundError,
    ValidationError,
)
from backend.reporting.csv_reporter import generate_csv_report
from backend.reporting.geojson_reporter import generate_geojson_report
from backend.reporting.json_reporter import generate_json_report
from backend.storage.storage import get_storage

router = APIRouter(tags=["Reports"])


class GenerateReportRequest(BaseModel):
    format: str
    job_id: Optional[uuid.UUID] = None
    min_confidence: Optional[float] = None
    include_filtered: bool = False


@router.get("/surveys/{survey_id}/reports")
async def list_reports(
    survey_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """List all reports generated for a survey."""
    survey_result = await db.execute(select(Survey).where(Survey.id == survey_id))
    if not survey_result.scalar_one_or_none():
        raise SurveyNotFoundError(survey_id)

    query = select(Report).where(Report.survey_id == survey_id).order_by(desc(Report.created_at))
    result = await db.execute(query)
    reports = result.scalars().all()

    settings = get_settings()

    data = []
    for rep in reports:
        data.append({
            "report_id": rep.id,
            "job_id": rep.job_id,
            "format": rep.format,
            "file_size_bytes": rep.file_size_bytes,
            "detection_count": rep.detection_count,
            "created_at": rep.created_at,
            "download_url": f"{settings.API_V1_STR}/reports/{rep.id}/download",
        })

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.post("/surveys/{survey_id}/reports/generate", status_code=status.HTTP_201_CREATED)
async def generate_report(
    survey_id: uuid.UUID,
    request: Request,
    payload: GenerateReportRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate a new report for a survey."""
    fmt = payload.format.lower()
    if fmt not in ("json", "csv", "geojson"):
        raise ValidationError(f"Format must be 'json', 'csv', or 'geojson', got '{fmt}'")

    survey_result = await db.execute(select(Survey).where(Survey.id == survey_id))
    survey = survey_result.scalar_one_or_none()
    if not survey:
        raise SurveyNotFoundError(survey_id)

    # Get the target job
    job_id = payload.job_id
    if not job_id:
        # Get the latest completed job
        job_query = select(ProcessingJob).where(ProcessingJob.survey_id == survey_id).order_by(desc(ProcessingJob.created_at))
        job_result = await db.execute(job_query)
        latest_job = job_result.scalars().first()
        if not latest_job:
            raise AppException("No processing job found for survey.", status_code=400, error_code="NO_JOB")
        job_id = latest_job.id

    # Fetch detections
    det_query = select(Detection).where(Detection.job_id == job_id)
    if payload.min_confidence is not None:
        det_query = det_query.where(Detection.confidence >= payload.min_confidence)
    if not payload.include_filtered:
        det_query = det_query.where(Detection.is_filtered == False)

    det_result = await db.execute(det_query)
    detections = det_result.scalars().all()

    # Convert detections to dicts
    det_dicts = []
    for d in detections:
        det_dicts.append({
            "id": str(d.id),
            "detection_code": d.detection_code,
            "class_name": d.class_name,
            "confidence": d.confidence,
            "confidence_calibrated": d.confidence_calibrated,
            "bbox_x": d.bbox_x,
            "bbox_y": d.bbox_y,
            "bbox_w": d.bbox_w,
            "bbox_h": d.bbox_h,
            "estimated_length_m": d.estimated_length_m,
            "estimated_width_m": d.estimated_width_m,
            "geotagging_available": d.geotagging_available,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "ping_number": d.ping_number,
            "ping_timestamp": d.ping_timestamp,
            "is_filtered": d.is_filtered,
            "filtered_reason": d.filtered_reason,
        })

    # Prepare local output path
    temp_dir = os.path.join(tempfile.gettempdir(), "marine_sonar_reports")
    os.makedirs(temp_dir, exist_ok=True)
    report_id = uuid.uuid4()
    local_path = os.path.join(temp_dir, f"{report_id}.{fmt}")

    # Call appropriate reporter
    if fmt == "json":
        survey_info = {
            "survey_id": str(survey.id),
            "source_filename": survey.source_filename,
        }
        generate_json_report(det_dicts, survey_info, local_path)
    elif fmt == "csv":
        generate_csv_report(det_dicts, local_path)
    elif fmt == "geojson":
        generate_geojson_report(det_dicts, local_path)

    # Upload to storage
    storage = get_storage()
    with open(local_path, "rb") as f:
        storage_path = storage.save_file(f, f"reports/{survey_id}", filename=f"{report_id}.{fmt}")

    file_size = os.path.getsize(local_path)

    # Save Report record
    report = Report(
        id=report_id,
        survey_id=survey_id,
        job_id=job_id,
        format=fmt,
        storage_path=storage_path,
        file_size_bytes=file_size,
        detection_count=len(det_dicts),
    )
    db.add(report)
    await db.commit()

    settings = get_settings()

    return {
        "success": True,
        "data": {
            "report_id": report.id,
            "format": report.format,
            "download_url": f"{settings.API_V1_STR}/reports/{report.id}/download",
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Download a generated report."""
    query = select(Report).where(Report.id == report_id)
    result = await db.execute(query)
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError(message=f"Report not found with id {report_id}", details={"report_id": str(report_id)})

    storage = get_storage()
    try:
        file_bytes = storage.read_file(report.storage_path)
    except Exception:
        raise NotFoundError(message="Report file not found in storage.")

    media_types = {
        "json": "application/json",
        "csv": "text/csv",
        "geojson": "application/geo+json",
    }
    content_type = media_types.get(report.format, "application/octet-stream")

    filename = f"survey_{report.survey_id}_report.{report.format}"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
    }

    return Response(content=file_bytes, media_type=content_type, headers=headers)
