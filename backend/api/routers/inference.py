import io
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
import numpy as np
import cv2
import torch
from ultralytics import YOLO

from backend.schemas.inference import InferenceResponseData, SingleDetectionResult, BoundingBox
from backend.services.model_evaluation_service import get_model_evaluation_service

router = APIRouter(prefix="/inference", tags=["Inference"])

# Production model path and verified SHA256
PROD_MODEL_PATH = "models/detection/sonar_yolov8_fls_trained.pt"
PROD_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"

CLASS_NAMES = [
    "derelict_fishing_gear",
    "general_marine_debris",
    "shipwreck",
    "pipe_or_cylinder",
    "other_man_made_target",
]

# In-memory model cache for latency preservation
_LOADED_MODELS: Dict[str, YOLO] = {}


def _get_or_load_model(checkpoint_path: str) -> YOLO:
    if checkpoint_path not in _LOADED_MODELS:
        if not os.path.exists(checkpoint_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Checkpoint weights not found at {checkpoint_path}",
            )
        _LOADED_MODELS[checkpoint_path] = YOLO(checkpoint_path)
    return _LOADED_MODELS[checkpoint_path]


@router.post("/predict")
async def predict_sonar_frame(
    request: Request,
    file: UploadFile = File(...),
    model_id: Optional[str] = Form("production_fls_yolov8n"),
    confidence_threshold: Optional[float] = Form(0.25),
    iou_threshold: Optional[float] = Form(0.45),
    device: Optional[str] = Form("cpu"),
):
    """
    Production acoustic frame object detection endpoint.
    Performs real-time YOLOv8 inference on forward-looking or side-scan sonar imagery.
    """
    t_start = time.perf_counter()

    # Read uploaded file
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty image payload provided",
        )

    # Decode image
    t_pre_start = time.perf_counter()
    np_arr = np.frombuffer(file_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_UNCHANGED)
    if image is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to decode acoustic image. Ensure valid PNG, JPEG, or TIFF format.",
        )

    # Normalize image channels and range
    if len(image.shape) == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    elif len(image.shape) == 3 and image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    elif len(image.shape) == 3 and image.shape[2] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    if image.dtype != np.uint8:
        if image.max() <= 1.0:
            image = (image * 255.0).clip(0, 255).astype(np.uint8)
        else:
            image = image.clip(0, 255).astype(np.uint8)

    t_pre_end = time.perf_counter()
    preprocessing_ms = (t_pre_end - t_pre_start) * 1000.0

    # Resolve model checkpoint
    eval_service = get_model_evaluation_service()
    checkpoint_path = PROD_MODEL_PATH
    is_prod = True

    if model_id and model_id != "production_fls_yolov8n":
        candidate_model = eval_service.get_model_detail(model_id)
        if candidate_model and candidate_model.get("checkpoint_path"):
            checkpoint_path = candidate_model["checkpoint_path"]
            is_prod = candidate_model.get("is_production", False)

    yolo_model = _get_or_load_model(checkpoint_path)

    # Compute SHA256 of checkpoint
    with open(checkpoint_path, "rb") as f:
        ckpt_sha256 = hashlib.sha256(f.read()).hexdigest()

    # Run inference with torch.inference_mode()
    t_infer_start = time.perf_counter()
    with torch.inference_mode():
        results = yolo_model.predict(
            image,
            conf=confidence_threshold,
            iou=iou_threshold,
            device=device,
            verbose=False,
        )
    t_infer_end = time.perf_counter()
    inference_ms = (t_infer_end - t_infer_start) * 1000.0

    # Postprocessing
    t_post_start = time.perf_counter()
    detections: List[SingleDetectionResult] = []

    if results and len(results) > 0 and results[0].boxes:
        for box in results[0].boxes:
            cls_id = int(box.cls[0].item())
            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = box.xyxy[0].tolist()

            w = float(x2 - x1)
            h = float(y2 - y1)
            x = float(x1)
            y = float(y1)

            class_name = (
                CLASS_NAMES[cls_id]
                if cls_id < len(CLASS_NAMES)
                else f"target_class_{cls_id}"
            )

            detections.append(
                SingleDetectionResult(
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=round(conf, 4),
                    bbox=BoundingBox(
                        x=round(x, 1),
                        y=round(y, 1),
                        width=round(w, 1),
                        height=round(h, 1),
                    ),
                    confidence_calibrated=round(conf, 4),
                    is_filtered=False,
                )
            )

    t_post_end = time.perf_counter()
    postprocessing_ms = (t_post_end - t_post_start) * 1000.0
    total_ms = (time.perf_counter() - t_start) * 1000.0

    response_data = InferenceResponseData(
        model_id=model_id or "production_fls_yolov8n",
        checkpoint_path=checkpoint_path,
        checkpoint_sha256=ckpt_sha256,
        is_production_checkpoint=is_prod,
        inference_time_ms=round(inference_ms, 2),
        preprocessing_time_ms=round(preprocessing_ms, 2),
        postprocessing_time_ms=round(postprocessing_ms, 2),
        total_time_ms=round(total_ms, 2),
        device=device,
        detections=detections,
        detection_count=len(detections),
        operating_thresholds={
            "confidence_threshold": confidence_threshold,
            "iou_threshold": iou_threshold,
        },
        provenance={
            "source_filename": file.filename,
            "image_dimensions": [image.shape[1], image.shape[0]],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )

    return {
        "success": True,
        "data": response_data.model_dump(),
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/health")
async def get_inference_health(request: Request):
    """Inspect status and readiness of inference runtime."""
    prod_exists = os.path.exists(PROD_MODEL_PATH)
    return {
        "success": True,
        "data": {
            "status": "ready" if prod_exists else "degraded",
            "device": "cpu",
            "loaded_models": list(_LOADED_MODELS.keys()),
            "production_weights_found": prod_exists,
            "production_sha256": PROD_SHA256,
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/model")
async def get_inference_model_info(
    request: Request,
    model_id: Optional[str] = "production_fls_yolov8n",
):
    """Retrieve active inference model metadata and operating parameters."""
    eval_service = get_model_evaluation_service()
    model_meta = eval_service.get_model_detail(model_id)
    if not model_meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inference model '{model_id}' not found in registry",
        )

    return {
        "success": True,
        "data": model_meta,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }

