"""Edge inference benchmark measuring latency, throughput, and memory footprint.

Supports both PyTorch (.pt) and ONNX (.onnx) runtime backends.
"""

import argparse
import time
from pathlib import Path
from typing import Any, Dict
import numpy as np


def benchmark_model(
    model_path: str,
    imgsz: int = 640,
    batch_size: int = 1,
    num_warmup: int = 10,
    num_runs: int = 50,
    device: str = "cpu",
) -> dict[str, Any]:
    """Benchmark inference latency and FPS.

    Args:
        model_path: Path to .pt or .onnx model.
        imgsz: Image resolution (640).
        batch_size: Batch size for testing.
        num_warmup: Number of warmup iterations.
        num_runs: Timed iteration count.
        device: 'cpu' or 'cuda'.

    Returns:
        Dict with latency and throughput metrics.
    """
    if not Path(model_path).exists():
        raise FileNotFoundError(f"Model file not found: {model_path}")

    from ultralytics import YOLO

    model = YOLO(model_path)
    print(f"[BENCHMARK] Loading {model_path} on device={device}")

    # Generate synthetic dummy sonar tile batch
    dummy_input = np.random.uniform(0.0, 1.0, size=(batch_size, 3, imgsz, imgsz)).astype(
        np.float32
    )

    # Warmup
    print(f"[BENCHMARK] Running {num_warmup} warmup iterations...")
    for _ in range(num_warmup):
        _ = model(dummy_input, device=device, verbose=False)

    # Timed runs
    print(f"[BENCHMARK] Running {num_runs} timed iterations...")
    latencies_ms = []

    for _ in range(num_runs):
        start = time.perf_counter()
        _ = model(dummy_input, device=device, verbose=False)
        end = time.perf_counter()
        latencies_ms.append((end - start) * 1000.0)

    avg_latency = float(np.mean(latencies_ms))
    p50_latency = float(np.percentile(latencies_ms, 50))
    p95_latency = float(np.percentile(latencies_ms, 95))
    p99_latency = float(np.percentile(latencies_ms, 99))
    fps = (batch_size * 1000.0) / avg_latency

    results = {
        "model": model_path,
        "device": device,
        "batch_size": batch_size,
        "input_shape": [batch_size, 3, imgsz, imgsz],
        "latency_avg_ms": round(avg_latency, 2),
        "latency_p50_ms": round(p50_latency, 2),
        "latency_p95_ms": round(p95_latency, 2),
        "latency_p99_ms": round(p99_latency, 2),
        "throughput_fps": round(fps, 1),
    }

    print(f"\n================ BENCHMARK RESULTS ================")
    print(f"Model:           {results['model']}")
    print(f"Device:          {results['device']}")
    print(f"Batch Size:      {results['batch_size']}")
    print(f"Average Latency: {results['latency_avg_ms']} ms")
    print(f"P95 Latency:     {results['latency_p95_ms']} ms")
    print(f"Throughput:      {results['throughput_fps']} FPS")
    print(f"===================================================\n")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark edge inference")
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--device", type=str, default="cpu")
    parser.add_argument("--batch", type=int, default=1)
    parser.add_argument("--imgsz", type=int, default=640)
    args = parser.parse_args()

    benchmark_model(
        model_path=args.model,
        device=args.device,
        batch_size=args.batch,
        imgsz=args.imgsz,
    )
