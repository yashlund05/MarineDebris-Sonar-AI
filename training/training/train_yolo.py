"""Ultralytics YOLOv8 training runner for MarineDebris-Sonar-AI.

Configures and trains YOLOv8m on acoustic sonar patches (640x640) with:
- Canonical 5 debris classes: derelict_fishing_gear, general_marine_debris,
  shipwreck, pipe_or_cylinder, other_man_made_target
- Strict hyperparameters per DEVELOPMENT_GUIDELINES.md §4.7
"""

import argparse
import os
from pathlib import Path
from typing import Optional


def train_sonar_yolo(
    data_yaml: str,
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    weights: str = "yolov8m.pt",
    device: str = "0",
    project: str = "runs/detect",
    name: str = "sonar_yolov8m_ghostpot_v1",
) -> None:
    """Train YOLOv8 on acoustic sonar imagery.

    Args:
        data_yaml: Path to data.yaml dataset config file.
        epochs: Number of training epochs.
        imgsz: Image tile resolution (640).
        batch: Batch size.
        weights: Initial checkpoint (yolov8m.pt).
        device: CUDA device index or 'cpu'.
        project: Runs output directory.
        name: Experiment run name.
    """
    from ultralytics import YOLO

    print(f"[TRAIN] Initializing YOLOv8 model from {weights}")
    model = YOLO(weights)

    print(f"[TRAIN] Launching training with {data_yaml}, {epochs} epochs, batch={batch}")
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        project=project,
        name=name,
        optimizer="AdamW",
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        mosaic=1.0,
        mixup=0.1,
        copy_paste=0.1,
        save=True,
        plots=True,
    )

    print("[TRAIN] Training complete. Exporting best weights to models/detection/")
    out_dir = Path("models/detection")
    out_dir.mkdir(parents=True, exist_ok=True)
    best_weights = Path(project) / name / "weights" / "best.pt"
    if best_weights.exists():
        import shutil

        dest = out_dir / f"{name}.pt"
        shutil.copy(best_weights, dest)
        print(f"[TRAIN] Deployed best weights to {dest}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 on sonar dataset")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--weights", type=str, default="yolov8m.pt")
    parser.add_argument("--device", type=str, default="0")
    args = parser.parse_args()

    train_sonar_yolo(
        data_yaml=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        weights=args.weights,
        device=args.device,
    )
