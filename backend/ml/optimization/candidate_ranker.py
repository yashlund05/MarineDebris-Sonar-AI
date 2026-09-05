"""
MarineDebris-Sonar-AI: Candidate Ranker Module
Implements multi-objective candidate ranking using a transparent composite utility score:
- Generalization on V3 held-out test (35%)
- Legacy V2 preservation (25%)
- Hard negative false alarm rejection (20%)
- Small-target (<40 px) sensitivity (10%)
- Latency & efficiency adherence (10%)
"""

from typing import Dict, Any, List
from pathlib import Path


class CandidateRanker:
    def __init__(
        self,
        weight_v3_gen: float = 0.35,
        weight_v2_pres: float = 0.25,
        weight_far_rej: float = 0.20,
        weight_small_rec: float = 0.10,
        weight_latency: float = 0.10,
    ):
        self.w_v3 = weight_v3_gen
        self.w_v2 = weight_v2_pres
        self.w_far = weight_far_rej
        self.w_small = weight_small_rec
        self.w_lat = weight_latency

    def compute_composite_score(
        self,
        bench_a: Dict[str, Any],
        bench_b: Dict[str, Any],
        bench_c: Dict[str, Any],
        subgroup: Dict[str, Any] = None,
        latency: Dict[str, Any] = None,
    ) -> float:
        """Calculates normalized composite score in range [0, 1]."""
        v2_m50 = float(bench_a.get("mAP50", 0.0))
        v3_m50 = float(bench_b.get("mAP50", 0.0))
        far = float(bench_c.get("negative_image_FAR", 1.0))
        far_score = max(0.0, 1.0 - far)

        small_recall = 0.0
        if subgroup and "subgroups" in subgroup:
            small_recall = float(subgroup["subgroups"].get("small_lt_40px", {}).get("recall", 0.0))

        lat_factor = 1.0
        if latency and "latency_mean_ms" in latency:
            mean_ms = float(latency["latency_mean_ms"])
            # Normalized score: 1.0 if <= 50ms, decreasing to 0 if >= 150ms
            lat_factor = max(0.0, min(1.0, (150.0 - mean_ms) / 100.0))

        composite = (
            self.w_v3 * v3_m50
            + self.w_v2 * v2_m50
            + self.w_far * far_score
            + self.w_small * small_recall
            + self.w_lat * lat_factor
        )
        return round(composite, 4)

    def rank_candidates(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Ranks a list of candidate dictionaries.
        Each candidate must have: experiment_id, benchmark_a, benchmark_b, benchmark_c,
        and optionally subgroup_analysis, latency, promotion_gate.
        """
        ranked = []
        for c in candidates:
            score = self.compute_composite_score(
                bench_a=c.get("benchmark_a", {}),
                bench_b=c.get("benchmark_b", {}),
                bench_c=c.get("benchmark_c", {}),
                subgroup=c.get("subgroup_analysis", {}),
                latency=c.get("latency", {}),
            )
            c_copy = dict(c)
            c_copy["composite_score"] = score
            ranked.append(c_copy)

        # Sort descending by composite score
        ranked.sort(key=lambda x: x["composite_score"], reverse=True)

        for i, item in enumerate(ranked):
            item["rank"] = i + 1

        return ranked
