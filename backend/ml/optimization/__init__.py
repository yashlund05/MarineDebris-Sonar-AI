"""
MarineDebris-Sonar-AI: Phase 3 Optimization Framework
Provides balanced multi-source training, hard-negative/positive sampling,
benchmark evaluations, candidate ranking, and production promotion governance.
"""

from backend.ml.optimization.experiment_contract import ExperimentContract
from backend.ml.optimization.experiment_registry import ExperimentRegistry, OptimizationRecord
from backend.ml.optimization.promotion_gate import PromotionGate, PromotionResult

__all__ = [
    "ExperimentContract",
    "ExperimentRegistry",
    "OptimizationRecord",
    "PromotionGate",
    "PromotionResult",
]
