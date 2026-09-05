"""
MarineDebris-Sonar-AI: Hard-Positive and Failure Mining Engine
Inspects training and validation pools (strictly excluding the legacy test benchmark)
to identify missed debris, low-confidence detections, tiny targets, and boundary false alarms.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import cv2
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[3]


def box_iou(b1, b2):
    # b1, b2 are [xc, yc, w, h] normalized
    x1_min = b1[0] - b1[2] / 2
    x1_max = b1[0] + b1[2] / 2
    y1_min = b1[1] - b1[3] / 2
    y1_max = b1[1] + b1[3] / 2

    x2_min = b2[0] - b2[2] / 2
    x2_max = b2[0] + b2[2] / 2
    y2_min = b2[1] - b2[3] / 2
    y2_max = b2[1] + b2[3] / 2

    xi_min = max(x1_min, x2_min)
    yi_min = max(y1_min, y2_min)
    xi_max = min(x1_max, x2_max)
    yi_max = min(y1_max, y2_max)

    inter_w = max(0.0, xi_max - xi_min)
    inter_h = max(0.0, yi_max - yi_min)
    inter_area = inter_w * inter_h

    area1 = b1[2] * b1[3]
    area2 = b2[2] * b2[3]
    union = area1 + area2 - inter_area
    return inter_area / union if union > 0 else 0.0


class HardPositiveMiner:
    def __init__(self, model_path: Path):
        self.model_path = Path(model_path)
        self.model = YOLO(str(self.model_path))

    def mine_failures(
        self,
        dataset_root: Path = ROOT_DIR / "datasets" / "sonar_debris_v3",
        splits: List[str] = ["train", "val"],
        conf_threshold: float = 0.25,
        iou_match_threshold: float = 0.45,
    ) -> Dict[str, Any]:
        """
        Scans train and val splits ONLY.
        Identifies hard positives, missed debris, and low-confidence detections.
        """
        print(f"[MINING] Scanning splits {splits} for difficult acoustic targets...")
        hard_positives = []
        missed_debris = []
        low_confidence_hits = []
        tiny_targets = []
        wall_false_positives = []

        total_scanned = 0

        for split in splits:
            img_dir = dataset_root / "images" / split
            lbl_dir = dataset_root / "labels" / split
            if not img_dir.exists():
                continue

            images = sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")))
            for img_p in images:
                total_scanned += 1
                txt_p = lbl_dir / f"{img_p.stem}.txt"

                gt_boxes = []
                if txt_p.exists() and txt_p.stat().st_size > 0:
                    with open(txt_p, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) == 5:
                                cid = int(parts[0])
                                xc, yc, w, h = map(float, parts[1:])
                                max_dim_px = max(w, h) * 640
                                gt_boxes.append({
                                    "class_id": cid,
                                    "bbox": [xc, yc, w, h],
                                    "max_dim_px": round(max_dim_px, 1),
                                    "matched": False,
                                })

                res = self.model.predict(str(img_p), imgsz=640, conf=conf_threshold, verbose=False)
                preds = []
                if res and len(res) > 0 and res[0].boxes:
                    for b in res[0].boxes:
                        c_id = int(b.cls[0].item())
                        conf_val = float(b.conf[0].item())
                        xywhn = b.xywhn[0].tolist()
                        preds.append({"class_id": c_id, "conf": round(conf_val, 4), "bbox": xywhn})

                # Match predictions to GT
                for gt in gt_boxes:
                    best_iou = 0.0
                    best_pred = None
                    for p in preds:
                        iou = box_iou(gt["bbox"], p["bbox"])
                        if iou > best_iou:
                            best_iou = iou
                            best_pred = p

                    if best_iou >= iou_match_threshold:
                        gt["matched"] = True
                        if best_pred and best_pred["conf"] < 0.40:
                            low_confidence_hits.append({
                                "image": img_p.name,
                                "split": split,
                                "gt_class": gt["class_id"],
                                "confidence": best_pred["conf"],
                                "iou": round(best_iou, 3),
                                "max_dim_px": gt["max_dim_px"],
                                "category": "LOW_CONFIDENCE_TRUE_POSITIVE",
                            })
                    else:
                        # Missed target
                        missed_item = {
                            "image": img_p.name,
                            "split": split,
                            "gt_class": gt["class_id"],
                            "max_dim_px": gt["max_dim_px"],
                            "category": "MISSED_DEBRIS_FALSE_NEGATIVE",
                            "scale": "tiny" if gt["max_dim_px"] < 32 else ("small" if gt["max_dim_px"] < 64 else "medium"),
                        }
                        missed_debris.append(missed_item)
                        if gt["max_dim_px"] < 40:
                            tiny_targets.append(missed_item)

                # Unmatched predictions on empty images
                if len(gt_boxes) == 0 and len(preds) > 0:
                    for p in preds:
                        wall_false_positives.append({
                            "image": img_p.name,
                            "split": split,
                            "pred_class": p["class_id"],
                            "confidence": p["conf"],
                            "category": "BACKGROUND_CLUTTER_FALSE_ALARM",
                        })

        summary = {
            "total_images_scanned": total_scanned,
            "missed_debris_count": len(missed_debris),
            "low_confidence_count": len(low_confidence_hits),
            "tiny_missed_count": len(tiny_targets),
            "background_false_alarm_count": len(wall_false_positives),
            "missed_debris_samples": missed_debris[:30],
            "low_confidence_samples": low_confidence_hits[:30],
            "background_false_alarms": wall_false_positives[:30],
        }

        return summary
