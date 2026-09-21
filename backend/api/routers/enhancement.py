"""
FastAPI Router for Intelligent Sonar Image Enhancement & Visibility Engine.

Endpoints:
- POST /enhancement/process : Processes an image with unified EnhancementManager
- GET /enhancement/profiles : Returns registered operational profiles with hypotheses
- GET /enhancement/palettes : Returns registered pseudocolor display palettes
- GET /enhancement/methods : Returns all classical enhancement methods
- GET /enhancement/providers : Returns health and status of all enhancement providers
- POST /enhancement/compare : Compares multiple methods on a single target image
- GET /enhancement/sample-images : Lists available development benchmark samples
- POST /enhancement/detect-improved : Runs YOLO on improved image (experimental)
"""

import base64
import io
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any
import numpy as np
import cv2
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database.session import get_db
from backend.database.models import Survey
from backend.storage.storage import get_storage
from backend.enhancement.types import (
    EnhancementMethod,
    PaletteType,
    ProfileName,
    MetricStatus,
)
from backend.enhancement.profiles import list_profiles, get_profile_info
from backend.enhancement.colormap import apply_palette, get_available_palettes
from backend.enhancement.metric_definitions import compute_enl, compute_cnr, compute_epi
from backend.enhancement.data_loader import BenchmarkDatasetLoader
from backend.enhancement.providers.manager import EnhancementManager

router = APIRouter(prefix="/enhancement", tags=["Sonar Image Enhancement"])
loader = BenchmarkDatasetLoader()
manager = EnhancementManager.get_instance()


class ProcessRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    image_data_url: Optional[str] = None
    method: Optional[str] = "auto"
    profile: Optional[str] = None
    palette: Optional[str] = "amber"
    parameters: Optional[Dict[str, Any]] = None


class CompareRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    methods: Optional[List[str]] = None
    palette: Optional[str] = "amber"


class DetectImprovedRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    method: Optional[str] = "auto"
    profile: Optional[str] = "BALANCED"
    conf_threshold: Optional[float] = 0.25


