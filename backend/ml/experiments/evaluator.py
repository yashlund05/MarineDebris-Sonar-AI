"""
MarineDebris-Sonar-AI: Multi-Benchmark Standardized Evaluator
Evaluates candidate models independently across:
1. Benchmark 1: Legacy V2 Held-out Control (37 images, 54 annotations)
2. Benchmark 2: Dataset V3 Held-out Generalization (80 images, 127 annotations)
3. Benchmark 3: Hard-Negative Clutter Suppression (84 verified empty/clutter frames)
4. Benchmark 4: Cross-Domain & Auxiliary Sonar Benchmark
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import cv2
import torch
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[3]


class MultiBenchmarkEvaluator:
    def __init__(
        self,
        legacy_data_yaml: Path = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "data.yaml",
        v3_data_yaml: Path = ROOT_DIR / "datasets" / "sonar_debris_v3" / "data.yaml",
        cross_domain_yaml: Path = ROOT_DIR / "datasets" / "sonar_debris_v3" / "variants" / "v3_c" / "data.yaml",
        hard_negatives_dir: Path = ROOT_DIR / "datasets" / "sonar_debris_v3" / "hard_negatives",
    ):
        self.legacy_data_yaml = Path(legacy_data_yaml)
        self.v3_data_yaml = Path(v3_data_yaml)
        self.cross_domain_yaml = Path(cross_domain_yaml)
        self.hard_negatives_dir = Path(hard_negatives_dir)

    def evaluate_yolo_split(
        self,
        model: YOLO,
        data_yaml: Path,
        split: str = "test",
        imgsz: int = 640,
        batch: int = 8,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> Dict[str, Any]:
        """Runs standard evaluation on a data.yaml split."""
        results = model.val(
            data=str(data_yaml),
            split=split,
            imgsz=imgsz,
            batch=batch,
            conf=conf,
            iou=iou,
            device="cpu",
            verbose=False,
            plots=False,
        )
        rd = results.results_dict
        mp = float(rd.get("metrics/precision(B)", 0.0))
        mr = float(rd.get("metrics/recall(B)", 0.0))
        map50 = float(rd.get("metrics/mAP50(B)", 0.0))
        map50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
        f1 = float((2 * mp * mr) / (mp + mr)) if (mp + mr) > 0 else 0.0

        # Extract per-class
        per_class = {}
        if hasattr(results, "box") and results.box is not None:
            box = results.box
            names = results.names
            for c_idx, c_name in names.items():
                if hasattr(box, "ap50") and box.ap50 is not None and c_idx < len(box.ap50):
                    per_class[c_name] = {
                        "mAP50": round(float(box.ap50[c_idx]), 4),
                        "mAP50_95": round(float(box.ap[c_idx]), 4) if hasattr(box, "ap") and c_idx < len(box.ap) else 0.0,
                    }

        return {
            "precision": round(mp, 4),
            "recall": round(mr, 4),
            "f1": round(f1, 4),
            "mAP50": round(map50, 4),
            "mAP50_95": round(map50_95, 4),
            "per_class": per_class,
        }

    def evaluate_hard_negatives(
        self,
        model: YOLO,
        imgsz: int = 640,
        conf: float = 0.25,
    ) -> Dict[str, Any]:
        """Evaluates model on genuine negative seabed and wall clutter images."""
        if not self.hard_negatives_dir.exists():
            return {"status": "SKIPPED_NOT_FOUND", "false_alarm_rate": 0.0, "total_negatives": 0}

        neg_images = list(self.hard_negatives_dir.glob("*.png")) + list(self.hard_negatives_dir.glob("*.jpg"))
        if not neg_images:
            return {"status": "NO_IMAGES", "false_alarm_rate": 0.0, "total_negatives": 0}

        total_images = len(neg_images)
        images_with_false_positives = 0
        total_false_positives = 0
        quarry_fps = 0
        wall_fps = 0

        for img_p in neg_images:
            res = model.predict(str(img_p), imgsz=imgsz, conf=conf, verbose=False)
            boxes = res[0].boxes if res and len(res) > 0 else None
            num_boxes = len(boxes) if boxes is not None else 0

            if num_boxes > 0:
                images_with_false_positives += 1
                total_false_positives += num_boxes
                if "frame" in img_p.name or "2016" in img_p.name:
                    quarry_fps += num_boxes
                else:
                    wall_fps += num_boxes

        far = images_with_false_positives / total_images if total_images > 0 else 0.0
        fp_per_image = total_false_positives / total_images if total_images > 0 else 0.0

        return {
            "total_negative_images": total_images,
            "images_with_false_alarms": images_with_false_positives,
            "total_false_positives": total_false_positives,
            "false_alarm_rate": round(far, 4),
            "false_positives_per_image": round(fp_per_image, 4),
            "quarry_false_positives": quarry_fps,
            "wall_false_positives": wall_fps,
            "status": "PASS" if far <= 0.05 else "HIGH_FALSE_ALARMS",
        }

    def run_complete_evaluation(
        self,
        model_path: Path,
        imgsz: int = 640,
        conf: float = 0.25,
        iou: float = 0.45,
    ) -> Dict[str, Any]:
        """Executes complete evaluation suite across all four benchmarks."""
        model = YOLO(str(model_path))

        print(f"[EVAL] Evaluating model {model_path.name} on Legacy V2 Benchmark...")
        legacy_metrics = self.evaluate_yolo_split(model, self.legacy_data_yaml, split="test", imgsz=imgsz, conf=conf, iou=iou)

        print(f"[EVAL] Evaluating model {model_path.name} on Dataset V3 Held-Out Benchmark...")
        v3_metrics = self.evaluate_yolo_split(model, self.v3_data_yaml, split="test", imgsz=imgsz, conf=conf, iou=iou)

        print(f"[EVAL] Evaluating model {model_path.name} on Hard Negatives Clutter Suite...")
        negative_metrics = self.evaluate_hard_negatives(model, imgsz=imgsz, conf=conf)

        print(f"[EVAL] Evaluating model {model_path.name} on Cross-Domain & Auxiliary Suite...")
        cross_domain_metrics = {}
        if self.cross_domain_yaml.exists():
            try:
                cross_domain_metrics = self.evaluate_yolo_split(model, self.cross_domain_yaml, split="test", imgsz=imgsz, conf=conf, iou=iou)
            except Exception as e:
                cross_domain_metrics = {"error": str(e)}

        return {
            "model_path": str(model_path),
            "imgsz": imgsz,
            "conf_threshold": conf,
            "iou_threshold": iou,
            "benchmark_1_legacy_v2": legacy_metrics,
            "benchmark_2_v3_held_out": v3_metrics,
            "benchmark_3_hard_negatives": negative_metrics,
            "benchmark_4_cross_domain": cross_domain_metrics,
        }
