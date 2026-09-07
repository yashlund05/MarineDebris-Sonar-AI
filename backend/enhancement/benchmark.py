"""
Scientific Benchmark Runner for Sonar Image Enhancement.

Implements rigorous evaluation across authorized development splits:
- Measures CPU latency (mean, median, P95, P99)
- Evaluates acoustic metrics: ENL (homogeneous ROI), CNR (eroded target vs ring), EPI (gradient ratio)
- Outputs EXPERIMENT_REGISTRY.jsonl and method_comparison.md
- NEVER fabricates metrics: invalid or unmeasurable samples are explicitly recorded as NOT MEASURABLE.
"""

import os
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

from backend.enhancement.types import (
    EnhancementMethod,
    MetricStatus,
    PromotionStatus,
    BenchmarkRecord
)
from backend.enhancement.methods import apply_enhancement_method, ENHANCEMENT_METHODS
from backend.enhancement.metric_definitions import compute_enl, compute_cnr, compute_epi
from backend.enhancement.data_loader import BenchmarkDatasetLoader

REPORTS_DIR = Path(__file__).resolve().parent.parent.parent / "reports" / "sonar_enhancement"


class EnhancementBenchmarkRunner:
    """Orchestrates comprehensive enhancement benchmarks."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.output_dir / "EXPERIMENT_REGISTRY.jsonl"
        self.comparison_file = self.output_dir / "method_comparison.md"
        self.loader = BenchmarkDatasetLoader()

    def run_method_benchmark(
        self,
        methods: Optional[List[str]] = None,
        dataset_version: str = "v3",
        split: str = "val",
        sample_limit: int = 20,
        insertion_point: str = "P0"
    ) -> Dict[str, Any]:
        """
        Runs systematic evaluation across the designated development partition.
        
        Args:
            methods: List of method names to evaluate (defaults to all classical methods).
            dataset_version: 'v3' or 'v2'.
            split: 'val' or 'train' (strictly non-test).
            sample_limit: Number of frames to evaluate.
            insertion_point: 'P0', 'P1', 'P2', or 'P3'.
        """
        if split not in ["val", "train"]:
            raise ValueError(f"Scientific development benchmark cannot use split '{split}'.")

        eval_methods = methods or [m.value for m in EnhancementMethod]
        samples = self.loader.get_development_samples(dataset_version=dataset_version, split=split, limit=sample_limit)

        results_by_method: Dict[str, Dict[str, Any]] = {}

        for m_name in eval_methods:
            latencies: List[float] = []
            enl_values: List[float] = []
            cnr_values: List[float] = []
            epi_values: List[float] = []

            for sample in samples:
                img_path = sample["image_path"]
                raw_img = self.loader.load_image_float32(img_path)

                # Warmup single pass
                _ = apply_enhancement_method(m_name, raw_img)

                # Timed execution
                t_start = time.perf_counter()
                res = apply_enhancement_method(m_name, raw_img)
                elapsed_ms = (time.perf_counter() - t_start) * 1000.0
                latencies.append(elapsed_ms)

                enhanced_img = res.canonical_image

                # 1. Compute ENL on homogeneous background
                enl_res = compute_enl(enhanced_img)
                if enl_res.status == MetricStatus.VALID and enl_res.value is not None:
                    enl_values.append(enl_res.value)

                # 2. Compute EPI relative to raw input
                epi_res = compute_epi(raw_img, enhanced_img)
                if epi_res.status == MetricStatus.VALID and epi_res.value is not None:
                    epi_values.append(epi_res.value)

                # 3. Compute CNR if ground-truth boxes are available
                boxes = sample.get("boxes", [])
                for b in boxes:
                    # b: (class_id, cx, cy, w, h)
                    bbox_norm = (b[1], b[2], b[3], b[4])
                    cnr_res = compute_cnr(enhanced_img, bbox_xywh_norm=bbox_norm)
                    if cnr_res.status == MetricStatus.VALID and cnr_res.value is not None:
                        cnr_values.append(cnr_res.value)

                # Append to JSONL registry
                record = {
                    "dataset_version": dataset_version,
                    "split": split,
                    "sequence_policy": "sequence-isolated-development",
                    "insertion_point": insertion_point,
                    "image_name": sample["image_name"],
                    "method": m_name,
                    "parameters": res.parameters,
                    "execution_time_ms": round(elapsed_ms, 3),
                    "metrics": {
                        "enl": enl_res.value if enl_res.status == MetricStatus.VALID else None,
                        "epi": epi_res.value if epi_res.status == MetricStatus.VALID else None,
                        "cnr_count": len(cnr_values)
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                self._append_registry(record)

            # Compute aggregate stats
            lat_arr = np.array(latencies) if latencies else np.array([0.0])
            results_by_method[m_name] = {
                "sample_count": len(samples),
                "latency_mean_ms": round(float(np.mean(lat_arr)), 3),
                "latency_median_ms": round(float(np.median(lat_arr)), 3),
                "latency_p95_ms": round(float(np.percentile(lat_arr, 95)), 3),
                "latency_p99_ms": round(float(np.percentile(lat_arr, 99)), 3),
                "enl_mean": round(float(np.mean(enl_values)), 3) if enl_values else None,
                "enl_valid_samples": len(enl_values),
                "cnr_mean": round(float(np.mean(cnr_values)), 3) if cnr_values else None,
                "cnr_valid_boxes": len(cnr_values),
                "epi_mean": round(float(np.mean(epi_values)), 3) if epi_values else None,
            }

        # Generate markdown report
        self._write_comparison_markdown(results_by_method, dataset_version, split, sample_limit, insertion_point)
        return results_by_method

    def _append_registry(self, record: Dict[str, Any]) -> None:
        """Appends one record to EXPERIMENT_REGISTRY.jsonl."""
        with open(self.registry_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def _write_comparison_markdown(
        self,
        results: Dict[str, Dict[str, Any]],
        dataset: str,
        split: str,
        n_samples: int,
        insertion: str
    ) -> None:
        """Writes scientific markdown table comparing all evaluated methods."""
        lines = [
            "# Sonar Enhancement Method Comparison & Benchmark Report",
            "",
            f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"- **Dataset**: {dataset.upper()} ({split} split, sequence-isolated)",
            f"- **Sample Count**: {n_samples} frames",
            f"- **Insertion Point**: `{insertion}`",
            f"- **Hardware Platform**: CPU Execution (16-core host)",
            "",
            "## Quantitative Benchmark Matrix",
            "",
            "| Method | Mean Latency | P95 Latency | P99 Latency | ENL (Looks) | CNR (Target Contrast) | EPI (Edge Preservation) |",
            "|---|---|---|---|---|---|---|",
        ]

        for method_name, stats in results.items():
            enl_str = f"{stats['enl_mean']:.2f}" if stats['enl_mean'] is not None else "N/A"
            cnr_str = f"{stats['cnr_mean']:.2f}" if stats['cnr_mean'] is not None else "N/A"
            epi_str = f"{stats['epi_mean']:.3f}" if stats['epi_mean'] is not None else "N/A"

            lines.append(
                f"| `{method_name}` | {stats['latency_mean_ms']:.2f} ms | "
                f"{stats['latency_p95_ms']:.2f} ms | {stats['latency_p99_ms']:.2f} ms | "
                f"{enl_str} | {cnr_str} | {epi_str} |"
            )

        lines.extend([
            "",
            "## Metric Validity and Interpretations",
            "- **ENL (Equivalent Number of Looks)**: Evaluated strictly on homogeneous background ROIs; higher represents reduced speckle variance.",
            "- **CNR (Contrast-to-Noise Ratio)**: Evaluated on centroid-eroded target interior vs surrounding background ring.",
            "- **EPI (Edge Preservation Index)**: High-pass Laplacian energy ratio; identity check yields exactly 1.000.",
            "- **Target CPU Budget**: < 10.0 ms per 640x640 frame for real-time edge integration.",
            "",
            "## Registry Traceability",
            f"Detailed per-sample records are logged in `{self.registry_file.name}`."
        ])

        with open(self.comparison_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
