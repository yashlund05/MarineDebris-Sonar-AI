"""
MarineDebris-Sonar-AI: Production Model Promotion Tool
Promotes validated experimental checkpoints to production status,
updating weight files, model metrics manifests, and registry entries.
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime, timezone

# Add project root to sys.path
root_dir = str(Path(__file__).resolve().parents[3])
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)


def promote_model_to_production(
    src_weights: str = "ml/experiments/exp01_sonar_aug_adamw_640/train_run/weights/best.pt",
    test_metrics_json: str = "ml/experiments/final/evaluation_test_640px.json",
    dest_dir: str = "models/detection",
):
    src_p = Path(src_weights)
    if not src_p.exists():
        raise FileNotFoundError(f"Source weights not found: {src_weights}")

    dest_dir_p = Path(dest_dir)
    dest_dir_p.mkdir(parents=True, exist_ok=True)

    # 1. Promote weights
    dest_target1 = dest_dir_p / "sonar_yolov8_fls_trained.pt"
    dest_target2 = dest_dir_p / "sonar_yolov8m_ghostpot_v1.pt"

    shutil.copy2(src_p, dest_target1)
    shutil.copy2(src_p, dest_target2)
    print(f"Promoted checkpoint to {dest_target1} and {dest_target2}")

    # 2. Update fls_model_metrics.json
    with open(test_metrics_json, "r", encoding="utf-8") as f:
        test_eval = json.load(f)

    metrics_manifest = {
        "dataset": "Marine Debris Forward-Looking Sonar (FLS)",
        "sensor": "ARIS Explorer 3000 (3.0 MHz High-Frequency Sonar)",
        "resolution": "0.08m range resolution",
        "held_out_test_images": 37,
        "precision": test_eval["overall_metrics"]["precision"],
        "recall": test_eval["overall_metrics"]["recall"],
        "f1": test_eval["overall_metrics"]["f1"],
        "mAP50": test_eval["overall_metrics"]["mAP50"],
        "mAP50_95": test_eval["overall_metrics"]["mAP50_95"],
        "per_class": {
            k: {"mAP50_95": v["mAP50_95"], "mAP50": v["mAP50"], "precision": v["precision"], "recall": v["recall"], "f1": v["f1"]}
            for k, v in test_eval["per_class_metrics"].items()
        },
        "latency_ms": test_eval["latency_ms"],
        "weights_file": "models/detection/sonar_yolov8_fls_trained.pt",
        "status": "READY",
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "checkpoint_experiment": "exp01_sonar_aug_adamw_640",
    }

    out_metrics = dest_dir_p / "fls_model_metrics.json"
    with open(out_metrics, "w", encoding="utf-8") as f:
        json.dump(metrics_manifest, f, indent=2)

    print(f"Updated metrics manifest at {out_metrics}")
    return metrics_manifest


if __name__ == "__main__":
    promote_model_to_production()
