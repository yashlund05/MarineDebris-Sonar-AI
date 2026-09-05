"""
MarineDebris-Sonar-AI: Latency Benchmark Module
Benchmarks CPU inference latency and throughput for candidate models:
- 10 warmup iterations to stabilize CPU caches
- 50 timed iterations using high-precision time.perf_counter()
- Computes mean, std, P50, P95, min, max latency (ms) and throughput (FPS)
- Assesses against the edge/AUV latency budget (<= 125 ms / >= 8.0 FPS)
"""

import time
from pathlib import Path
from typing import Dict, Any, Union
import numpy as np
from ultralytics import YOLO

from backend.ml.optimization.utils import ROOT_DIR
from backend.ml.evaluation.evaluation_contract import (
    CANONICAL_IMAGE_SIZE,
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
)

MAX_LATENCY_BUDGET_MS = 125.0  # Production latency SLA for embedded AUV systems


class LatencyBenchmarker:
    def __init__(
        self,
        imgsz: int = CANONICAL_IMAGE_SIZE,
        warmup_runs: int = 10,
        timed_runs: int = 50,
        budget_ms: float = MAX_LATENCY_BUDGET_MS,
    ):
        self.imgsz = imgsz
        self.warmup_runs = warmup_runs
        self.timed_runs = timed_runs
        self.budget_ms = budget_ms

    def benchmark(self, model_input: Union[Path, str, YOLO]) -> Dict[str, Any]:
        """Runs the latency benchmark on CPU."""
        if isinstance(model_input, (str, Path)):
            model = YOLO(str(model_input))
            model_path_str = str(model_input)
        else:
            model = model_input
            model_path_str = getattr(model, "ckpt_path", "YOLO_model")

        # Create synthetic dummy acoustic image (640x640x3 uint8)
        dummy_img = np.random.randint(20, 180, (self.imgsz, self.imgsz, 3), dtype=np.uint8)

        # Warmup runs
        for _ in range(self.warmup_runs):
            _ = model.predict(
                dummy_img,
                imgsz=self.imgsz,
                conf=OPERATIONAL_MISSION_CONF,
                iou=OPERATIONAL_MISSION_IOU,
                device="cpu",
                verbose=False,
            )

        # Timed runs
        timings_ms = []
        for _ in range(self.timed_runs):
            t0 = time.perf_counter()
            _ = model.predict(
                dummy_img,
                imgsz=self.imgsz,
                conf=OPERATIONAL_MISSION_CONF,
                iou=OPERATIONAL_MISSION_IOU,
                device="cpu",
                verbose=False,
            )
            t1 = time.perf_counter()
            timings_ms.append((t1 - t0) * 1000.0)

        timings_arr = np.array(timings_ms)
        mean_ms = float(np.mean(timings_arr))
        std_ms = float(np.std(timings_arr))
        p50_ms = float(np.percentile(timings_arr, 50))
        p95_ms = float(np.percentile(timings_arr, 95))
        min_ms = float(np.min(timings_arr))
        max_ms = float(np.max(timings_arr))
        fps = round(1000.0 / mean_ms, 2) if mean_ms > 0 else 0.0

        meets_budget = bool(p95_ms <= self.budget_ms)

        return {
            "model_path": model_path_str,
            "device": "cpu",
            "imgsz": self.imgsz,
            "warmup_runs": self.warmup_runs,
            "timed_runs": self.timed_runs,
            "latency_mean_ms": round(mean_ms, 2),
            "latency_std_ms": round(std_ms, 2),
            "latency_p50_ms": round(p50_ms, 2),
            "latency_p95_ms": round(p95_ms, 2),
            "latency_min_ms": round(min_ms, 2),
            "latency_max_ms": round(max_ms, 2),
            "fps": fps,
            "budget_ms": self.budget_ms,
            "meets_budget": meets_budget,
        }
