"""
Detector Utility & Profile Validation Benchmark for Sonar Image Enhancement.

Evaluates operational enhancement profiles (RAW, AI_SAFE, HUMAN_VISUAL, BALANCED)
against the frozen YOLOv8n-FLS production model on authorized V3 validation samples.

Scientific Invariants:
1. Production model checkpoint (sonar_yolov8_fls_trained.pt) is 100% immutable.
2. Model SHA256 verified before and after execution.
3. Decoupled presentation: only canonical single-channel grayscale replicated to 3 channels
   is supplied to the detector. NEVER colormapped/pseudocolor images.
4. Ground truth derived strictly from dataset labels; zero metric fabrication.
"""

import sys
import os
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Tuple, Any
import numpy as np
import cv2

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.enhancement.data_loader import BenchmarkDatasetLoader
from backend.enhancement.profiles import build_pipeline_for_profile, StandardProfile
from backend.enhancement.pipeline_base import (
    SonarEnhancementContext,
    ProcessingMode,
    Modality,
    SignalRepresentation,
)
from backend.enhancement.inspection import inspect_sonar_input
from backend.inference.model_loader import ModelLoader

PRODUCTION_CHECKPOINT = PROJECT_ROOT / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
EXPECTED_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "sonar_enhancement"


def calculate_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def compute_iou(boxA: Tuple[float, float, float, float], boxB: Tuple[float, float, float, float]) -> float:
    cxA, cyA, wA, hA = boxA
    cxB, cyB, wB, hB = boxB

    xA1, yA1 = cxA - wA / 2.0, cyA - hA / 2.0
    xA2, yA2 = cxA + wA / 2.0, cyA + hA / 2.0
    xB1, yB1 = cxB - wB / 2.0, cyB - hB / 2.0
    xB2, yB2 = cxB + wB / 2.0, cyB + hB / 2.0

    inter_x1 = max(xA1, xB1)
    inter_y1 = max(yA1, yB1)
    inter_x2 = min(xA2, xB2)
    inter_y2 = min(yA2, yB2)

    inter_w = max(0.0, inter_x2 - inter_x1)
    inter_h = max(0.0, inter_y2 - inter_y1)
    inter_area = inter_w * inter_h

    areaA = wA * hA
    areaB = wB * hB
    union_area = areaA + areaB - inter_area

    if union_area <= 0:
        return 0.0
    return inter_area / union_area


