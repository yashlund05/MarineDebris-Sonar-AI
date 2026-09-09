"""
FastAPI Router for SidescanTools-Based Sonar Image Enhancement & Visualization Pipeline.
Smart India Hackathon 2026 — PS26057.

Endpoints:
- POST /sonar/enhance : Process dataset sample, survey image, or data URL
- POST /sonar/enhance/upload : Direct file upload processing
- POST /sonar/recolor : Ultra-fast colormap recoloring on cached enhancement (< 5ms)
- GET /sonar/download : Download full-resolution raw, enhanced grayscale, or pseudocolor PNG
- GET /sonar/samples : Get curated benchmark development sample images
- GET /sonar/palettes : List supported acoustic false-color palettes
"""

import os
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import cv2
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_db
from backend.database.models import Survey
from backend.storage.storage import get_storage
from backend.enhancement.data_loader import BenchmarkDatasetLoader
from backend.services.sonar_enhancement import (
    SonarEnhancementProcessor,
    SonarEnhancementConfig,
    ColormapName,
    DetectionInputMode,
)
from backend.services.sonar_enhancement.image_export import encode_to_png_bytes

router = APIRouter(prefix="", tags=["Sidescan Sonar Enhancement"])
processor = SonarEnhancementProcessor.get_instance()
loader = BenchmarkDatasetLoader()


class ProcessSonarRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    image_data_url: Optional[str] = None
    convert_to_db: Optional[bool] = True
    stripe_noise_filter: Optional[bool] = True
    clahe: Optional[bool] = True
    clahe_clip_limit: Optional[float] = 0.01
    clahe_grid_size: Optional[List[int]] = [8, 8]
    sharpening: Optional[bool] = False
    sharpening_gamma_h: Optional[float] = 2.0
    sharpening_gamma_l: Optional[float] = 0.5
    sharpening_c: Optional[float] = 1.5
    gain_normalization: Optional[bool] = False
    colormap: Optional[str] = "amber"
    run_detection: Optional[bool] = False
    conf_threshold: Optional[float] = 0.25
    detection_input_mode: Optional[str] = "enhanced_grayscale"


class RecolorRequest(BaseModel):
    cache_key: str
    colormap: str = "amber"


def _get_detector_if_requested(run_detection: bool):
    if not run_detection:
        return None
    try:
        from backend.ml.detector.yolo_detector import YOLOv8Detector
        detector = YOLOv8Detector()
        return detector
    except Exception:
        return None


@router.get("/palettes")
async def get_palettes():
    """Returns available false-color palettes for display-only visualization."""
    return {
        "success": True,
        "palettes": [
            {
                "id": "amber",
                "name": "Oceanographic Amber",
                "description": "Standard high-resolution ARIS/DIDSON sonar bronze-amber palette. Optimized for shadow-highlight contrast.",
                "is_default": True,
            },
            {
                "id": "viridis",
                "name": "Viridis (Perceptually Uniform)",
                "description": "Perceptually uniform sequential colormap from deep blue to bright yellow.",
                "is_default": False,
            },
            {
                "id": "inferno",
                "name": "Inferno (High Contrast)",
                "description": "Warm black-red-yellow map highlighting intense acoustic reflections.",
                "is_default": False,
            },
            {
                "id": "magma",
                "name": "Magma",
                "description": "Smooth black-purple-white thermal gradient.",
                "is_default": False,
            },
            {
                "id": "plasma",
                "name": "Plasma",
                "description": "High perceptual gradient across intermediate acoustic backscatter.",
                "is_default": False,
            },
            {
                "id": "turbo",
                "name": "Turbo (Rainbow Alternative)",
                "description": "Enhanced rainbow with smooth perceptual linearity across all frequencies.",
                "is_default": False,
            },
            {
                "id": "copper",
                "name": "Copper",
                "description": "Classic marine acoustic copper gradient.",
                "is_default": False,
            },
            {
                "id": "grayscale",
                "name": "Acoustic Grayscale",
                "description": "Standard scientific monochromatic intensity (linear backscatter).",
                "is_default": False,
            },
        ],
    }


