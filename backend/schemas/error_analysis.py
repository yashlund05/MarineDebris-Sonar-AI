from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class SubgroupMetric(BaseModel):
    total_gt: int
    detected: int
    recall: float
    mean_tp_confidence: float

class ErrorAnalysisResponse(BaseModel):
    model_id: str
    dataset_version: str
    total_gt_boxes: int
    total_true_positives: int
    overall_recall: float
    subgroups: Dict[str, SubgroupMetric]
    false_alarm_profile: Dict[str, Any]
    error_breakdown_notes: List[str]
