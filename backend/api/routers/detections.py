import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, get_settings
from backend.database.models import Detection, Survey
from backend.exceptions import DetectionNotFoundError, SurveyNotFoundError
from backend.storage.storage import get_storage

router = APIRouter(tags=["Detections"])

class DetectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    survey_id: uuid.UUID
    job_id: uuid.UUID
    detection_code: str
    class_name: str
    confidence: float
    confidence_calibrated: Optional[float]
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    estimated_length_m: Optional[float]
    estimated_width_m: Optional[float]
    geotagging_available: bool
    latitude: Optional[float]
    longitude: Optional[float]
    ping_number: Optional[int]
    ping_timestamp: Optional[float]
    is_filtered: bool
    filtered_reason: Optional[str]
    source_tile_url: Optional[str]
    created_at: datetime

@router.get("/surveys/{survey_id}/detections")
async def get_survey_detections(
    survey_id: uuid.UUID,
    request: Request,
    job_id: Optional[uuid.UUID] = Query(None),
    class_name: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    include_filtered: bool = Query(False),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List detections for a given survey."""
    # Check survey exists
    survey_result = await db.execute(select(Survey).where(Survey.id == survey_id))
    if not survey_result.scalar_one_or_none():
        raise SurveyNotFoundError(survey_id)
        
    query = select(Detection).where(Detection.survey_id == survey_id)
    
    if job_id:
        query = query.where(Detection.job_id == job_id)
    if class_name:
        query = query.where(Detection.class_name == class_name)
    if min_confidence is not None:
        query = query.where(Detection.confidence >= min_confidence)
    if not include_filtered:
        query = query.where(Detection.is_filtered == False)
        
    # Count total matching query
    count_query = select(func.count(Detection.id)).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0
    
    # Get paginated results
    query = query.order_by(desc(Detection.confidence)).limit(limit).offset(offset)
    result = await db.execute(query)
    detections = result.scalars().all()
    
    data = []
    settings = get_settings()
    for det in detections:
        det_dict = {
            "id": det.id,
            "survey_id": det.survey_id,
            "job_id": det.job_id,
            "detection_code": det.detection_code,
            "class_name": det.class_name,
            "confidence": det.confidence,
            "confidence_calibrated": det.confidence_calibrated,
            "bbox_x": det.bbox_x,
            "bbox_y": det.bbox_y,
            "bbox_w": det.bbox_w,
            "bbox_h": det.bbox_h,
            "estimated_length_m": det.estimated_length_m,
            "estimated_width_m": det.estimated_width_m,
            "geotagging_available": det.geotagging_available,
            "latitude": det.latitude,
            "longitude": det.longitude,
            "ping_number": det.ping_number,
            "ping_timestamp": det.ping_timestamp,
            "is_filtered": det.is_filtered,
            "filtered_reason": det.filtered_reason,
            "created_at": det.created_at,
            "source_tile_url": f"{settings.API_V1_STR}/detections/{det.id}/tile" if det.source_tile_path else None
        }
        data.append(det_dict)

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "limit": limit,
            "offset": offset,
            "total_count": total_count,
            "filtered_count": total_count  # In context, how many matched the filter
        }
    }

@router.get("/detections/{detection_id}")
async def get_detection(
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get single detection detail."""
    query = select(Detection).where(Detection.id == detection_id)
    result = await db.execute(query)
    det = result.scalar_one_or_none()
    
    if not det:
        raise DetectionNotFoundError(detection_id)
        
    settings = get_settings()
    source_tile_url = f"{settings.API_V1_STR}/detections/{det.id}/tile" if det.source_tile_path else None
    
    data = {
        "id": det.id,
        "survey_id": det.survey_id,
        "job_id": det.job_id,
        "detection_code": det.detection_code,
        "class_name": det.class_name,
        "confidence": det.confidence,
        "confidence_calibrated": det.confidence_calibrated,
        "bbox_x": det.bbox_x,
        "bbox_y": det.bbox_y,
        "bbox_w": det.bbox_w,
        "bbox_h": det.bbox_h,
        "mask_rle": det.mask_rle,
        "estimated_length_m": det.estimated_length_m,
        "estimated_width_m": det.estimated_width_m,
        "geotagging_available": det.geotagging_available,
        "latitude": det.latitude,
        "longitude": det.longitude,
        "ping_number": det.ping_number,
        "ping_timestamp": det.ping_timestamp,
        "is_filtered": det.is_filtered,
        "filtered_reason": det.filtered_reason,
        "extra_metadata": det.extra_metadata,
        "created_at": det.created_at,
        "source_tile_url": source_tile_url
    }

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
