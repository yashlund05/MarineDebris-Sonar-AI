"""
MarineDebris-Sonar-AI: Subgroup Analysis Module
Evaluates detection performance across critical acoustic and geometric subgroups:
1. Target Size: Small (<40 px), Medium (40-100 px), Large (>100 px)
2. Acoustic Range: Near (<2m), Mid (2-3.5m), Far (>3.5m)
3. Target Contrast / Intensity: Faint (low backscatter contrast) vs Normal
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import cv2
import numpy as np
from ultralytics import YOLO

from backend.ml.optimization.utils import ROOT_DIR
from backend.ml.evaluation.evaluation_contract import (
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
    CANONICAL_IMAGE_SIZE,
)


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """Computes IoU between two boxes in xyxy format."""
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area1 = max(0.0, box1[2] - box1[0]) * max(0.0, box1[3] - box1[1])
    area2 = max(0.0, box2[2] - box2[0]) * max(0.0, box2[3] - box2[1])
    union = area1 + area2 - inter

    return inter / union if union > 0 else 0.0


class SubgroupAnalyzer:
    def __init__(self, conf: float = OPERATIONAL_MISSION_CONF, iou: float = OPERATIONAL_MISSION_IOU):
        self.conf = conf
        self.iou = iou

    def analyze_dataset(self, model_path: Path, data_dir: Path, split: str = "test") -> Dict[str, Any]:
        """
        Runs subgroup analysis over a dataset split.
        data_dir must contain images/<split> and labels/<split>.
        """
        model_path = Path(model_path)
        data_dir = Path(data_dir)
        img_dir = data_dir / "images" / split
        lbl_dir = data_dir / "labels" / split

        if not img_dir.exists():
            return {"error": f"Image directory {img_dir} does not exist"}

        model = YOLO(str(model_path))

        # Subgroup counters: {subgroup: {"total": N, "detected": K, "confidences": []}}
        subgroups = {
            "small_lt_40px": {"total": 0, "detected": 0, "confidences": []},
            "medium_40_100px": {"total": 0, "detected": 0, "confidences": []},
            "large_gt_100px": {"total": 0, "detected": 0, "confidences": []},
            "far_range_gt_3_5m": {"total": 0, "detected": 0, "confidences": []},
            "mid_range_2_to_3_5m": {"total": 0, "detected": 0, "confidences": []},
            "near_range_lt_2m": {"total": 0, "detected": 0, "confidences": []},
            "faint_low_contrast": {"total": 0, "detected": 0, "confidences": []},
            "normal_contrast": {"total": 0, "detected": 0, "confidences": []},
        }

        image_files = sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")))
        total_gt = 0
        total_tp = 0

        for img_p in image_files:
            lbl_p = lbl_dir / f"{img_p.stem}.txt"
            if not lbl_p.exists():
                continue

            img = cv2.imread(str(img_p))
            if img is None:
                continue
            h_img, w_img = img.shape[:2]
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

            # Parse GT boxes (class, x_c, y_c, w, h in normalized coords)
            gt_boxes = []
            with open(lbl_p, "r", encoding="utf-8") as lf:
                for line in lf:
                    parts = line.strip().split()
                    if len(parts) == 5:
                        cls_id = int(parts[0])
                        xc, yc, bw, bh = map(float, parts[1:])
                        # Convert to absolute pixel coordinates
                        x1 = (xc - bw / 2.0) * w_img
                        y1 = (yc - bh / 2.0) * h_img
                        x2 = (xc + bw / 2.0) * w_img
                        y2 = (yc + bh / 2.0) * h_img
                        gt_boxes.append({
                            "class": cls_id,
                            "norm": [xc, yc, bw, bh],
                            "xyxy": [x1, y1, x2, y2],
                            "max_dim_px": max(bw * 640.0, bh * 640.0),
                            "yc": yc,
                        })

            if not gt_boxes:
                continue

            # Predict detections
            res = model.predict(str(img_p), imgsz=CANONICAL_IMAGE_SIZE, conf=self.conf, iou=self.iou, verbose=False)[0]
            preds = []
            if res.boxes is not None and len(res.boxes) > 0:
                xyxy = res.boxes.xyxy.cpu().numpy()
                confs = res.boxes.conf.cpu().numpy()
                classes = res.boxes.cls.cpu().numpy()
                # Scale predictions if img was resized
                scale_x = w_img / 640.0
                scale_y = h_img / 640.0
                for i in range(len(xyxy)):
                    preds.append({
                        "xyxy": [
                            xyxy[i][0] * scale_x,
                            xyxy[i][1] * scale_y,
                            xyxy[i][2] * scale_x,
                            xyxy[i][3] * scale_y,
                        ],
                        "conf": float(confs[i]),
                        "class": int(classes[i]),
                    })

            # Match GT to predictions (greedy matching)
            matched_pred_indices = set()
            for gt in gt_boxes:
                total_gt += 1
                best_iou = 0.0
                best_pred_idx = -1
                best_conf = 0.0

                for p_idx, pred in enumerate(preds):
                    if p_idx in matched_pred_indices:
                        continue
                    iou_val = calculate_iou(gt["xyxy"], pred["xyxy"])
                    if iou_val > best_iou:
                        best_iou = iou_val
                        best_pred_idx = p_idx
                        best_conf = pred["conf"]

                is_detected = (best_iou >= 0.50)
                if is_detected:
                    matched_pred_indices.add(best_pred_idx)
                    total_tp += 1

                # Determine subgroups for this GT
                dim_px = gt["max_dim_px"]
                if dim_px < 40.0:
                    size_key = "small_lt_40px"
                elif dim_px <= 100.0:
                    size_key = "medium_40_100px"
                else:
                    size_key = "large_gt_100px"

                yc = gt["yc"]
                if yc < 0.35:
                    range_key = "far_range_gt_3_5m"
                elif yc <= 0.65:
                    range_key = "mid_range_2_to_3_5m"
                else:
                    range_key = "near_range_lt_2m"

                # Contrast estimation (target region vs surrounding ring)
                gx1, gy1, gx2, gy2 = map(int, gt["xyxy"])
                gx1 = max(0, min(w_img - 1, gx1))
                gx2 = max(0, min(w_img, gx2))
                gy1 = max(0, min(h_img - 1, gy1))
                gy2 = max(0, min(h_img, gy2))

                patch = gray[gy1:gy2, gx1:gx2]
                if patch.size > 0:
                    target_mean = float(np.mean(patch))
                    # Background ring
                    rx1 = max(0, gx1 - 10)
                    ry1 = max(0, gy1 - 10)
                    rx2 = min(w_img, gx2 + 10)
                    ry2 = min(h_img, gy2 + 10)
                    surround = gray[ry1:ry2, rx1:rx2]
                    bg_mean = float(np.mean(surround)) if surround.size > 0 else 0.0
                    contrast = abs(target_mean - bg_mean) / (bg_mean + 1e-5)
                else:
                    contrast = 0.5

                contrast_key = "faint_low_contrast" if contrast < 0.20 else "normal_contrast"

                for k in [size_key, range_key, contrast_key]:
                    subgroups[k]["total"] += 1
                    if is_detected:
                        subgroups[k]["detected"] += 1
                        subgroups[k]["confidences"].append(best_conf)

        # Summarize results
        summary = {
            "total_gt_boxes": total_gt,
            "total_true_positives": total_tp,
            "overall_recall": round(total_tp / total_gt, 4) if total_gt > 0 else 0.0,
            "subgroups": {},
        }

        for k, v in subgroups.items():
            tot = v["total"]
            det = v["detected"]
            rec = round(det / tot, 4) if tot > 0 else 0.0
            mean_conf = round(float(np.mean(v["confidences"])), 4) if v["confidences"] else 0.0
            summary["subgroups"][k] = {
                "total_gt": tot,
                "detected": det,
                "recall": rec,
                "mean_tp_confidence": mean_conf,
            }

        return summary
