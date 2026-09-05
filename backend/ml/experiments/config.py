"""
MarineDebris-Sonar-AI: Experiment Configuration and Promotion Governance
Defines formal promotion tolerances, immutable baseline locks, and paths.
Enforces hard programmatic protection over production weights and legacy benchmarks.
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

ROOT_DIR = Path(__file__).resolve().parents[3]
BASELINE_DATASET_PATH = ROOT_DIR / "datasets" / "sonar_debris_v2_clean"
PRODUCTION_MODEL_PATH = ROOT_DIR / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
FROZEN_PRODUCTION_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"
PRODUCTION_MODEL_SHA256 = FROZEN_PRODUCTION_SHA256
PROTECTION_LOCK_FILE = ROOT_DIR / "reports" / "model_optimization" / "PROTECTION_LOCK"

BASELINE_DATASET_FROZEN: bool = True
PRODUCTION_MODEL_FROZEN: bool = True


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_production_lock() -> Dict[str, Any]:
    """
    Guarantees baseline dataset and production model weights remain untouched.
    Fails loudly with RuntimeError if any modification or tampering is detected.
    """
    if not BASELINE_DATASET_FROZEN:
        raise RuntimeError("CRITICAL VIOLATION: BASELINE_DATASET_FROZEN is False!")
    if not PRODUCTION_MODEL_FROZEN:
        raise RuntimeError("CRITICAL VIOLATION: PRODUCTION_MODEL_FROZEN is False!")

    if not BASELINE_DATASET_PATH.exists():
        raise RuntimeError(f"CRITICAL VIOLATION: Baseline dataset missing at {BASELINE_DATASET_PATH}")
    if not PRODUCTION_MODEL_PATH.exists():
        raise RuntimeError(f"CRITICAL VIOLATION: Production model missing at {PRODUCTION_MODEL_PATH}")

    # Verify legacy test split has exactly 37 images and 54 annotations
    test_img_dir = BASELINE_DATASET_PATH / "images" / "test"
    test_lbl_dir = BASELINE_DATASET_PATH / "labels" / "test"
    test_imgs = list(test_img_dir.glob("*.png")) + list(test_img_dir.glob("*.jpg"))
    if len(test_imgs) != 37:
        raise RuntimeError(f"CRITICAL VIOLATION: Legacy test set count altered! Expected 37, found {len(test_imgs)}")

    total_boxes = 0
    for lbl in test_lbl_dir.glob("*.txt"):
        with open(lbl, "r", encoding="utf-8") as f:
            total_boxes += sum(1 for line in f if line.strip())
    if total_boxes != 54:
        raise RuntimeError(f"CRITICAL VIOLATION: Legacy test annotations altered! Expected 54, found {total_boxes}")

    # Verify production model SHA256
    current_sha = compute_sha256(PRODUCTION_MODEL_PATH)
    if current_sha != FROZEN_PRODUCTION_SHA256:
        raise RuntimeError(
            f"CRITICAL VIOLATION: Production model weights tampered or overwritten!\n"
            f"Expected SHA256: {FROZEN_PRODUCTION_SHA256}\n"
            f"Observed SHA256: {current_sha}"
        )

    return {
        "baseline_dataset_frozen": True,
        "production_model_frozen": True,
        "legacy_test_images": 37,
        "legacy_test_boxes": 54,
        "production_model_sha256": current_sha,
        "status": "LOCKED_AND_VERIFIED",
    }


@dataclass
class PromotionCriteria:
    max_legacy_map50_regression: float = 0.015  # Max 1.5% drop on legacy benchmark
    max_legacy_f1_regression: float = 0.020     # Max 2.0% drop on legacy F1
    min_v3_map50_gain: float = 0.005           # Min 0.5% gain on V3 test split
    max_hard_negative_far: float = 0.050       # Max 5.0% false alarm rate on negative clutter
    max_cpu_latency_ms: float = 125.0          # Latency ceiling (min 8 FPS)
    min_reproducibility_seeds: int = 3         # Consistency across 3 seeds


@dataclass
class ExperimentConfig:
    experiment_id: str
    description: str
    category: str  # baseline, v3_control, balanced, hard_negative, domain_balanced, small_object
    data_yaml: str
    base_model: str = "yolov8n.pt"
    imgsz: int = 640
    batch_size: int = 16
    epochs: int = 20
    lr0: float = 0.001
    lrf: float = 0.01
    optimizer: str = "AdamW"
    weight_decay: float = 0.0005
    box_loss_weight: float = 7.5
    cls_loss_weight: float = 0.5
    dfl_loss_weight: float = 1.5
    hsv_v: float = 0.15
    degrees: float = 5.0
    translate: float = 0.05
    scale: float = 0.10
    fliplr: float = 0.50
    flipud: float = 0.00
    mosaic: float = 0.20
    seed: int = 42
    device: str = "cpu"
    output_dir: str = "ml/experiments"
