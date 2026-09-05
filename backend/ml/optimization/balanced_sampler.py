"""
MarineDebris-Sonar-AI: Domain-Balanced Sampler
Calculates sampling distributions across V2 legacy positive, V3 real positive,
and verified negative backgrounds to prevent domain collapse.
"""

from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class DomainWeights:
    v2_legacy: float = 0.35
    v3_positive: float = 0.50
    v3_negative: float = 0.15

    def validate(self):
        total = self.v2_legacy + self.v3_positive + self.v3_negative
        if abs(total - 1.0) > 1e-4:
            raise ValueError(f"Domain weights must sum to 1.0, got {total}")


class BalancedSampler:
    def __init__(self, weights: DomainWeights = DomainWeights()):
        weights.validate()
        self.weights = weights

    def get_split_counts(self, total_target_images: int) -> Dict[str, int]:
        n_v2 = int(total_target_images * self.weights.v2_legacy)
        n_v3_pos = int(total_target_images * self.weights.v3_positive)
        n_neg = total_target_images - n_v2 - n_v3_pos
        return {
            "v2_legacy": n_v2,
            "v3_positive": n_v3_pos,
            "v3_negative": n_neg,
        }
