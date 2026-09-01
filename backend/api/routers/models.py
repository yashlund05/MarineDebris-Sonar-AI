import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.database.models import ModelRegistry
from backend.inference.model_loader import ModelLoader
from backend.ml.registry.model_registry import ModelRegistryService

router = APIRouter(tags=["Models"])


@router.get("/models")
async def list_models(
    request: Request,
    task: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List registered AI models with verified runtime weight status and supported classes."""
    query = select(ModelRegistry)
    if task:
        query = query.where(ModelRegistry.task == task)

    result = await db.execute(query)
    models = result.scalars().all()

    device = ModelLoader.get_device()
    data = []

    # If database has models, use them; otherwise pull from verified catalog service
    if models:
        for m in models:
            weight_status = ModelLoader.get_model_status(m.weight_path)
            data.append({
                "id": str(m.id),
                "model_name": m.model_name,
                "name": m.model_name,
                "version": m.version,
                "task": m.task,
                "architecture": m.architecture,
                "framework": getattr(m, "framework", "PyTorch / Ultralytics"),
                "training_dataset": m.training_dataset,
                "dataset_version": getattr(m, "dataset_version", "v1.0.0"),
                "supported_classes": getattr(m, "supported_classes", ["general_marine_debris", "other_man_made_target"]),
                "unsupported_classes": ["derelict_fishing_gear", "shipwreck", "pipe_or_cylinder"],
                "map50": m.map50,
                "map50_95": m.map50_95,
                "dice_score": m.dice_score,
                "inference_latency_ms": m.inference_latency_ms,
                "weight_path": m.weight_path,
                "weights_path": m.weight_path,
                "runtime_status": weight_status["state"],
                "status": weight_status["state"],
                "device": device,
                "is_loaded": weight_status["is_loaded"],
                "is_active": m.is_active and weight_status["is_loaded"],
                "metrics": getattr(m, "metrics", {
                    "map50": m.map50,
                    "map50_95": m.map50_95,
                    "dice_score": m.dice_score,
                }),
                "trained_at": m.trained_at,
                "registered_at": m.registered_at,
            })
    else:
        # Fallback to catalog service
        catalog_models = ModelRegistryService.list_catalog(task=task)
        for cm in catalog_models:
            data.append({
                "id": cm["id"],
                "model_name": cm["name"],
                "name": cm["name"],
                "version": cm["version"],
                "task": cm["task"],
                "architecture": cm["architecture"],
                "framework": cm["framework"],
                "training_dataset": cm["dataset"],
                "dataset_version": cm["dataset_version"],
                "supported_classes": cm["supported_classes"],
                "unsupported_classes": cm["unsupported_classes"],
                "map50": cm["metrics"].get("mAP50"),
                "map50_95": cm["metrics"].get("mAP50_95"),
                "dice_score": cm["metrics"].get("dice_score"),
                "inference_latency_ms": None,
                "weight_path": cm["weights_path"],
                "weights_path": cm["weights_path"],
                "runtime_status": cm["status"],
                "status": cm["status"],
                "device": device,
                "is_loaded": cm["is_loaded"],
                "is_active": cm["is_active"],
                "metrics": cm["metrics"],
                "trained_at": None,
                "registered_at": datetime.now(timezone.utc).isoformat(),
            })

    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}")
async def get_model(
    model_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Get single model metadata and truthful status."""
    catalog_model = ModelRegistryService.get_model_by_id(model_id)
    if catalog_model:
        return {
            "success": True,
            "data": catalog_model,
            "meta": {
                "request_id": getattr(request.state, "request_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    # Search in DB
    try:
        parsed_id = uuid.UUID(model_id)
        result = await db.execute(select(ModelRegistry).where(ModelRegistry.id == parsed_id))
        m = result.scalar_one_or_none()
        if m:
            weight_status = ModelLoader.get_model_status(m.weight_path)
            return {
                "success": True,
                "data": {
                    "id": str(m.id),
                    "model_name": m.model_name,
                    "version": m.version,
                    "task": m.task,
                    "architecture": m.architecture,
                    "framework": getattr(m, "framework", "PyTorch / Ultralytics"),
                    "status": weight_status["state"],
                    "weights_path": m.weight_path,
                    "supported_classes": getattr(m, "supported_classes", ["general_marine_debris", "other_man_made_target"]),
                },
                "meta": {
                    "request_id": getattr(request.state, "request_id", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }
    except ValueError:
        pass

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")


@router.get("/models/{model_id}/health")
async def get_model_health(
    model_id: str,
    request: Request,
):
    """Inspect truthful health of a specific model."""
    catalog_model = ModelRegistryService.get_model_by_id(model_id)
    if not catalog_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    status_code = catalog_model["status"]
    return {
        "success": True,
        "data": {
            "model_id": model_id,
            "model_name": catalog_model["name"],
            "status": status_code,
            "is_ready": status_code in ("READY", "PRODUCTION_READY"),
            "device": catalog_model["device"],
            "weights_path": catalog_model["weights_path"],
            "supported_classes": catalog_model["supported_classes"],
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/metrics")
async def get_model_metrics(
    model_id: str,
    request: Request,
):
    """Retrieve measured evaluation metrics for a model."""
    catalog_model = ModelRegistryService.get_model_by_id(model_id)
    if not catalog_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    return {
        "success": True,
        "data": {
            "model_id": model_id,
            "model_name": catalog_model["name"],
            "metrics": catalog_model.get("metrics", {}),
            "is_measured": False,  # Truthful indicator that metrics require verified training
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }
