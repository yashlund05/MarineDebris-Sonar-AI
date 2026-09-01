import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_db
from backend.database.models import ModelRegistry

router = APIRouter(tags=["Models"])

@router.get("/models")
async def list_models(
    request: Request,
    task: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List registered AI models."""
    query = select(ModelRegistry)
    if task:
        query = query.where(ModelRegistry.task == task)
        
    result = await db.execute(query)
    models = result.scalars().all()
    
    data = []
    for m in models:
        data.append({
            "id": m.id,
            "model_name": m.model_name,
            "version": m.version,
            "task": m.task,
            "architecture": m.architecture,
            "training_dataset": m.training_dataset,
            "map50": m.map50,
            "map50_95": m.map50_95,
            "dice_score": m.dice_score,
            "inference_latency_ms": m.inference_latency_ms,
            "is_active": m.is_active,
            "trained_at": m.trained_at,
            "registered_at": m.registered_at
        })
        
    return {
        "success": True,
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", ""),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    }
