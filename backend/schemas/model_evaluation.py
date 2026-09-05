from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field


class MetricEntry(BaseModel):
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1: Optional[float] = None
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    far: Optional[float] = None
    fnr: Optional[float] = None
    false_positive_count: Optional[int] = None
    false_negative_count: Optional[int] = None
    latency_mean_ms: Optional[float] = None
    latency_p50_ms: Optional[float] = None
    latency_p95_ms: Optional[float] = None
    latency_p99_ms: Optional[float] = None
    throughput: Optional[float] = None
    confidence_threshold: Optional[float] = None
    iou_threshold: Optional[float] = None
    evaluation_split: Optional[str] = None
    dataset_version: Optional[str] = None


class PromotionGateCheck(BaseModel):
    name: str
    required: str
    observed: str
    passed: bool


class PromotionGateResult(BaseModel):
    status: str  # e.g., 'REJECTED', 'ELIGIBLE_FOR_PROMOTION', 'NOT_EVALUATED'
    overall_pass: bool
    promotion_eligible: bool
    checks: List[PromotionGateCheck] = []
    recommendation: Optional[str] = None


class MultiSeedStats(BaseModel):
    mean: float
    std: float
    min: float
    max: float
    values: List[float] = []
    ci_95: Optional[List[float]] = None
    sample_size_note: Optional[str] = None


class MultiSeedAggregation(BaseModel):
    seeds: List[int]
    number_of_seeds: int
    v2_mAP50: MultiSeedStats
    v2_recall: MultiSeedStats
    v3_mAP50: MultiSeedStats
    v3_recall: MultiSeedStats
    hard_negatives_FAR: MultiSeedStats
    total_false_positive_boxes: MultiSeedStats
    stability_passed: bool
    best_seed: int
    best_checkpoint: str


class ExperimentRunSummary(BaseModel):
    experiment_id: str
    experiment_name: str
    strategy: str
    seed: Optional[int] = None
    checkpoint_path: str
    checkpoint_sha256: Optional[str] = None
    status: str
    metrics: Dict[str, Any] = {}
    promotion_gate: Optional[PromotionGateResult] = None


class RegisteredModel(BaseModel):
    model_id: str
    display_name: str
    model_family: str
    architecture: str
    dataset_versions: List[str] = []
    experiment_id: Optional[str] = None
    strategy: Optional[str] = None
    checkpoint_path: str
    checkpoint_sha256: Optional[str] = None
    created_at: Optional[str] = None
    status: str  # 'production', 'candidate', 'experimental', 'rejected'
    is_production: bool = False
    metrics: Optional[Dict[str, Any]] = None
