"""
MarineDebris-Sonar-AI: Promotion Gate Module
Enforces strict, auditable promotion criteria comparing candidates against
the frozen production baseline (Benchmark A: V2, Benchmark B: V3, Benchmark C: Hard Negatives, Latency).

CRITICAL RULE:
Regression tolerances are defined as ABSOLUTE percentage points:
- V2 mAP50 regression <= 1.0 percentage points (0.8921 - 0.0100 = 0.8821)
- V2 Recall regression <= 2.0 percentage points (0.9015 - 0.0200 = 0.8815)
- Image-level FAR <= 21.43% (18/84)
- Total FP boxes <= 18
- Latency P95 <= 125.0 ms
"""

from typing import Dict, Any, List, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict


@dataclass
class PromotionResult:
    status: str  # ELIGIBLE_FOR_PROMOTION or REJECTED
    overall_pass: bool
    promotion_eligible: bool
    checks: List[Dict[str, Any]]
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def __getitem__(self, item):
        return asdict(self)[item]

    def get(self, key, default=None):
        return asdict(self).get(key, default)


# Frozen production baseline targets established in Phase 2.5 Evaluation Integrity
FROZEN_BASELINE = {
    "v2_test": {
        "mAP50": 0.8921,
        "mAP50_95": 0.6235,
        "precision": 0.9325,
        "recall": 0.9015,
        "f1": 0.9167,
    },
    "v3_test": {
        "mAP50": 0.9192,
        "mAP50_95": 0.6402,
        "precision": 0.9092,
        "recall": 0.9024,
        "f1": 0.9058,
    },
    "hard_negatives": {
        "negative_image_FAR": 0.2143,
        "total_false_positive_boxes": 18,
    },
    "latency": {
        "p95_budget_ms": 125.0,
    },
    "stability": {
        "max_seed_std_mAP50": 0.0150,  # <= 1.5% absolute points std dev across seeds
    },
}

# Strict absolute percentage-point tolerances
TOLERANCE = {
    "v2_map50_regression_abs": 0.0100,  # 1.0 percentage point max regression
    "v2_recall_regression_abs": 0.0200,  # 2.0 percentage points max regression
}