def run_profile_benchmark(sample_limit: int = 25):
    print("=" * 78)
    print("     OPERATIONAL PROFILES DETECTOR UTILITY VALIDATION BENCHMARK")
    print("=" * 78)

    # 1. Model Integrity Check
    if not PRODUCTION_CHECKPOINT.exists():
        print(f"[ERROR] Checkpoint not found at {PRODUCTION_CHECKPOINT}")
        sys.exit(1)

    initial_sha = calculate_sha256(PRODUCTION_CHECKPOINT)
    print(f"Model Checkpoint: {PRODUCTION_CHECKPOINT.name}")
    print(f"SHA256:           {initial_sha}")
    if initial_sha != EXPECTED_SHA256:
        print(f"[ERROR] SHA256 mismatch! Expected {EXPECTED_SHA256}, got {initial_sha}")
        sys.exit(1)
    print("[INTEGRITY] Model SHA256 matches production contract.")

    # 2. Load Model
    print("\n[SETUP] Loading YOLOv8n-FLS detector into memory...")
    model = ModelLoader.load_detection_model(str(PRODUCTION_CHECKPOINT))
    print(f"[SETUP] Device: {ModelLoader.get_device()}")

    # 3. Load Validation Dataset
    loader = BenchmarkDatasetLoader(PROJECT_ROOT / "datasets")
    all_val_samples = loader.get_development_samples(dataset_version="v3", split="val")
    val_samples = all_val_samples[:sample_limit]
    print(f"[DATASET] Evaluating on {len(val_samples)} validation samples (limit={sample_limit}).")

    # Profiles to benchmark
    profiles_to_test = [
        ("RAW", StandardProfile.RAW.value, ProcessingMode.AI_SAFE, "Raw Baseline (Control)"),
        ("AI_SAFE", StandardProfile.AI_SAFE.value, ProcessingMode.AI_SAFE, "AI-Safe Profile"),
        ("BALANCED", StandardProfile.BALANCED.value, ProcessingMode.AI_SAFE, "Balanced Profile"),
        ("HUMAN_VISUAL", StandardProfile.HUMAN_VISUAL.value, ProcessingMode.HUMAN_DISPLAY, "Human Visual Inspection"),
    ]

    results = {}

    for profile_key, profile_enum_val, proc_mode, desc in profiles_to_test:
        print(f"\nEvaluating profile: {desc} [{profile_key}] (Mode: {proc_mode.value})...")
        pipeline = build_pipeline_for_profile(profile_enum_val, mode=proc_mode)

        total_gt = 0
        total_pred = 0
        tp = 0
        fp = 0
        latencies = []

        for sample in val_samples:
            img_path = sample["image_path"]
            raw_float = loader.load_image_float32(img_path)
            gt_boxes = sample["boxes"]
            total_gt += len(gt_boxes)

            # Context
            insp = inspect_sonar_input(raw_float)
            ctx = SonarEnhancementContext(
                artifact_id=sample["image_name"],
                modality=insp.modality,
                representation=insp.detected_representation,
                mode=proc_mode,
                metadata={"raw_image": raw_float},
            )

            # Execute enhancement pipeline
            t0 = time.perf_counter()
            enh_res = pipeline.execute(raw_float, ctx)
            t_enhance_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(t_enhance_ms)

            # Replicate 1-ch canonical float32 to 3-ch uint8 for YOLO
            uint8_gray = (np.clip(enh_res.canonical_image, 0.0, 1.0) * 255.0).astype(np.uint8)
            uint8_3ch = cv2.cvtColor(uint8_gray, cv2.COLOR_GRAY2BGR)

            # Inference
            pred_results = model.predict(uint8_3ch, conf=0.25, iou=0.45, verbose=False)
            pred_boxes = []
            if pred_results and len(pred_results) > 0:
                boxes_obj = pred_results[0].boxes
                if boxes_obj is not None and len(boxes_obj) > 0:
                    xywhn = boxes_obj.xywhn.cpu().numpy()
                    confs = boxes_obj.conf.cpu().numpy()
                    classes = boxes_obj.cls.cpu().numpy()
                    for box, c_score, cls_idx in zip(xywhn, confs, classes):
                        pred_boxes.append((int(cls_idx), float(box[0]), float(box[1]), float(box[2]), float(box[3]), float(c_score)))

            total_pred += len(pred_boxes)

            # Match detections to GT (greedy IoU >= 0.45)
            matched_gt = set()
            for p_cls, pcx, pcy, pw, ph, pconf in pred_boxes:
                best_iou = 0.0
                best_gt_idx = -1
                for gt_idx, (gt_cls, gcx, gcy, gw, gh) in enumerate(gt_boxes):
                    if gt_idx in matched_gt:
                        continue
                    if gt_cls != p_cls:
                        continue
                    iou = compute_iou((pcx, pcy, pw, ph), (gcx, gcy, gw, gh))
                    if iou > best_iou:
                        best_iou = iou
                        best_gt_idx = gt_idx

                if best_iou >= 0.45 and best_gt_idx >= 0:
                    tp += 1
                    matched_gt.add(best_gt_idx)
                else:
                    fp += 1

        fn = total_gt - tp
        precision = tp / max(total_pred, 1)
        recall = tp / max(total_gt, 1)
        f1 = (2 * precision * recall) / max(precision + recall, 1e-6)

        results[profile_key] = {
            "description": desc,
            "profile": profile_key,
            "mode": proc_mode.value,
            "total_gt": total_gt,
            "total_pred": total_pred,
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "mean_latency_ms": round(float(np.mean(latencies)), 2),
            "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2),
        }

        print(f"  Precision: {precision:.4f} | Recall: {recall:.4f} | F1: {f1:.4f} | Latency: {np.mean(latencies):.2f} ms")

    # Post-execution Checkpoint Verification
    final_sha = calculate_sha256(PRODUCTION_CHECKPOINT)
    assert final_sha == EXPECTED_SHA256, "CRITICAL: Model checkpoint modified during benchmark!"
    print("\n[VERIFICATION] Checkpoint SHA256 verified unchanged after benchmark.")

    # Save benchmark report
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_file = OUTPUT_DIR / "profile_detector_utility_report.md"
    json_file = OUTPUT_DIR / "profile_detector_utility_results.json"

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # Markdown Table
    lines = [
        "# Sonar Enhancement Profile Detector Utility Report",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}",
        f"**Model Checkpoint**: `{PRODUCTION_CHECKPOINT.name}` (`{EXPECTED_SHA256[:12]}...`)",
        f"**Validation Frames**: {len(val_samples)} from `datasets/sonar_debris_v3/val`",
        "",
        "## Quantitative Performance Summary",
        "",
        "| Profile | Mode | Precision | Recall | F1 Score | Δ F1 vs Raw | Mean Latency |",
        "|---|---|---|---|---|---|---|",
    ]

    raw_f1 = results.get("RAW", {}).get("f1_score", 0.0)

    for p_key, data in results.items():
        diff_f1 = data["f1_score"] - raw_f1
        diff_str = f"{diff_f1:+.4f}" if p_key != "RAW" else "baseline"
        lines.append(
            f"| **{p_key}** | `{data['mode']}` | {data['precision']:.4f} | {data['recall']:.4f} | "
            f"**{data['f1_score']:.4f}** | {diff_str} | {data['mean_latency_ms']:.2f} ms |"
        )

    lines.extend([
        "",
        "## Architectural Findings & Recommendations",
        "- **AI_SAFE Profile**: Calibrated with conservative speckle reduction and strict shadow preservation.",
        "- **HUMAN_VISUAL Profile**: Optimized for operator clarity with controlled CLAHE and edge definition.",
        "- **Frozen Invariant**: Production YOLOv8 weights remain unaltered; SHA-256 integrity verified.",
    ])

    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"\n[OUTPUT] Report written to: {report_file}")
    return results


if __name__ == "__main__":
    run_profile_benchmark(sample_limit=15)
