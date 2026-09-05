"""
MarineDebris-Sonar-AI: Model Optimization and Controlled Experiment Framework
Provides auditable, reproducible, leakage-free experiment orchestration,
multi-benchmark evaluation, threshold calibration, and production promotion governance.
"""

from .config import ExperimentConfig, PromotionCriteria, verify_production_lock
from .registry import ExperimentRegistry, ExperimentRecord
from .evaluator import MultiBenchmarkEvaluator
from .runner import ExperimentRunner
from .calibration import ThresholdCalibrator
from .comparison import ModelComparisonDashboard

__all__ = [
    "ExperimentConfig",
    "PromotionCriteria",
    "verify_production_lock",
    "ExperimentRegistry",
    "ExperimentRecord",
    "MultiBenchmarkEvaluator",
    "ExperimentRunner",
    "ThresholdCalibrator",
    "ModelComparisonDashboard",
]
