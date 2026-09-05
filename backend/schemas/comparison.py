from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class ModelComparisonEntry(BaseModel):
    model_id: str
    display_name: str
    is_production: bool
    v2_map50: Optional[float] = None
    v2_recall: Optional[float] = None
    v3_map50: Optional[float] = None
    v3_recall: Optional[float] = None
    negative_far: Optional[float] = None
    total_fp_boxes: Optional[int] = None
    small_target_recall: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    fps: Optional[float] = None
    composite_score: Optional[float] = None
    rank: Optional[int] = None
    promotion_status: str

class ModelComparisonResponse(BaseModel):
    baseline_model_id: str
    compared_models: List[ModelComparisonEntry]
    weighting_schema: Dict[str, float]
