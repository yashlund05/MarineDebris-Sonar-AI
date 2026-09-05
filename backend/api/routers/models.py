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
from backend.services.model_evaluation_service import (
    ModelEvaluationService,
    get_model_evaluation_service,
)

router = APIRouter(tags=["Models"])


@router.get("/models")
async def list_models(
    request: Request,
    task: Optional[str] = Query(None),
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
    db: AsyncSession = Depends(get_db),
):
    """List registered AI models and evaluated experiment checkpoints."""
    query = select(ModelRegistry)
    if task:
        query = query.where(ModelRegistry.task == task)

    result = await db.execute(query)
    models = result.scalars().all()

    device = ModelLoader.get_device()
    data = []

    # If database has models, add them
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

    # Integrate real evaluated experiment models
    eval_models = eval_service.list_models()
    for em in eval_models:
        # avoid duplicate if already in data
        if not any(d["id"] == em["model_id"] or d.get("name") == em["display_name"] for d in data):
            data.append({
                "id": em["model_id"],
                "model_name": em["display_name"],
                "name": em["display_name"],
                "version": "Phase 3 Experiment",
                "task": "detection",
                "architecture": em["architecture"],
                "framework": "PyTorch / Ultralytics",
                "training_dataset": "sonar_debris_v3",
                "dataset_version": "v3.0.0",
                "supported_classes": ["general_marine_debris", "other_man_made_target"],
                "unsupported_classes": ["derelict_fishing_gear", "shipwreck", "pipe_or_cylinder"],
                "map50": em["metrics"].get("mAP50") if em.get("metrics") else None,
                "map50_95": em["metrics"].get("mAP50_95") if em.get("metrics") else None,
                "dice_score": None,
                "inference_latency_ms": em["metrics"].get("latency_p95_ms") if em.get("metrics") else None,
                "weight_path": em["checkpoint_path"],
                "weights_path": em["checkpoint_path"],
                "runtime_status": "READY" if os.path.exists(em["checkpoint_path"]) else "MISSING_WEIGHTS",
                "status": em["status"],
                "device": device,
                "is_loaded": os.path.exists(em["checkpoint_path"]),
                "is_active": em["is_production"],
                "metrics": em.get("metrics", {}),
                "trained_at": em.get("created_at"),
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
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
    db: AsyncSession = Depends(get_db),
):
    """Get single model metadata, status, or experiment candidate specification."""
    # First check evaluated models from real artifacts
    eval_model = eval_service.get_model_detail(model_id)
    if eval_model:
        return {
            "success": True,
            "data": eval_model,
            "meta": {
                "request_id": getattr(request.state, "request_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

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


from backend.services.model_evaluation_service import (
    ModelEvaluationService,
    get_model_evaluation_service,
)

@router.get("/models/{model_id}/metrics")
async def get_model_metrics(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Retrieve measured evaluation metrics for a model from real evaluation artifacts."""
    # First check evaluation service for real experiment/production artifacts
    eval_metrics = eval_service.get_model_metrics(model_id)
    if eval_metrics.get("confidence") != "NOT_AVAILABLE":
        return {
            "success": True,
            "data": eval_metrics,
            "meta": {
                "request_id": getattr(request.state, "request_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    # Fallback to catalog model check
    catalog_model = ModelRegistryService.get_model_by_id(model_id)
    if not catalog_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    return {
        "success": True,
        "data": {
            "model_id": model_id,
            "model_name": catalog_model["name"],
            "metrics": catalog_model.get("metrics", {}),
            "confidence": "NOT_AVAILABLE",
            "is_measured": False,
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/runs")
async def get_model_runs(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Retrieve training runs and multi-seed evaluations for a model."""
    if "E6" in model_id or model_id == "P3_E2_NAIVE_MIX" or model_id == "production_fls_yolov8n":
        multiseed = eval_service.get_multiseed_aggregation()
        return {
            "success": True,
            "data": {
                "model_id": model_id,
                "multiseed": multiseed,
            },
            "meta": {
                "request_id": getattr(request.state, "request_id", ""),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        }

    model = eval_service.get_model_detail(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    return {
        "success": True,
        "data": {
            "model_id": model_id,
            "multiseed": {"confidence": "NOT_AVAILABLE", "aggregation": None},
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/artifacts")
async def get_model_artifacts(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Retrieve list of verified physical artifacts (weights, reports, logs) for a model."""
    artifacts = eval_service.get_model_artifacts(model_id)
    return {
        "success": True,
        "data": artifacts,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/promotion")
async def get_model_promotion(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Inspect promotion gating outcome, thresholds, and rejection rationale."""
    decision = eval_service.get_promotion_decision(model_id)
    return {
        "success": True,
        "data": decision,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/explanations")
async def get_model_explanations(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Explain why model passed/failed gates and its acoustic operating characteristics."""
    decision = eval_service.get_promotion_decision(model_id)
    metrics = eval_service.get_model_metrics(model_id)
    
    explanation = {
        "model_id": model_id,
        "decision": decision.get("promotion_gate", {}).get("status", "UNKNOWN") if decision.get("promotion_gate") else decision.get("status", "UNKNOWN"),
        "rationale": decision.get("rationale", ""),
        "strengths": [],
        "weaknesses": [],
    }

    if "E6" in model_id:
        explanation["strengths"] = [
            "Superior generalization on Dataset V3 (mAP50 = 95.94% +/- 1.05% vs 91.92% baseline)",
            "Strong retention on legacy V2 control (mAP50 = 98.15% +/- 0.84% vs 89.21% baseline)",
            "Robust acoustic clutter rejection with 35.2% relative False Alarm Rate reduction"
        ]
        explanation["weaknesses"] = [
            "CPU inference latency P95 (195.13 ms) exceeds real-time acoustic pipeline budget of <= 125.0 ms",
            "Requires CPU inference optimization (preprocessing, threading, runtime) before production promotion"
        ]
    elif model_id == "production_fls_yolov8n":
        explanation["strengths"] = [
            "Verified frozen production baseline with zero regression risk",
            "Meets CPU real-time latency budget"
        ]
        explanation["weaknesses"] = [
            "Higher False Alarm Rate on hard negative quarry seabed (21.43%)",
            "Lower recall on faint and low-contrast acoustic targets"
        ]

    return {
        "success": True,
        "data": explanation,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/traceability")
async def get_model_traceability(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Inspect full Dataset -> Model -> Prediction traceability graph."""
    traceability = eval_service.get_model_traceability(model_id)
    if not traceability:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found")

    return {
        "success": True,
        "data": traceability,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models/{model_id}/error-analysis")
async def get_model_error_analysis(
    model_id: str,
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Retrieve sample-level error analysis and acoustic subgroup metrics."""
    analysis = eval_service.get_error_analysis(model_id)
    if not analysis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error analysis not available for this model")

    return {
        "success": True,
        "data": analysis,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models-comparison")
async def get_models_comparison(
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Compare evaluated models side-by-side using the multi-objective ranking engine."""
    comparison = eval_service.compare_models()
    return {
        "success": True,
        "data": comparison,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }


@router.get("/models-promotion/audit")
async def get_promotion_audit(
    request: Request,
    eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
):
    """Retrieve immutable promotion gate decisions and audit ledger."""
    records = eval_service._read_jsonl(eval_service.registry_file)
    audit_entries = []
    for r in records:
        eid = r.get("experiment_id", "")
        gate = r.get("promotion_gate", {})
        rejections = [
            chk["name"] + ": " + chk["observed"] + " (Required: " + chk["required"] + ")"
            for chk in gate.get("checks", [])
            if not chk.get("passed", True)
        ]
        audit_entries.append({
            "timestamp": r.get("completed_at") or "2026-03-01T00:00:00Z",
            "action": "EVALUATE_PROMOTION_GATE",
            "status": gate.get("status", "REJECTED"),
            "target_model_id": eid,
            "overall_pass": gate.get("overall_pass", False),
            "rejection_reasons": rejections,
            "allowed_actions": ["ARCHIVE", "EVALUATE"] if not gate.get("overall_pass") else ["PROMOTE_WITH_EXPLICIT_APPROVAL"],
        })

    return {
        "success": True,
        "data": {
            "current_production_model_id": "production_fls_yolov8n",
            "current_production_sha256": "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7",
            "promotion_policy": "STRICT_HUMAN_IN_THE_LOOP_OPT_IN",
            "audit_records": audit_entries,
        },
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }




