import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, Query, Request, status, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db, get_settings
from backend.database.models import Detection, Survey
from backend.exceptions import DetectionNotFoundError, SurveyNotFoundError
from backend.storage.storage import get_storage

router = APIRouter(tags=["Detections"])


@router.get("/detections")
async def list_all_detections(
    request: Request,
    survey_id: Optional[uuid.UUID] = Query(None),
    job_id: Optional[uuid.UUID] = Query(None),
    class_name: Optional[str] = Query(None),
    min_confidence: Optional[float] = Query(None),
    include_filtered: bool = Query(False),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List detections across all surveys or filtered by survey, class, or confidence."""
    query = select(Detection)
    if survey_id:
        query = query.where(Detection.survey_id == survey_id)
    if job_id:
        query = query.where(Detection.job_id == job_id)
    if class_name:
        query = query.where(Detection.class_name == class_name)
    if min_confidence is not None:
        query = query.where(Detection.confidence >= min_confidence)
    if not include_filtered:
        query = query.where(Detection.is_filtered == False)

    count_query = select(func.count(Detection.id)).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total_count = count_result.scalar() or 0

    query = query.order_by(desc(Detection.confidence)).limit(limit).offset(offset)
    result = await db.execute(query)
    detections = result.scalars().all()

    data = []
    settings = get_settings()
    for det in detections:
        source_tile_url = f"{settings.API_V1_STR}/detections/{det.id}/tile" if det.source_tile_path else None
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
            "bbox": {
                "x": det.bbox_x,
                "y": det.bbox_y,
                "width": det.bbox_w,
                "height": det.bbox_h,
            },
            "primary_detector": "YOLOv8n-FLS",
            "detection_stage": "primary_detection",
            "segmentation": {
                "status": getattr(det, "segmentation_status", "unavailable") or "unavailable",
                "confidence": getattr(det, "segmentation_confidence", None),
                "mask_area": getattr(det, "mask_area", None),
                "mask_rle": det.mask_rle,
            },
            "classification": {
                "role": "secondary_verification",
                "status": getattr(det, "classification_status", "unavailable") or "unavailable",
                "model": getattr(det, "classifier_name", None),
                "class_name": getattr(det, "classifier_class", None),
                "confidence": getattr(det, "classifier_confidence", None),
                "agreement": getattr(det, "classification_agreement", None),
            },
            "geolocation": {
                "latitude": det.latitude,
                "longitude": det.longitude,
            },
            "dimensions": {
                "length_m": det.estimated_length_m,
                "width_m": det.estimated_width_m,
            },
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
            "source_tile_url": source_tile_url,
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
            "filtered_count": total_count,
        },
    }


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
    """List detections for a given survey with both backward-compatible flat fields and structured ML metadata."""
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
        source_tile_url = f"{settings.API_V1_STR}/detections/{det.id}/tile" if det.source_tile_path else None
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
            "bbox": {
                "x": det.bbox_x,
                "y": det.bbox_y,
                "width": det.bbox_w,
                "height": det.bbox_h,
            },
            "primary_detector": "YOLOv8n-FLS",
            "detection_stage": "primary_detection",
            "segmentation": {
                "status": getattr(det, "segmentation_status", "unavailable") or "unavailable",
                "confidence": getattr(det, "segmentation_confidence", None),
                "mask_area": getattr(det, "mask_area", None),
                "mask_rle": det.mask_rle,
            },
            "classification": {
                "role": "secondary_verification",
                "status": getattr(det, "classification_status", "unavailable") or "unavailable",
                "model": getattr(det, "classifier_name", None),
                "class_name": getattr(det, "classifier_class", None),
                "confidence": getattr(det, "classifier_confidence", None),
                "agreement": getattr(det, "classification_agreement", None),
            },
            "geolocation": {
                "latitude": det.latitude,
                "longitude": det.longitude,
            },
            "dimensions": {
                "length_m": det.estimated_length_m,
                "width_m": det.estimated_width_m,
            },
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
            "source_tile_url": source_tile_url,
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
            "filtered_count": total_count,
        },
    }


@router.get("/detections/{detection_id}")
async def get_detection(
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get single detection detail with structured segmentation and classification blocks."""
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
        "bbox": {
            "x": det.bbox_x,
            "y": det.bbox_y,
            "width": det.bbox_w,
            "height": det.bbox_h,
        },
        "primary_detector": "YOLOv8n-FLS",
        "detection_stage": "primary_detection",
        "segmentation": {
            "status": getattr(det, "segmentation_status", "unavailable") or "unavailable",
            "confidence": getattr(det, "segmentation_confidence", None),
            "mask_area": getattr(det, "mask_area", None),
            "mask_rle": det.mask_rle,
            "mask_geometry": getattr(det, "mask_geometry", None),
        },
        "classification": {
            "role": "secondary_verification",
            "status": getattr(det, "classification_status", "unavailable") or "unavailable",
            "model": getattr(det, "classifier_name", None),
            "class_name": getattr(det, "classifier_class", None),
            "confidence": getattr(det, "classifier_confidence", None),
            "agreement": getattr(det, "classification_agreement", None),
        },
        "geolocation": {
            "latitude": det.latitude,
            "longitude": det.longitude,
        },
        "dimensions": {
            "length_m": det.estimated_length_m,
            "width_m": det.estimated_width_m,
        },
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
        "source_tile_url": source_tile_url,
    }

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/surveys/{survey_id}/detections/{detection_id}")
async def get_survey_detection_detail(
    survey_id: uuid.UUID,
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Scoped endpoint to fetch a single detection for a survey."""
    query = select(Detection).where(Detection.id == detection_id, Detection.survey_id == survey_id)
    result = await db.execute(query)
    det = result.scalar_one_or_none()
    if not det:
        raise DetectionNotFoundError(detection_id)
    return await get_detection(detection_id=detection_id, request=request, db=db)


@router.get("/surveys/{survey_id}/detections/{detection_id}/segmentation")
async def get_detection_segmentation(
    survey_id: uuid.UUID,
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get segmentation mask and boundary contour for a specific detection."""
    query = select(Detection).where(Detection.id == detection_id, Detection.survey_id == survey_id)
    result = await db.execute(query)
    det = result.scalar_one_or_none()
    if not det:
        raise DetectionNotFoundError(detection_id)

    seg_status = getattr(det, "segmentation_status", "unavailable") or "unavailable"
    return {
        "success": True,
        "data": {
            "detection_id": det.id,
            "status": seg_status,
            "is_available": seg_status == "available",
            "confidence": getattr(det, "segmentation_confidence", None),
            "mask_area": getattr(det, "mask_area", None),
            "mask_rle": det.mask_rle,
            "mask_geometry": getattr(det, "mask_geometry", None),
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/surveys/{survey_id}/detections/{detection_id}/classification")
async def get_detection_classification(
    survey_id: uuid.UUID,
    detection_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get secondary classification results and agreement status for a detection."""
    query = select(Detection).where(Detection.id == detection_id, Detection.survey_id == survey_id)
    result = await db.execute(query)
    det = result.scalar_one_or_none()
    if not det:
        raise DetectionNotFoundError(detection_id)

    classif_status = getattr(det, "classification_status", "unavailable") or "unavailable"
    return {
        "success": True,
        "data": {
            "detection_id": det.id,
            "status": classif_status,
            "is_available": classif_status == "available",
            "classifier_model": getattr(det, "classifier_name", None),
            "predicted_class": getattr(det, "classifier_class", None),
            "confidence": getattr(det, "classifier_confidence", None),
            "agreement": getattr(det, "classification_agreement", None),
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
