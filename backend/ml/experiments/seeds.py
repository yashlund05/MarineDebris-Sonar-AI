"""
MarineDebris-Sonar-AI: Multi-Seed Experiment Controller
Coordinates multi-seed evaluations across seeds 42, 123, and 2026,
computing mean, standard deviation, best, and worst metrics to prevent cherry-picking.
"""

from typing import Dict, List, Any
import numpy as np


class MultiSeedEvaluator:
    @staticmethod
    def aggregate_seed_metrics(seed_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Computes mean, standard deviation, best, and worst across multiple seed evaluations.
        """
        if not seed_records:
            return {}

        metric_keys = ["precision", "recall", "f1", "mAP50", "mAP50_95"]
        aggregated = {}

        for key in metric_keys:
            values = [float(r.get(key, 0.0)) for r in seed_records if key in r]
            if values:
                aggregated[key] = {
                    "mean": round(float(np.mean(values)), 4),
                    "std": round(float(np.std(values)), 4),
                    "best": round(float(np.max(values)), 4),
                    "worst": round(float(np.min(values)), 4),
                    "raw_values": values,
                }

        return aggregated
