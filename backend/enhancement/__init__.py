"""
Intelligent Sonar Image Enhancement & Visibility Engine.
"""

from backend.enhancement.types import (
    EnhancementMethod,
    PaletteType,
    ProfileName,
    PromotionStatus,
    MetricStatus,
    MetricResult,
    EnhancementResult,
    BenchmarkRecord,
)
from backend.enhancement.pipeline_base import (
    Modality,
    SignalRepresentation,
    ProcessingMode,
    SonarEnhancementStage,
    SonarEnhancementPipeline,
    SonarEnhancementContext,
    SonarEnhancementResult,
    SonarEnhancementProvenance,
)
from backend.enhancement.inspection import (
    SonarInspectionReport,
    inspect_sonar_input,
)
from backend.enhancement.signal_domain import (
    amplitude_to_db,
    power_to_db,
    db_to_linear_power,
    safe_percentile_normalization,
    robust_dynamic_range_estimation,
)
from backend.enhancement.quality_metrics import (
    evaluate_enhancement_quality,
)
from backend.enhancement.profiles import (
    StandardProfile,
    build_pipeline_for_profile,
    list_profiles,
    get_profile_info,
)

__all__ = [
    "EnhancementMethod",
    "PaletteType",
    "ProfileName",
    "PromotionStatus",
    "MetricStatus",
    "MetricResult",
    "EnhancementResult",
    "BenchmarkRecord",
    "Modality",
    "SignalRepresentation",
    "ProcessingMode",
    "SonarEnhancementStage",
    "SonarEnhancementPipeline",
    "SonarEnhancementContext",
    "SonarEnhancementResult",
    "SonarEnhancementProvenance",
    "SonarInspectionReport",
    "inspect_sonar_input",
    "amplitude_to_db",
    "power_to_db",
    "db_to_linear_power",
    "safe_percentile_normalization",
    "robust_dynamic_range_estimation",
    "evaluate_enhancement_quality",
    "StandardProfile",
    "build_pipeline_for_profile",
    "list_profiles",
    "get_profile_info",
]
