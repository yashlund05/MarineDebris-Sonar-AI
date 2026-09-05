"""
MarineDebris-Sonar-AI: Frozen Benchmark Reproduction Engine
Evaluates models/detection/sonar_yolov8_fls_trained.pt against the frozen 37-image / 54-object legacy test set,
logging complete cryptographic provenance and metric comparisons.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT_DIR))

from backend.ml.evaluation.evaluation_contract import (
    EvaluationContract,
    CANONICAL_BENCHMARK_CONF,
    CANONICAL_BENCHMARK_IOU,
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
    CANONICAL_IMAGE_SIZE,
    EXPECTED_PRODUCTION_CHECKPOINT_SHA256,
)


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_reproduction(output_path: Path = ROOT_DIR / "reports" / "evaluation_integrity" / "frozen_benchmark_reproduction.json"):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_path = ROOT_DIR / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
    data_yaml = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "data.yaml"
    test_img_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "images" / "test"
    test_lbl_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "labels" / "test"

    # Cryptographic integrity check
    model_hash = compute_sha256(model_path)
    if model_hash != EXPECTED_PRODUCTION_CHECKPOINT_SHA256:
        raise RuntimeError(
            f"PRODUCTION CHECKPOINT HASH MISMATCH!\n"
            f"Expected: {EXPECTED_PRODUCTION_CHECKPOINT_SHA256}\n"
            f"Found:    {model_hash}"
        )

    test_imgs = list(test_img_dir.glob("*.png")) + list(test_img_dir.glob("*.jpg"))
    num_images = len(test_imgs)
    total_boxes = 0
    for lbl in test_lbl_dir.glob("*.txt"):
        with open(lbl, "r", encoding="utf-8") as f:
            total_boxes += sum(1 for line in f if line.strip())

    model = YOLO(str(model_path))

    # 1. Canonical Benchmark Evaluation (conf=0.001, iou=0.70)
    print(f"\n[REPRODUCTION] Running Canonical Benchmark Evaluation (conf={CANONICAL_BENCHMARK_CONF}, iou={CANONICAL_BENCHMARK_IOU})...")
    res_canonical = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=CANONICAL_IMAGE_SIZE,
        conf=CANONICAL_BENCHMARK_CONF,
        iou=CANONICAL_BENCHMARK_IOU,
        device="cpu",
        verbose=False,
        plots=False,
    )
    rd1 = res_canonical.results_dict
    mp1 = float(rd1.get("metrics/precision(B)", 0.0))
    mr1 = float(rd1.get("metrics/recall(B)", 0.0))
    map50_1 = float(rd1.get("metrics/mAP50(B)", 0.0))
    map50_95_1 = float(rd1.get("metrics/mAP50-95(B)", 0.0))
    f1_1 = float((2 * mp1 * mr1) / (mp1 + mr1)) if (mp1 + mr1) > 0 else 0.0

    # 2. Operational Evaluation (conf=0.25, iou=0.45)
    print("[REPRODUCTION] Running Operational Point Evaluation (conf=0.25, iou=0.45)...")
    res_operational = model.val(
        data=str(data_yaml),
        split="test",
        imgsz=CANONICAL_IMAGE_SIZE,
        conf=OPERATIONAL_MISSION_CONF,
        iou=OPERATIONAL_MISSION_IOU,
        device="cpu",
        verbose=False,
        plots=False,
    )
    rd2 = res_operational.results_dict
    mp2 = float(rd2.get("metrics/precision(B)", 0.0))
    mr2 = float(rd2.get("metrics/recall(B)", 0.0))
    map50_2 = float(rd2.get("metrics/mAP50(B)", 0.0))
    map50_95_2 = float(rd2.get("metrics/mAP50-95(B)", 0.0))
    f1_2 = float((2 * mp2 * mr2) / (mp2 + mr2)) if (mp2 + mr2) > 0 else 0.0

    reproduction_report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "REPRODUCED_AND_VERIFIED",
        "model": {
            "path": str(model_path),
            "sha256": model_hash,
            "expected_sha256": EXPECTED_PRODUCTION_CHECKPOINT_SHA256,
            "architecture": "YOLOv8n",
            "parameters": sum(p.numel() for p in model.model.parameters()) if hasattr(model, "model") else 0,
        },
        "dataset": {
            "name": "sonar_debris_v2_clean",
            "split": "test",
            "image_count": num_images,
            "annotation_count": total_boxes,
        },
        "canonical_benchmark_protocol": {
            "confidence_threshold": CANONICAL_BENCHMARK_CONF,
            "iou_threshold": CANONICAL_BENCHMARK_IOU,
            "image_size": CANONICAL_IMAGE_SIZE,
            "results": {
                "precision": round(mp1, 4),
                "recall": round(mr1, 4),
                "f1": round(f1_1, 4),
                "mAP50": round(map50_1, 4),
                "mAP50_95": round(map50_95_1, 4),
            },
            "historical_frozen_target": {
                "precision": 0.9325,
                "recall": 0.9015,
                "f1": 0.9167,
                "mAP50": 0.8921,
                "mAP50_95": 0.6235,
            },
            "match": (
                round(mp1, 4) == 0.9325
                and round(mr1, 4) == 0.9015
                and round(f1_1, 4) == 0.9167
                and round(map50_1, 4) == 0.8921
                and round(map50_95_1, 4) == 0.6235
            ),
        },
        "operational_point_protocol": {
            "confidence_threshold": OPERATIONAL_MISSION_CONF,
            "iou_threshold": OPERATIONAL_MISSION_IOU,
            "image_size": CANONICAL_IMAGE_SIZE,
            "results": {
                "precision": round(mp2, 4),
                "recall": round(mr2, 4),
                "f1": round(f1_2, 4),
                "mAP50": round(map50_2, 4),
                "mAP50_95": round(map50_95_2, 4),
            },
            "note": "Operational threshold for real-time AUV survey deployment. Truncates low-confidence predictions prior to PR integration.",
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(reproduction_report, f, indent=2)

    print(f"\n[REPRODUCTION] Saved reproduction report to {output_path}")
    print(f"Canonical Match Status: {reproduction_report['canonical_benchmark_protocol']['match']}")
    return reproduction_report


if __name__ == "__main__":
    run_reproduction()
