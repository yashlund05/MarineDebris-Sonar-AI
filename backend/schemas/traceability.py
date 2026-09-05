from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LineageEvent(BaseModel):
    timestamp: str
    stage: str  # 'dataset_curation', 'training', 'benchmark_eval', 'inference'
    description: str
    artifact_hash: Optional[str] = None
    confidence: str

class ModelTraceabilityResponse(BaseModel):
    model_id: str
    display_name: str
    dataset_version: str
    dataset_manifest_path: str
    dataset_sha256: Optional[str] = None
    training_split: Dict[str, Any]
    checkpoint_path: str
    checkpoint_sha256: str
    evaluation_manifest: str
    lineage_graph: List[LineageEvent]
