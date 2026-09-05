"""
MarineDebris-Sonar-AI: YOLO Model Evaluation and Benchmark Engine
Provides reproducible evaluation on validation and test splits with per-class metrics,
multi-threshold sweeps, confusion matrix extraction, and machine-readable output.
"""

import os
import sys
import json
import time
import platform
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import numpy as np
from ultralytics import YOLO


def evaluate_model(
    model_path: str,
    data_yaml: str,
    split: str = "val",
    imgsz: int = 640,
    batch: int = 8,
    conf_thresholds: Optional[list] = None,
    device: str = "cpu",
    save_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Run standard validation/test evaluation on a YOLO model.
    """
    if conf_thresholds is None:
        conf_thresholds = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80]

    model_path_obj = Path(model_path)
    if not model_path_obj.exists():
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    data_yaml_path = Path(data_yaml)
    if not data_yaml_path.exists():
        raise FileNotFoundError(f"Dataset YAML not found at: {data_yaml}")

    print(f"[{datetime.now(timezone.utc).isoformat()}] Loading model from {model_path} on {device}...")
    model = YOLO(str(model_path_obj))

    # Parameter count
    param_count = sum(p.numel() for p in model.model.parameters()) if hasattr(model, "model") and model.model is not None else 0

    print(f"Running validation on split='{split}', imgsz={imgsz}, batch={batch}...")
    # Run standard validation
    val_results = model.val(
        data=str(data_yaml_path),
        split=split,
        imgsz=imgsz,
        batch=batch,
        device=device,
        verbose=False,
        save_json=False,
        plots=False,
    )

    # Extract primary metrics
    # val_results.results_dict contains metrics
    rd = val_results.results_dict
    mp = float(rd.get("metrics/precision(B)", 0.0))
    mr = float(rd.get("metrics/recall(B)", 0.0))
    map50 = float(rd.get("metrics/mAP50(B)", 0.0))
    map50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
    f1 = float((2 * mp * mr) / (mp + mr)) if (mp + mr) > 0 else 0.0

    # Class-level metrics
    names = val_results.names
    per_class_metrics = {}
    if hasattr(val_results, "box") and val_results.box is not None:
        box = val_results.box
        ap50_per_class = box.ap50 if hasattr(box, "ap50") and box.ap50 is not None else []
        ap_per_class = box.ap if hasattr(box, "ap") and box.ap is not None else []
        p_per_class = box.p if hasattr(box, "p") and box.p is not None else []
        r_per_class = box.r if hasattr(box, "r") and box.r is not None else []
        f1_per_class = box.f1 if hasattr(box, "f1") and box.f1 is not None else []

        for c_idx, c_name in names.items():
            if c_idx < len(ap50_per_class):
                c_p = float(p_per_class[c_idx]) if c_idx < len(p_per_class) else 0.0
                c_r = float(r_per_class[c_idx]) if c_idx < len(r_per_class) else 0.0
                c_ap50 = float(ap50_per_class[c_idx])
                c_ap = float(ap_per_class[c_idx])
                c_f1 = float(f1_per_class[c_idx]) if c_idx < len(f1_per_class) else (
                    float((2 * c_p * c_r) / (c_p + c_r)) if (c_p + c_r) > 0 else 0.0
                )
                per_class_metrics[c_name] = {
                    "class_id": int(c_idx),
                    "precision": round(c_p, 4),
                    "recall": round(c_r, 4),
                    "f1": round(c_f1, 4),
                    "mAP50": round(c_ap50, 4),
                    "mAP50_95": round(c_ap, 4),
                }

    # Speed metrics (ms per image)
    speed_dict = getattr(val_results, "speed", {})
    preprocess_ms = float(speed_dict.get("preprocess", 0.0))
    inference_ms = float(speed_dict.get("inference", 0.0))
    loss_ms = float(speed_dict.get("loss", 0.0))
    postprocess_ms = float(speed_dict.get("postprocess", 0.0))
    total_ms = preprocess_ms + inference_ms + postprocess_ms

    # Multi-threshold evaluation
    threshold_sweeps = []
    print("Evaluating confidence threshold sweeps...")
    for conf in conf_thresholds:
        t_res = model.val(
            data=str(data_yaml_path),
            split=split,
            imgsz=imgsz,
            batch=batch,
            conf=conf,
            device=device,
            verbose=False,
            plots=False,
        )
        t_rd = t_res.results_dict
        t_p = float(t_rd.get("metrics/precision(B)", 0.0))
        t_r = float(t_rd.get("metrics/recall(B)", 0.0))
        t_map50 = float(t_rd.get("metrics/mAP50(B)", 0.0))
        t_map50_95 = float(t_rd.get("metrics/mAP50-95(B)", 0.0))
        t_f1 = float((2 * t_p * t_r) / (t_p + t_r)) if (t_p + t_r) > 0 else 0.0

        threshold_sweeps.append({
            "confidence_threshold": conf,
            "precision": round(t_p, 4),
            "recall": round(t_r, 4),
            "f1": round(t_f1, 4),
            "mAP50": round(t_map50, 4),
            "mAP50_95": round(t_map50_95, 4),
        })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_path": str(model_path_obj),
        "dataset_yaml": str(data_yaml_path),
        "split": split,
        "parameters": int(param_count),
        "input_resolution": [imgsz, imgsz],
        "device": device,
        "environment": {
            "os": platform.system(),
            "python": platform.python_version(),
            "pytorch": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
        },
        "overall_metrics": {
            "precision": round(mp, 4),
            "recall": round(mr, 4),
            "f1": round(f1, 4),
            "mAP50": round(map50, 4),
            "mAP50_95": round(map50_95, 4),
        },
        "per_class_metrics": per_class_metrics,
        "latency_ms": {
            "preprocess": round(preprocess_ms, 2),
            "inference": round(inference_ms, 2),
            "postprocess": round(postprocess_ms, 2),
            "total": round(total_ms, 2),
        },
        "confidence_threshold_sweeps": threshold_sweeps,
    }

    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
        out_file = Path(save_dir) / f"evaluation_{split}_{imgsz}px.json"
        with open(out_file, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Saved evaluation report to {out_file}")

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate YOLO FLS Model")
    parser.add_argument("--model", type=str, required=True, help="Path to model checkpoint")
    parser.add_argument("--data", type=str, default="datasets/sonar_debris/data.yaml", help="Path to data YAML")
    parser.add_argument("--split", type=str, default="val", choices=["val", "test", "train"], help="Split to evaluate")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    parser.add_argument("--save_dir", type=str, default="ml/experiments/baseline", help="Directory to save evaluation json")

    args = parser.parse_args()
    res = evaluate_model(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        save_dir=args.save_dir,
    )
    print(json.dumps(res["overall_metrics"], indent=2))
