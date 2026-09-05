"""
MarineDebris-Sonar-AI: Canonical Evaluation Package.
Establishes immutable evaluation standards, contracts, and benchmark reproduction.
"""

from backend.ml.evaluation.evaluation_contract import (
    EvaluationContract,
    CANONICAL_BENCHMARK_CONF,
    CANONICAL_BENCHMARK_IOU,
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
    CANONICAL_IMAGE_SIZE,
    get_canonical_eval_args,
)

__all__ = [
    "EvaluationContract",
    "CANONICAL_BENCHMARK_CONF",
    "CANONICAL_BENCHMARK_IOU",
    "OPERATIONAL_MISSION_CONF",
    "OPERATIONAL_MISSION_IOU",
    "CANONICAL_IMAGE_SIZE",
    "get_canonical_eval_args",
]
