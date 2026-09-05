from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x: float = Field(..., description="Top-left X pixel coordinate or normalized X")
    y: float = Field(..., description="Top-left Y pixel coordinate or normalized Y")
    width: float = Field(..., description="Bounding box width")
    height: float = Field(..., description="Bounding box height")

class SingleDetectionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBox
    confidence_calibrated: Optional[float] = None
    is_filtered: bool = False
    filtered_reason: Optional[str] = None

class InferenceResponseData(BaseModel):
    model_id: str
    checkpoint_path: str
    checkpoint_sha256: str
    is_production_checkpoint: bool
    inference_time_ms: float
    preprocessing_time_ms: float
    postprocessing_time_ms: float
    total_time_ms: float
    device: str
    detections: List[SingleDetectionResult]
    detection_count: int
    operating_thresholds: Dict[str, float]
    provenance: Dict[str, Any]