class PromotionGate:
    def __init__(self, baseline: Dict[str, Any] = FROZEN_BASELINE, tolerance: Dict[str, Any] = TOLERANCE):
        self.baseline = baseline
        self.tolerance = tolerance

    def evaluate_candidate(
        self,
        bench_a: Dict[str, Any],
        bench_b: Dict[str, Any],
        bench_c: Dict[str, Any],
        latency: Dict[str, Any],
        seed_stats: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates candidate against promotion rules.
        Returns detailed pass/fail status and audit report.
        """
        checks = []
        overall_pass = True

        # Check 1: V2 mAP50 Absolute Regression <= 1.0%
        cand_v2_map50 = float(bench_a.get("mAP50", 0.0))
        base_v2_map50 = self.baseline["v2_test"]["mAP50"]
        min_v2_map50 = base_v2_map50 - self.tolerance["v2_map50_regression_abs"]
        delta_v2_map50 = cand_v2_map50 - base_v2_map50
        pass_v2_map = cand_v2_map50 >= min_v2_map50
        if not pass_v2_map:
            overall_pass = False
        checks.append({
            "name": "V2 Legacy mAP50 Absolute Regression",
            "required": f">= {round(min_v2_map50 * 100, 2)}% (Base: {round(base_v2_map50 * 100, 2)}% - 1.0% abs)",
            "observed": f"{round(cand_v2_map50 * 100, 2)}% (Delta: {round(delta_v2_map50 * 100, 2)}%)",
            "passed": pass_v2_map,
        })

        # Check 2: V2 Recall Absolute Regression <= 2.0%
        cand_v2_rec = float(bench_a.get("recall", 0.0))
        base_v2_rec = self.baseline["v2_test"]["recall"]
        min_v2_rec = base_v2_rec - self.tolerance["v2_recall_regression_abs"]
        delta_v2_rec = cand_v2_rec - base_v2_rec
        pass_v2_rec = cand_v2_rec >= min_v2_rec
        if not pass_v2_rec:
            overall_pass = False
        checks.append({
            "name": "V2 Legacy Recall Absolute Regression",
            "required": f">= {round(min_v2_rec * 100, 2)}% (Base: {round(base_v2_rec * 100, 2)}% - 2.0% abs)",
            "observed": f"{round(cand_v2_rec * 100, 2)}% (Delta: {round(delta_v2_rec * 100, 2)}%)",
            "passed": pass_v2_rec,
        })

        # Check 3: V3 Held-out Generalization
        cand_v3_map50 = float(bench_b.get("mAP50", 0.0))
        base_v3_map50 = self.baseline["v3_test"]["mAP50"]
        delta_v3_map = cand_v3_map50 - base_v3_map50
        pass_v3_map = cand_v3_map50 >= (base_v3_map50 - 0.0200)  # Must retain V3 generalization
        if not pass_v3_map:
            overall_pass = False
        checks.append({
            "name": "V3 Generalization mAP50",
            "required": f">= {round((base_v3_map50 - 0.0200) * 100, 2)}% (Base: {round(base_v3_map50 * 100, 2)}%)",
            "observed": f"{round(cand_v3_map50 * 100, 2)}% (Delta: {round(delta_v3_map * 100, 2)}%)",
            "passed": pass_v3_map,
        })

        # Check 4: Negative Image False Alarm Rate (FAR)
        cand_far = float(bench_c.get("negative_image_FAR", 1.0))
        base_far = self.baseline["hard_negatives"]["negative_image_FAR"]
        pass_far = cand_far <= base_far
        if not pass_far:
            overall_pass = False
        checks.append({
            "name": "Negative Image False Alarm Rate (FAR)",
            "required": f"<= {round(base_far * 100, 2)}% (18/84 frames)",
            "observed": f"{round(cand_far * 100, 2)}% ({bench_c.get('flagged_negative_images', 0)}/84 frames)",
            "passed": pass_far,
        })

        # Check 5: Total False Positive Boxes
        cand_total_fps = int(bench_c.get("total_false_positive_boxes", 999))
        base_total_fps = self.baseline["hard_negatives"]["total_false_positive_boxes"]
        pass_total_fps = cand_total_fps <= base_total_fps
        if not pass_total_fps:
            overall_pass = False
        checks.append({
            "name": "Total False Positive Box Count",
            "required": f"<= {base_total_fps} boxes",
            "observed": f"{cand_total_fps} boxes",
            "passed": pass_total_fps,
        })

        # Check 6: CPU Inference Latency (P95)
        cand_p95 = float(latency.get("latency_p95_ms", 999.0))
        budget_p95 = self.baseline["latency"]["p95_budget_ms"]
        pass_lat = cand_p95 <= budget_p95
        if not pass_lat:
            overall_pass = False
        checks.append({
            "name": "CPU Latency Budget (P95)",
            "required": f"<= {budget_p95} ms",
            "observed": f"{cand_p95} ms (FPS: {latency.get('fps', 0.0)})",
            "passed": pass_lat,
        })

        # Check 7: Multi-Seed Stability (Optional if seed_stats provided)
        if seed_stats is not None and "mAP50_std" in seed_stats:
            seed_std = float(seed_stats["mAP50_std"])
            max_std = self.baseline["stability"]["max_seed_std_mAP50"]
            pass_seed = seed_std <= max_std
            if not pass_seed:
                overall_pass = False
            checks.append({
                "name": "Multi-Seed Stability (mAP50 Std Dev)",
                "required": f"<= {round(max_std * 100, 2)}%",
                "observed": f"{round(seed_std * 100, 2)}%",
                "passed": pass_seed,
            })

        status = "ELIGIBLE_FOR_PROMOTION" if overall_pass else "REJECTED"

        return PromotionResult(
            status=status,
            overall_pass=overall_pass,
            promotion_eligible=overall_pass,
            checks=checks,
            recommendation=(
                "Candidate model passes all non-regression, generalization, clutter rejection, "
                "and latency criteria. Eligible for opt-in promotion."
                if overall_pass
                else "Candidate model failed one or more gating criteria. Production weights remain active."
            ),
        )

    def evaluate_checkpoint(self, checkpoint_path: Path) -> PromotionResult:
        """Runs full benchmarks, latency measurement, and evaluates against promotion criteria."""
        from backend.ml.optimization.benchmark_suite import BenchmarkSuite
        from backend.ml.optimization.latency_benchmark import LatencyBenchmarker

        checkpoint_path = Path(checkpoint_path)
        suite = BenchmarkSuite()
        bench_results = suite.run_complete_suite(checkpoint_path)

        lb = LatencyBenchmarker(warmup_runs=5, timed_runs=20)
        lat_results = lb.benchmark(checkpoint_path)

        return self.evaluate_candidate(
            bench_a=bench_results["benchmark_a_legacy_v2"],
            bench_b=bench_results["benchmark_b_v3_held_out"],
            bench_c=bench_results["benchmark_c_hard_negatives"],
            latency=lat_results,
        )
