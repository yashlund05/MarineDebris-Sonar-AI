"""
MarineDebris-Sonar-AI: Advanced YOLO Training & Optimization Harness
Provides structured training, acoustic augmentations, hyperparameter control,
and experiment artifact tracking.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import torch
# Maximize CPU parallelization
if not torch.cuda.is_available():
    torch.set_num_threads(min(8, os.cpu_count() or 4))

from ultralytics import YOLO

from backend.ml.training.evaluate_yolo import evaluate_model


def train_yolo_experiment(
    experiment_id: str,
    base_model: str = "yolov8n.pt",
    data_yaml: str = "datasets/sonar_debris_v2_clean/data.yaml",
    epochs: int = 30,
    batch: int = 8,
    imgsz: int = 640,
    lr0: float = 0.001,
    lrf: float = 0.01,
    optimizer: str = "AdamW",
    weight_decay: float = 0.0005,
    warmup_epochs: float = 3.0,
    box: float = 7.5,
    cls: float = 0.5,
    dfl: float = 1.5,
    hsv_h: float = 0.0,  # Zero hue jitter for acoustic sonar
    hsv_s: float = 0.0,  # Zero saturation jitter for grayscale acoustic sonar
    hsv_v: float = 0.15,  # Acoustic intensity/gain variation
    degrees: float = 5.0,  # Controlled rotation
    translate: float = 0.05,
    scale: float = 0.1,
    fliplr: float = 0.5,  # Horizontal swath symmetry
    flipud: float = 0.0,  # Range axis is directional
    mosaic: float = 0.2,  # Controlled mosaic for acoustic context
    patience: int = 15,
    seed: int = 42,
    device: str = "cpu",
    output_dir: str = "ml/experiments",
) -> Dict[str, Any]:
    exp_dir = Path(output_dir) / experiment_id
    exp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=======================================================")
    print(f"Starting Experiment: {experiment_id}")
    print(f"Base Model: {base_model} | Imgsz: {imgsz} | Epochs: {epochs} | Device: {device} | Seed: {seed}")
    print(f"=======================================================\n")

    start_time = time.time()

    model = YOLO(base_model)

    train_args = {
        "data": str(Path(data_yaml).resolve()),
        "epochs": epochs,
        "batch": batch,
        "imgsz": imgsz,
        "device": device,
        "workers": 2,
        "optimizer": optimizer,
        "lr0": lr0,
        "lrf": lrf,
        "weight_decay": weight_decay,
        "warmup_epochs": warmup_epochs,
        "box": box,
        "cls": cls,
        "dfl": dfl,
        "hsv_h": hsv_h,
        "hsv_s": hsv_s,
        "hsv_v": hsv_v,
        "degrees": degrees,
        "translate": translate,
        "scale": scale,
        "fliplr": fliplr,
        "flipud": flipud,
        "mosaic": mosaic,
        "patience": patience,
        "seed": seed,
        "project": str(exp_dir.resolve()),
        "name": "train_run",
        "exist_ok": True,
        "verbose": True,
        "plots": True,
        "save": True,
    }

    # Execute training
    results = model.train(**train_args)

    training_duration = time.time() - start_time
    best_weights_path = exp_dir / "train_run" / "weights" / "best.pt"
    if not best_weights_path.exists():
        best_weights_path = exp_dir / "train_run" / "weights" / "last.pt"

    print(f"\nTraining completed in {training_duration:.1f}s. Best weights: {best_weights_path}")

    # Evaluate best weights on validation set
    val_report = evaluate_model(
        model_path=str(best_weights_path),
        data_yaml=str(Path(data_yaml).resolve()),
        split="val",
        imgsz=imgsz,
        batch=batch,
        device=device,
        save_dir=str(exp_dir),
    )

    exp_summary = {
        "experiment_id": experiment_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "training_duration_seconds": round(training_duration, 1),
        "base_model": base_model,
        "data_yaml": str(data_yaml),
        "hyperparameters": {
            "epochs": epochs,
            "batch": batch,
            "imgsz": imgsz,
            "lr0": lr0,
            "lrf": lrf,
            "optimizer": optimizer,
            "weight_decay": weight_decay,
            "warmup_epochs": warmup_epochs,
            "box": box,
            "cls": cls,
            "dfl": dfl,
            "hsv_h": hsv_h,
            "hsv_s": hsv_s,
            "hsv_v": hsv_v,
            "degrees": degrees,
            "mosaic": mosaic,
            "seed": seed,
        },
        "best_weights": str(best_weights_path),
        "validation_metrics": val_report["overall_metrics"],
        "per_class_metrics": val_report["per_class_metrics"],
        "latency_ms": val_report["latency_ms"],
    }

    with open(exp_dir / "experiment_summary.json", "w", encoding="utf-8") as f:
        json.dump(exp_summary, f, indent=2)

    return exp_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO on FLS Sonar Dataset")
    parser.add_argument("--id", type=str, required=True, help="Experiment ID")
    parser.add_argument("--base_model", type=str, default="yolov8n.pt", help="Base model checkpoint")
    parser.add_argument("--data", type=str, default="datasets/sonar_debris_v2_clean/data.yaml", help="Data YAML")
    parser.add_argument("--epochs", type=int, default=25, help="Number of epochs")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--lr0", type=float, default=0.001, help="Initial learning rate")
    parser.add_argument("--optimizer", type=str, default="AdamW", choices=["AdamW", "SGD", "Adam"], help="Optimizer")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--device", type=str, default="cpu", help="Device (cpu or cuda)")
    parser.add_argument("--output_dir", type=str, default="ml/experiments", help="Output directory")

    args = parser.parse_args()
    summary = train_yolo_experiment(
        experiment_id=args.id,
        base_model=args.base_model,
        data_yaml=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        lr0=args.lr0,
        optimizer=args.optimizer,
        seed=args.seed,
        device=args.device,
        output_dir=args.output_dir,
    )
    print(json.dumps(summary["validation_metrics"], indent=2))
