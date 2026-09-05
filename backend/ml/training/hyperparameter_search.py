import os
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

import json
from typing import List, Dict, Any

from backend.ml.training.train_yolo import train_yolo_experiment


def run_experiment_matrix() -> List[Dict[str, Any]]:
    experiments = [
        {
            "id": "exp01_sonar_aug_adamw_640",
            "base_model": "yolov8n.pt",
            "epochs": 25,
            "batch": 8,
            "imgsz": 640,
            "lr0": 0.001,
            "optimizer": "AdamW",
            "hsv_v": 0.15,
            "mosaic": 0.15,
            "box": 7.5,
            "cls": 0.5,
            "seed": 42,
        },
        {
            "id": "exp02_highres_768",
            "base_model": "yolov8n.pt",
            "epochs": 25,
            "batch": 8,
            "imgsz": 768,
            "lr0": 0.001,
            "optimizer": "AdamW",
            "hsv_v": 0.15,
            "mosaic": 0.15,
            "box": 7.5,
            "cls": 0.5,
            "seed": 42,
        },
        {
            "id": "exp03_tuned_loss_lr_640",
            "base_model": "yolov8n.pt",
            "epochs": 25,
            "batch": 8,
            "imgsz": 640,
            "lr0": 0.002,
            "optimizer": "AdamW",
            "hsv_v": 0.20,
            "mosaic": 0.10,
            "box": 8.5,
            "cls": 0.8,
            "seed": 42,
        },
    ]

    results = []
    for exp in experiments:
        print(f"\n=======================================================")
        print(f"Launching Experiment: {exp['id']}")
        print(f"=======================================================\n")

        summary = train_yolo_experiment(
            experiment_id=exp["id"],
            base_model=exp["base_model"],
            epochs=exp["epochs"],
            batch=exp["batch"],
            imgsz=exp["imgsz"],
            lr0=exp["lr0"],
            optimizer=exp["optimizer"],
            hsv_v=exp["hsv_v"],
            mosaic=exp["mosaic"],
            box=exp["box"],
            cls=exp["cls"],
            seed=exp["seed"],
            device="cpu",
            output_dir="ml/experiments",
        )
        results.append(summary)

    # Save comparative summary table
    matrix_file = Path("ml/experiments/experiment_comparison_matrix.json")
    with open(matrix_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n=======================================================")
    print("Experiment Matrix Completed. Summary saved to:", matrix_file)
    print("=======================================================\n")
    return results


if __name__ == "__main__":
    run_experiment_matrix()
