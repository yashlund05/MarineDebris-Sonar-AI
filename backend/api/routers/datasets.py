import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from backend.services.dataset_service import DatasetService, get_dataset_service

router = APIRouter(tags=["Datasets"])

@router.get("/datasets")
async def list_datasets(request: Request, service: DatasetService = Depends(get_dataset_service)):
    data = service.list_datasets()
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

@router.get("/datasets/canonical-status")
async def get_canonical_status(request: Request, service: DatasetService = Depends(get_dataset_service)):
    data = service.get_canonical_status()
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

@router.get("/datasets/{version}")
async def get_dataset_detail(version: str, request: Request, service: DatasetService = Depends(get_dataset_service)):
    data = service.get_dataset_detail(version)
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

@router.get("/datasets/{version}/summary")
async def get_dataset_summary(version: str, request: Request, service: DatasetService = Depends(get_dataset_service)):
    data = service.get_dataset_summary(version)
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }

@router.get("/datasets/{version}/manifest")
async def get_dataset_manifest(version: str, request: Request, service: DatasetService = Depends(get_dataset_service)):
    data = service.get_manifest(version)
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
