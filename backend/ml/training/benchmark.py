"""
MarineDebris-Sonar-AI: Latency and Resource Benchmarking Tool
Profiles preprocessing, model forward-pass, NMS, and total detection latency
across repeated trials, reporting Mean, Median, and 95th Percentile (P95).
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import time
import json
from typing import Dict, Any, List
import numpy as np
import cv2
import torch
from ultralytics import YOLO


def benchmark_model_latency(
    model_path: str = "models/detection/sonar_yolov8_fls_trained.pt",
    test_image_dir: str = "data/test_sonar_images",
    num_runs: int = 25,
    imgsz: int = 640,
) -> Dict[str, Any]:
    print(f"Benchmarking latency for {model_path} ({num_runs} runs)...")
    model = YOLO(model_path)

    img_dir = Path(test_image_dir)
    images = list(img_dir.glob("*.png"))
    if not images:
        images = list(Path("datasets/sonar_debris_v2_clean/images/test").glob("*.png"))

    if not images:
        raise FileNotFoundError(f"No test images found in {test_image_dir} or dataset")

    # Warmup
    dummy_img = cv2.imread(str(images[0]))
    for _ in range(3):
        _ = model.predict(dummy_img, imgsz=imgsz, verbose=False)

    preprocess_times = []
    inference_times = []
    postprocess_times = []
    total_times = []

    for i in range(num_runs):
        img_p = images[i % len(images)]
        img_raw = cv2.imread(str(img_p))

        t0 = time.perf_counter()
        # Simulated preprocessing (CLAHE + normalization)
        gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY) if len(img_raw.shape) == 3 else img_raw
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        t1 = time.perf_counter()

        # Model inference
        res = model.predict(bgr, imgsz=imgsz, conf=0.30, verbose=False)
        t2 = time.perf_counter()

        # Postprocessing (filtering/bounding box extraction)
        boxes = res[0].boxes if (res and len(res) > 0) else None
        _ = len(boxes) if boxes is not None else 0
        t3 = time.perf_counter()

        preprocess_ms = (t1 - t0) * 1000
        inference_ms = (t2 - t1) * 1000
        postprocess_ms = (t3 - t2) * 1000
        total_ms = (t3 - t0) * 1000

        preprocess_times.append(preprocess_ms)
        inference_times.append(inference_ms)
        postprocess_times.append(postprocess_ms)
        total_times.append(total_ms)

    def calc_stats(arr: List[float]) -> Dict[str, float]:
        a = np.array(arr)
        return {
            "mean_ms": round(float(np.mean(a)), 2),
            "median_ms": round(float(np.median(a)), 2),
            "p95_ms": round(float(np.percentile(a, 95)), 2),
            "min_ms": round(float(np.min(a)), 2),
            "max_ms": round(float(np.max(a)), 2),
        }

    benchmarks = {
        "model_path": str(model_path),
        "num_runs": num_runs,
        "resolution": [imgsz, imgsz],
        "device": "cpu" if not torch.cuda.is_available() else "cuda",
        "cpu_threads": torch.get_num_threads(),
        "stages": {
            "preprocessing": calc_stats(preprocess_times),
            "inference": calc_stats(inference_times),
            "postprocessing": calc_stats(postprocess_times),
            "total_pipeline": calc_stats(total_times),
        },
        "throughput_fps": round(1000.0 / float(np.mean(total_times)), 2),
    }

    out_file = Path("ml/experiments/final/latency_benchmark.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmarks, f, indent=2)

    print(f"Benchmark complete. Results saved to {out_file}")
    return benchmarks


if __name__ == "__main__":
    res = benchmark_model_latency("ml/experiments/exp01_sonar_aug_adamw_640/train_run/weights/best.pt")
    print(json.dumps(res, indent=2))