def _encode_png_base64(img: np.ndarray) -> str:
    """Encodes a uint8 image (grayscale or BGR) to base64 PNG data URL."""
    success, encoded = cv2.imencode(".png", img)
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    b64 = base64.b64encode(encoded.tobytes()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _decode_png_base64(data_url: str) -> np.ndarray:
    """Decodes a base64 data URL into float32 [0, 1] grayscale image with security checks."""
    if not data_url or "," not in data_url:
        raise ValueError("Invalid base64 image data URL")
    header, b64_str = data_url.split(",", 1)
    raw_bytes = base64.b64decode(b64_str)
    if len(raw_bytes) > 15 * 1024 * 1024:
        raise ValueError("Image payload exceeds 15MB limit")

    nparr = np.frombuffer(raw_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    if img is None or img.size == 0:
        raise ValueError("Failed to decode image from payload")
    return (img.astype(np.float32) / 255.0).clip(0.0, 1.0)


@router.get("/providers")
async def get_providers():
    """Returns runtime health and status of all enhancement providers."""
    return {
        "success": True,
        "providers": manager.get_providers_status()
    }


@router.get("/profiles")
async def get_profiles():
    """Returns list of candidate enhancement profiles with their scientific hypotheses."""
    return {
        "success": True,
        "profiles": list_profiles()
    }


@router.get("/palettes")
async def get_palettes():
    """Returns available display-only pseudocolor palettes."""
    return {
        "success": True,
        "palettes": get_available_palettes()
    }


@router.get("/methods")
async def get_methods():
    """Returns list of registered classical enhancement algorithms."""
    methods_meta = [
        {"id": "auto", "name": "Auto / Recommended", "description": "Automatically dispatches to best validated profile"},
        {"id": "identity", "name": "Identity Baseline", "description": "Unmodified acoustic backscatter control"},
        {"id": "percentile_normalize", "name": "Percentile Stretch", "description": "P2-P98 acoustic outlier suppression"},
        {"id": "gamma_correct", "name": "Gamma Power-Law", "description": "Contrast compression/expansion (gamma=0.7)"},
        {"id": "clahe_enhance", "name": "Adaptive CLAHE", "description": "Local histogram equalization (clip=2.0)"},
        {"id": "median_clahe", "name": "Median + CLAHE", "description": "Impulsive speckle removal prior to CLAHE"},
        {"id": "bilateral_clahe", "name": "Bilateral + CLAHE", "description": "Edge-preserving spatial filter prior to CLAHE"},
        {"id": "unsharp_clahe", "name": "Unsharp Mask + CLAHE", "description": "High-boost debris boundary sharpening"},
        {"id": "log_bilateral_clahe", "name": "Homomorphic Bilateral", "description": "Multiplicative speckle reduction in log domain"},
    ]
    return {
        "success": True,
        "methods": methods_meta
    }


@router.get("/sample-images")
async def get_sample_images(dataset_version: str = "v3", split: str = "val", limit: int = 25):
    """
    Returns list of development sample images for interactive workstation analysis.
    Only authorized non-test splits are accessible.
    """
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
                    "box_count": len(s["boxes"])
                }
                for s in samples
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/process")
async def process_image(payload: ProcessRequest, db: AsyncSession = Depends(get_db)):
    """
    Primary project-wide image improvement endpoint.
    Operates on dataset images, survey session images, uploaded base64 frames, or demo assets.
    Returns canonical enhanced grayscale, presentation pseudocolor, and scientific metrics.
    """
    try:
        raw_img = None
        boxes = []

        # 1. Resolve source image safely
        if payload.survey_id:
            try:
                s_id = uuid.UUID(payload.survey_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid survey UUID")
            stmt = select(Survey).where(Survey.id == s_id)
            res = await db.execute(stmt)
            survey = res.scalar_one_or_none()
            if not survey or not survey.storage_path:
                raise HTTPException(status_code=404, detail="Survey image not found in storage")
            storage = get_storage()
            file_bytes = storage.read_file(survey.storage_path)
            nparr = np.frombuffer(file_bytes, np.uint8)
            decoded = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            if decoded is None:
                raise HTTPException(status_code=500, detail="Failed to decode stored survey image")
            raw_img = (decoded.astype(np.float32) / 255.0).clip(0.0, 1.0)

        elif payload.image_data_url:
            raw_img = _decode_png_base64(payload.image_data_url)

        elif payload.image_name:
            # Prevent path traversal
            safe_name = Path(payload.image_name).name
            samples = loader.get_development_samples(
                dataset_version=payload.dataset_version or "v3",
                split=payload.split or "val"
            )
            matched = next((s for s in samples if s["image_name"] == safe_name), None)
            if not matched:
                raise HTTPException(status_code=404, detail=f"Sample '{safe_name}' not found in {payload.dataset_version}/{payload.split}")
            raw_img = loader.load_image_float32(matched["image_path"])
            boxes = matched.get("boxes", [])

        else:
            sample = loader.get_smoke_test_sample()
            raw_img = loader.load_image_float32(sample["image_path"])
            boxes = []

        if raw_img is None or raw_img.size == 0:
            raise HTTPException(status_code=400, detail="Could not resolve or decode valid sonar frame")

        # 2. Unified Enhancement Manager invocation
        method_req = payload.method or "auto"
        palette_str = payload.palette or "amber"
        enh_res, telemetry = manager.improve_sonar_image(
            image=raw_img,
            method=method_req,
            profile=payload.profile,
            parameters=payload.parameters,
            palette=palette_str
        )

        enhanced_gray = enh_res.canonical_image

        # 3. Apply display palette (PRESENTATION ONLY)
        palette_enum = PaletteType(palette_str) if palette_str in [p.value for p in PaletteType] else PaletteType.AMBER
        display_img_bgr = apply_palette(enhanced_gray, palette=palette_enum)
        raw_display_bgr = apply_palette(raw_img, palette=palette_enum)

        # 4. Compute acoustic metrics
        enl = compute_enl(enhanced_gray)
        epi = compute_epi(raw_img, enhanced_gray)

        cnr_list = []
        for b in boxes:
            bbox_norm = (b[1], b[2], b[3], b[4])
            c_res = compute_cnr(enhanced_gray, bbox_xywh_norm=bbox_norm)
            if c_res.status == MetricStatus.VALID and c_res.value is not None:
                cnr_list.append(c_res.value)

        mean_cnr = round(float(np.mean(cnr_list)), 3) if cnr_list else None

        enh_gray_u8 = (enhanced_gray * 255.0).clip(0, 255).astype(np.uint8)

        return {
            "success": True,
            "method": enh_res.method.value,
            "profile": payload.profile or (enh_res.profile_used.value if enh_res.profile_used else None),
            "palette": palette_enum.value,
            "parameters": enh_res.parameters,
            "provider_used": telemetry["provider_used"],
            "engine_status": telemetry["engine_status"],
            "cache_hit": telemetry["cache_hit"],
            "execution_time_ms": enh_res.execution_time_ms,
            "raw_image_data_url": _encode_png_base64(raw_display_bgr),
            "enhanced_image_data_url": _encode_png_base64(display_img_bgr),
            "canonical_grayscale_data_url": _encode_png_base64(enh_gray_u8),
            "metrics": {
                "enl": {
                    "value": enl.value,
                    "status": enl.status.value,
                    "unit": enl.unit,
                    "reason": enl.failure_reason
                },
                "epi": {
                    "value": epi.value,
                    "status": epi.status.value,
                    "unit": epi.unit,
                    "reason": epi.failure_reason
                },
                "cnr": {
                    "value": mean_cnr,
                    "status": MetricStatus.VALID.value if mean_cnr is not None else MetricStatus.NOT_MEASURABLE.value,
                    "unit": "ratio",
                    "valid_targets_evaluated": len(cnr_list)
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_methods(payload: CompareRequest, db: AsyncSession = Depends(get_db)):
    """
    Runs multiple enhancement methods against the specified image to support
    side-by-side empirical trade-off analysis.
    """
    try:
        raw_img = None
        boxes = []

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
            file_bytes = storage.read_file(survey.storage_path)
            nparr = np.frombuffer(file_bytes, np.uint8)
            decoded = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
            raw_img = (decoded.astype(np.float32) / 255.0).clip(0.0, 1.0)
        elif payload.image_name:
            safe_name = Path(payload.image_name).name
            samples = loader.get_development_samples(
                dataset_version=payload.dataset_version or "v3",
                split=payload.split or "val"
            )
            matched = next((s for s in samples if s["image_name"] == safe_name), None)
            if not matched:
                raise HTTPException(status_code=404, detail="Image not found")
            raw_img = loader.load_image_float32(matched["image_path"])
            boxes = matched.get("boxes", [])
        else:
            sample = loader.get_smoke_test_sample()
            raw_img = loader.load_image_float32(sample["image_path"])
            boxes = []

        methods_to_run = payload.methods or [
            "identity",
            "gamma_correct",
            "clahe_enhance",
            "median_clahe",
            "bilateral_clahe",
            "unsharp_clahe"
        ]

        palette_enum = PaletteType(payload.palette) if payload.palette in [p.value for p in PaletteType] else PaletteType.AMBER
        results = []

        for m in methods_to_run:
            enh_res, _ = manager.improve_sonar_image(raw_img, method=m, palette=palette_enum.value)
            display_bgr = apply_palette(enh_res.canonical_image, palette=palette_enum)

            enl = compute_enl(enh_res.canonical_image)
            epi = compute_epi(raw_img, enh_res.canonical_image)

            cnr_list = []
            for b in boxes:
                bbox_norm = (b[1], b[2], b[3], b[4])
                c_res = compute_cnr(enh_res.canonical_image, bbox_xywh_norm=bbox_norm)
                if c_res.status == MetricStatus.VALID and c_res.value is not None:
                    cnr_list.append(c_res.value)

            mean_cnr = round(float(np.mean(cnr_list)), 3) if cnr_list else None

            results.append({
                "method": m,
                "execution_time_ms": enh_res.execution_time_ms,
                "thumbnail_data_url": _encode_png_base64(display_bgr),
                "metrics": {
                    "enl": enl.value,
                    "epi": epi.value,
                    "cnr": mean_cnr
                }
            })

        return {
            "success": True,
            "palette": palette_enum.value,
            "comparisons": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-improved")
async def detect_on_improved_image(payload: DetectImprovedRequest, db: AsyncSession = Depends(get_db)):
    """
    Experimental endpoint: Runs the frozen production YOLOv8 detector directly
    on the enhanced canonical grayscale matrix.
    Results are strictly tagged as 'ENHANCED-INPUT INFERENCE'.
    """
    try:
        from backend.ml.detector.yolo_detector import YOLOv8Detector

        # Resolve image
        if payload.image_name:
            safe_name = Path(payload.image_name).name
            samples = loader.get_development_samples(
                dataset_version=payload.dataset_version or "v3",
                split=payload.split or "val"
            )
            matched = next((s for s in samples if s["image_name"] == safe_name), None)
            if not matched:
                raise HTTPException(status_code=404, detail="Image not found")
            raw_img = loader.load_image_float32(matched["image_path"])
        else:
            sample = loader.get_smoke_test_sample()
            raw_img = loader.load_image_float32(sample["image_path"])

        # 1. Enhance
        enh_res, telemetry = manager.improve_sonar_image(
            raw_img,
            method=payload.method or "auto",
            profile=payload.profile or "BALANCED"
        )
        enhanced_gray = enh_res.canonical_image

        # 2. Run detector on raw vs enhanced
        detector = YOLOv8Detector()
        conf_thr = payload.conf_threshold or 0.25

        raw_dets = detector.predict([raw_img], conf_threshold=conf_thr)
        enh_dets = detector.predict([enhanced_gray], conf_threshold=conf_thr)

        raw_list = raw_dets[0] if raw_dets else []
        enh_list = enh_dets[0] if enh_dets else []

        return {
            "success": True,
            "experiment_tag": "ENHANCED-INPUT INFERENCE",
            "production_checkpoint": "sonar_yolov8_fls_trained.pt (PROD)",
            "enhancement_method": enh_res.method.value,
            "raw_detection_count": len(raw_list),
            "enhanced_detection_count": len(enh_list),
            "raw_detections": [
                {"class_name": d.class_name, "confidence": d.confidence, "bbox": [d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h]}
                for d in raw_list
            ],
            "enhanced_detections": [
                {"class_name": d.class_name, "confidence": d.confidence, "bbox": [d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h]}
                for d in enh_list
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class InspectRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    image_data_url: Optional[str] = None


class PipelineProcessRequest(BaseModel):
    dataset_version: Optional[str] = "v3"
    split: Optional[str] = "val"
    image_name: Optional[str] = None
    survey_id: Optional[str] = None
    image_data_url: Optional[str] = None
    profile: Optional[str] = "BALANCED"
    mode: Optional[str] = "AI_SAFE"
    palette: Optional[str] = "amber"
    custom_parameters: Optional[Dict[str, Any]] = None
    run_detection: Optional[bool] = False
    conf_threshold: Optional[float] = 0.25


@router.post("/inspect")
async def inspect_image_endpoint(payload: InspectRequest):
    """
    Performs forensic inspection of sonar input:
    Extracts dynamic range, bit depth, dead columns, saturation ratio, and detects FLS vs SSS.
    """
    try:
        from backend.enhancement.inspection import inspect_sonar_input

        if payload.image_data_url:
            raw_img = _decode_png_base64(payload.image_data_url)
        elif payload.image_name:
            safe_name = Path(payload.image_name).name
            samples = loader.get_development_samples(
                dataset_version=payload.dataset_version or "v3",
                split=payload.split or "val",
            )
            matched = next((s for s in samples if s["image_name"] == safe_name), None)
            if not matched:
                raise HTTPException(status_code=404, detail="Image not found")
            raw_img = loader.load_image_float32(matched["image_path"])
        else:
            sample = loader.get_smoke_test_sample()
            raw_img = loader.load_image_float32(sample["image_path"])

        report = inspect_sonar_input(raw_img)
        return {
            "success": True,
            "report": report.to_dict(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pipeline/process")
async def process_modular_pipeline(payload: PipelineProcessRequest):
    """
    Executes the modular 9-stage Sonar Enhancement Pipeline.
    Supports HUMAN_DISPLAY and AI_SAFE modes with mask propagation and comprehensive metrics.
    """
    try:
        from backend.enhancement.pipeline_base import (
            SonarEnhancementContext,
            ProcessingMode,
            Modality,
            SignalRepresentation,
            SonarEnhancementProvenance,
        )
        from backend.enhancement.inspection import inspect_sonar_input
        from backend.enhancement.profiles import build_pipeline_for_profile
        from backend.enhancement.quality_metrics import evaluate_enhancement_quality

        # 1. Resolve raw input image
        artifact_id = payload.image_name or "uploaded_image"
        if payload.image_data_url:
            raw_img = _decode_png_base64(payload.image_data_url)
            artifact_id = f"upload_{uuid.uuid4().hex[:8]}"
        elif payload.image_name:
            safe_name = Path(payload.image_name).name
            samples = loader.get_development_samples(
                dataset_version=payload.dataset_version or "v3",
                split=payload.split or "val",
            )
            matched = next((s for s in samples if s["image_name"] == safe_name), None)
            if not matched:
                raise HTTPException(status_code=404, detail="Image not found")
            raw_img = loader.load_image_float32(matched["image_path"])
        else:
            sample = loader.get_smoke_test_sample()
            raw_img = loader.load_image_float32(sample["image_path"])

        # 2. Inspect input
        inspection = inspect_sonar_input(raw_img)

        # 3. Setup context and pipeline
        mode = ProcessingMode.HUMAN_DISPLAY if (payload.mode and "HUMAN" in payload.mode.upper()) else ProcessingMode.AI_SAFE
        profile_name = payload.profile or "BALANCED"
        pipeline = build_pipeline_for_profile(profile_name, mode=mode, custom_params=payload.custom_parameters)

        context = SonarEnhancementContext(
            artifact_id=artifact_id,
            modality=inspection.modality,
            representation=inspection.detected_representation,
            mode=mode,
            metadata={"raw_image": raw_img},
            provenance=SonarEnhancementProvenance(
                source_artifact_id=artifact_id,
                modality=inspection.modality,
                input_representation=inspection.detected_representation,
                output_representation=SignalRepresentation.NORMALIZED_FLOAT,
                timestamp_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            ),
        )

        # 4. Execute pipeline
        result = pipeline.execute(raw_img, context)

        # 5. Format display image with palette
        palette_enum = PaletteType(payload.palette or "amber")
        display_rgb = apply_palette(result.canonical_image, palette_enum)
        raw_display_rgb = apply_palette(raw_img, palette_enum)

        # 6. Evaluate comprehensive metrics
        quality_metrics = evaluate_enhancement_quality(raw_img, result.canonical_image)

        # 7. Encode masks
        validity_mask_u8 = (result.validity_mask.astype(np.uint8) * 255) if result.validity_mask is not None else None
        modified_mask_u8 = (result.modified_mask.astype(np.uint8) * 255) if result.modified_mask is not None else None

        # 8. Optional YOLO detection
        detections_res = None
        if payload.run_detection:
            from backend.ml.detector.yolo_detector import YOLOv8Detector
            detector = YOLOv8Detector()
            conf = payload.conf_threshold or 0.25
            raw_dets = detector.predict([raw_img], conf_threshold=conf)
            enh_dets = detector.predict([result.canonical_image], conf_threshold=conf)
            detections_res = {
                "raw_count": len(raw_dets[0]) if raw_dets else 0,
                "enhanced_count": len(enh_dets[0]) if enh_dets else 0,
                "raw_detections": [
                    {"class_name": d.class_name, "confidence": d.confidence, "bbox": [d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h]}
                    for d in (raw_dets[0] if raw_dets else [])
                ],
                "enhanced_detections": [
                    {"class_name": d.class_name, "confidence": d.confidence, "bbox": [d.bbox_x, d.bbox_y, d.bbox_w, d.bbox_h]}
                    for d in (enh_dets[0] if enh_dets else [])
                ],
            }

        return {
            "success": True,
            "artifact_id": artifact_id,
            "profile": profile_name,
            "mode": mode.value,
            "palette": palette_enum.value,
            "is_ai_safe": result.is_ai_safe,
            "raw_image_url": _encode_png_base64(raw_display_rgb),
            "raw_grayscale_url": _encode_png_base64((raw_img * 255).astype(np.uint8)),
            "enhanced_image_url": _encode_png_base64(display_rgb),
            "enhanced_canonical_url": _encode_png_base64((result.canonical_image * 255).astype(np.uint8)),
            "validity_mask_url": _encode_png_base64(validity_mask_u8) if validity_mask_u8 is not None else None,
            "modified_mask_url": _encode_png_base64(modified_mask_u8) if modified_mask_u8 is not None else None,
            "applied_stages": result.applied_stages,
            "skipped_stages": result.skipped_stages,
            "warnings": result.warnings,
            "stage_metrics": result.metrics,
            "quality_metrics": quality_metrics,
            "inspection": inspection.to_dict(),
            "execution_time_ms": result.execution_time_ms,
            "detections": detections_res,
            "provenance": {
                "source_artifact_id": result.provenance.source_artifact_id if result.provenance else artifact_id,
                "modality": result.provenance.modality.value if result.provenance else inspection.modality.value,
                "applied_stages": result.applied_stages,
                "skipped_stages": result.skipped_stages,
                "execution_time_ms": result.execution_time_ms,
                "software_version": "1.0.0",
                "device": "cpu",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics/definitions")
async def get_metrics_definitions():
    """Returns documentation of all acoustic and safety metrics."""
    from backend.enhancement.metric_definitions import METRIC_DEFINITIONS
    return {
        "success": True,
        "metrics": METRIC_DEFINITIONS,
    }

