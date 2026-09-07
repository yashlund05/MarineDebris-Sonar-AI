"""
Core data structures and type definitions for the Sonar Enhancement Engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
import numpy as np


class EnhancementMethod(str, Enum):
    IDENTITY = "identity"
    PERCENTILE_NORM = "percentile_normalize"
    GAMMA_CORRECT = "gamma_correct"
    CLAHE = "clahe_enhance"
    MEDIAN_CLAHE = "median_clahe"
    BILATERAL_CLAHE = "bilateral_clahe"
    UNSHARP_CLAHE = "unsharp_clahe"
    LOG_BILATERAL_CLAHE = "log_bilateral_clahe"


class PaletteType(str, Enum):
    GRAYSCALE = "grayscale"
    AMBER = "amber"
    THERMAL = "thermal"
    INFERNO = "inferno"


class ProfileName(str, Enum):
    BALANCED = "BALANCED"
    LOW_SNR = "LOW_SNR"
    HIGH_CONTRAST = "HIGH_CONTRAST"
    HEAVY_CLUTTER = "HEAVY_CLUTTER"
    LONG_RANGE = "LONG_RANGE"
    HUMAN_INSPECTION = "HUMAN_INSPECTION"
    DETECTION_OPTIMIZED = "DETECTION_OPTIMIZED"


class PromotionStatus(str, Enum):
    PRODUCTION_DISPLAY_ENHANCER = "PRODUCTION DISPLAY ENHANCER"
    DETECTION_PREPROCESSOR_CANDIDATE = "DETECTION PREPROCESSOR CANDIDATE"
    HUMAN_INSPECTION_ONLY = "HUMAN-INSPECTION ONLY"
    EXPERIMENTAL = "EXPERIMENTAL"
    REJECTED = "REJECTED"


class MetricStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NOT_MEASURABLE = "NOT MEASURABLE"


@dataclass
class MetricResult:
    """Individual acoustic metric measurement with validity conditions."""
    name: str
    value: Optional[float]
    status: MetricStatus
    unit: str
    formula: str
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EnhancementResult:
    """Canonical enhancement output (float32 [0, 1] grayscale) with metadata."""
    canonical_image: np.ndarray  # Single-channel float32 [0, 1]
    method: EnhancementMethod
    parameters: Dict[str, Any]
    execution_time_ms: float
    profile_used: Optional[ProfileName] = None
    metrics: Dict[str, MetricResult] = field(default_factory=dict)
    
    def __post_init__(self):
        # Strict validation: Canonical output must always be float32 in range [0, 1]
        if self.canonical_image.size > 0:
            if self.canonical_image.ndim != 2:
                raise ValueError(f"Canonical enhanced image must be 2D single-channel, got shape {self.canonical_image.shape}")
            if self.canonical_image.dtype != np.float32:
                self.canonical_image = self.canonical_image.astype(np.float32)


@dataclass
class BenchmarkRecord:
    """Record for EXPERIMENT_REGISTRY.jsonl and methodology audit."""
    dataset_version: str
    split: str
    sequence_policy: str
    image_name: str
    method: str
    parameters: Dict[str, Any]
    execution_time_ms: float
    metrics: Dict[str, Any]
    timestamp: str