@router.get("/samples")
async def get_sample_images(dataset_version: str = "v3", split: str = "val", limit: int = 25):
    """Returns curated development sample frames for instant enhancement demonstration."""
    try:
        samples = loader.get_development_samples(dataset_version=dataset_version, split=split, limit=limit)
        return {
            "success": True,
            "dataset_version": dataset_version,
            "split": split,
            "samples": [
                {
                    "name": s["image_name"],
                    "has_annotations": len(s["boxes"]) > 0,
                    "box_count": len(s["boxes"]),
                }
                for s in samples
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/enhance")
async def enhance_sonar_image(
    payload: ProcessSonarRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Main enhancement endpoint.
    Processes dataset image, survey frame, or base64 data URL.
    Returns untouched raw, enhanced grayscale, display pseudocolor, metrics, and audit trail.
    """
    image_bytes = None
    filename = "sonar_frame.png"

    if payload.survey_id:
        try:
            s_id = uuid.UUID(payload.survey_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid survey UUID")
        stmt = select(Survey).where(Survey.id == s_id)
        res = await db.execute(stmt)
        survey = res.scalar_one_or_none()
        if not survey or not survey.storage_path:
            raise HTTPException(status_code=404, detail="Survey image not found")
        storage = get_storage()
        image_bytes = storage.read_file(survey.storage_path)
        filename = Path(survey.storage_path).name

    elif payload.image_data_url:
        if "," in payload.image_data_url:
            import base64
            _, b64_str = payload.image_data_url.split(",", 1)
            image_bytes = base64.b64decode(b64_str)
        else:
            raise HTTPException(status_code=400, detail="Invalid data URL format")
        filename = payload.image_name or "sonar_frame.png"

    elif payload.image_name and payload.image_name != "__custom_upload__":
        safe_name = Path(payload.image_name).name
        samples = loader.get_development_samples(
            dataset_version=payload.dataset_version or "v3",
            split=payload.split or "val",
        )
        matched = next((s for s in samples if s["image_name"] == safe_name), None)
        if not matched:
            try:
                # Also fallback search in other splits if not found in specified split
                other_samples = loader.get_development_samples(dataset_version="v3", split="train") + loader.get_development_samples(dataset_version="v2", split="val")
                matched = next((s for s in other_samples if s["image_name"] == safe_name), None)
            except Exception:
                matched = None
        if not matched:
            raise HTTPException(
                status_code=404,
                detail=f"Sample '{safe_name}' not found in dataset.",
            )
        image_bytes = Path(matched["image_path"]).read_bytes()
        filename = safe_name

    else:
        # Default fallback for initial cold start: use canonical first development sample (ARIS 3000 FLS)
        # NEVER load annotated composite demo asset sample_annotation_viz.png
        dev_samples = loader.get_development_samples(dataset_version="v3", split="val", limit=1)
        if dev_samples:
            image_bytes = Path(dev_samples[0]["image_path"]).read_bytes()
            filename = dev_samples[0]["image_name"]
        else:
            sample = loader.get_smoke_test_sample()
            image_bytes = Path(sample["image_path"]).read_bytes()
            filename = Path(sample["image_path"]).name

    if not image_bytes:
        raise HTTPException(status_code=400, detail="Could not read valid sonar image bytes")

    grid = tuple(payload.clahe_grid_size) if payload.clahe_grid_size else (8, 8)
    cfg = SonarEnhancementConfig(
        convert_to_db=payload.convert_to_db if payload.convert_to_db is not None else True,
        stripe_noise_filter=payload.stripe_noise_filter if payload.stripe_noise_filter is not None else True,
        clahe=payload.clahe if payload.clahe is not None else True,
        clahe_clip_limit=payload.clahe_clip_limit or 0.01,
        clahe_grid_size=grid,
        sharpening=payload.sharpening or False,
        sharpening_gamma_h=payload.sharpening_gamma_h or 2.0,
        sharpening_gamma_l=payload.sharpening_gamma_l or 0.5,
        sharpening_c=payload.sharpening_c or 1.5,
        gain_normalization=payload.gain_normalization or False,
        colormap=payload.colormap or "amber",
        detection_input_mode=payload.detection_input_mode or "enhanced_grayscale",
    )

    detector = _get_detector_if_requested(payload.run_detection or False)

    try:
        result = processor.process_image_bytes(
            image_bytes=image_bytes,
            filename=filename,
            config=cfg,
            run_detection=payload.run_detection or False,
            detector=detector,
            conf_threshold=payload.conf_threshold or 0.25,
        )
        # Omit internal binary arrays from JSON response
        clean_res = {k: v for k, v in result.items() if not k.startswith("_")}
        return clean_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enhance/upload")
async def enhance_uploaded_file(
    file: UploadFile = File(...),
    convert_to_db: bool = Form(True),
    stripe_noise_filter: bool = Form(True),
    clahe: bool = Form(True),
    clahe_clip_limit: float = Form(0.01),
    sharpening: bool = Form(False),
    colormap: str = Form("amber"),
    run_detection: bool = Form(False),
    conf_threshold: float = Form(0.25),
    detection_input_mode: str = Form("enhanced_grayscale"),
):
    """Direct file upload enhancement endpoint."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    cfg = SonarEnhancementConfig(
        convert_to_db=convert_to_db,
        stripe_noise_filter=stripe_noise_filter,
        clahe=clahe,
        clahe_clip_limit=clahe_clip_limit,
        sharpening=sharpening,
        colormap=colormap,
        detection_input_mode=detection_input_mode,
    )

    detector = _get_detector_if_requested(run_detection)

    try:
        result = processor.process_image_bytes(
            image_bytes=contents,
            filename=file.filename or "uploaded_sonar.png",
            config=cfg,
            run_detection=run_detection,
            detector=detector,
            conf_threshold=conf_threshold,
        )
        clean_res = {k: v for k, v in result.items() if not k.startswith("_")}
        return clean_res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recolor")
async def recolor_cached_frame(payload: RecolorRequest):
    """
    Sub-10ms colormap recoloring endpoint.
    Recolors cached enhanced grayscale without re-executing FFT or CLAHE.
    """
    try:
        return processor.render_colormap_fast(
            cache_key=payload.cache_key,
            colormap=payload.colormap,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/download")
async def download_image(
    cache_key: str = Query(...),
    target: str = Query("enhanced_gray", pattern="^(raw|enhanced_gray|pseudocolor)$"),
):
    """Downloads full-resolution PNG for raw, enhanced grayscale, or pseudocolor representation."""
    if cache_key not in processor._memory_cache:
        raise HTTPException(status_code=404, detail="Enhancement cache key expired or not found")

    entry = processor._memory_cache[cache_key]
    if target == "raw":
        img_arr = entry["_raw_gray_u8"]
        filename = f"sonar_raw_{cache_key[:8]}.png"
    elif target == "enhanced_gray":
        img_arr = entry["_enhanced_gray_u8"]
        filename = f"sonar_enhanced_gray_{cache_key[:8]}.png"
    else:
        # Pseudocolor
        from backend.services.sonar_enhancement.image_export import apply_sonar_colormap
        img_arr = apply_sonar_colormap(entry["_enhanced_gray_u8"], colormap=entry["colormap"])
        filename = f"sonar_pseudocolor_{cache_key[:8]}.png"

    png_bytes = encode_to_png_bytes(img_arr)
    return Response(
        content=png_bytes,
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
