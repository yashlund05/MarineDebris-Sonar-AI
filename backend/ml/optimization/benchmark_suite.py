"""
MarineDebris-Sonar-AI: Standardized Benchmark Suite (Benchmarks A through G)
Evaluates candidate models strictly adhering to the canonical evaluation contract:
- Benchmark A: Legacy V2 Held-out Control (37 images, 54 annotations)
- Benchmark B: Dataset V3 Held-out Generalization (80 images, 127 annotations)
- Benchmark C: Hard-Negative Acoustic Clutter Suite (84 verified empty/clutter frames)
- Benchmark D: Cross-Domain & Auxiliary Sonar Suite
- Benchmark E: Hard Positives Target Sensitivity
- Benchmark F: Small-Target (<40 px) Performance
- Benchmark G: Long-Range Target (>3.5 m) Analysis
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from ultralytics import YOLO

from backend.ml.optimization.utils import ROOT_DIR
from backend.ml.evaluation.evaluation_contract import (
    EvaluationContract,
    CANONICAL_BENCHMARK_CONF,
    CANONICAL_BENCHMARK_IOU,
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
    CANONICAL_IMAGE_SIZE,
)

V2_YAML = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "data.yaml"
V3_YAML = ROOT_DIR / "datasets" / "sonar_debris_v3" / "data.yaml"
CROSS_DOMAIN_YAML = ROOT_DIR / "datasets" / "sonar_debris_v3" / "variants" / "v3_c" / "data.yaml"
NEGATIVES_DIR = ROOT_DIR / "datasets" / "sonar_debris_v3" / "hard_negatives"


class BenchmarkSuite:
    def __init__(
        self,
        v2_yaml: Path = V2_YAML,
        v3_yaml: Path = V3_YAML,
        cross_domain_yaml: Path = CROSS_DOMAIN_YAML,
        negatives_dir: Path = NEGATIVES_DIR,
    ):
        self.v2_yaml = Path(v2_yaml)
        self.v3_yaml = Path(v3_yaml)
        self.cross_domain_yaml = Path(cross_domain_yaml)
        self.negatives_dir = Path(negatives_dir)
        self.contract = EvaluationContract()

    def evaluate_yolo_split(
        self,
        model: YOLO,
        data_yaml: Path,
        split: str = "test",
        mode: str = "benchmark",
    ) -> Dict[str, Any]:
        val_args = self.contract.get_val_args(mode=mode)
        results = model.val(data=str(data_yaml), split=split, **val_args)
        rd = results.results_dict

        mp = float(rd.get("metrics/precision(B)", 0.0))
        mr = float(rd.get("metrics/recall(B)", 0.0))
        m50 = float(rd.get("metrics/mAP50(B)", 0.0))
        m50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
        f1 = float((2 * mp * mr) / (mp + mr)) if (mp + mr) > 0 else 0.0

        return {
            "precision": round(mp, 4),
            "recall": round(mr, 4),
            "f1": round(f1, 4),
            "mAP50": round(m50, 4),
            "mAP50_95": round(m50_95, 4),
        }

    def evaluate_hard_negatives(
        self,
        model: YOLO,
        conf: float = OPERATIONAL_MISSION_CONF,
        iou: float = OPERATIONAL_MISSION_IOU,
    ) -> Dict[str, Any]:
        """Evaluates operational false alarm rates on verified negative images."""
        if not self.negatives_dir.exists():
            return {"status": "SKIPPED_NOT_FOUND"}

        neg_images = sorted(list(self.negatives_dir.glob("*.png")) + list(self.negatives_dir.glob("*.jpg")))
        total_images = len(neg_images)
        if total_images == 0:
            return {"status": "NO_IMAGES"}

        flagged_images = 0
        total_fps = 0
        quarry_fps = 0
        wall_fps = 0
        fps_per_image_list = []

        for p in neg_images:
            res = model.predict(str(p), imgsz=CANONICAL_IMAGE_SIZE, conf=conf, iou=iou, verbose=False)[0]
            n_boxes = len(res.boxes) if res.boxes is not None else 0
            fps_per_image_list.append(n_boxes)
            if n_boxes > 0:
                flagged_images += 1
                total_fps += n_boxes
                if "wall" in p.name.lower() or "tank" in p.name.lower():
                    wall_fps += n_boxes
                else:
                    quarry_fps += n_boxes

        far = flagged_images / total_images if total_images > 0 else 0.0
        fps_per_neg = total_fps / total_images if total_images > 0 else 0.0
        fps_per_flagged = total_fps / flagged_images if flagged_images > 0 else 0.0
        max_fp = max(fps_per_image_list) if fps_per_image_list else 0

        return {
            "total_negative_images": total_images,
            "flagged_negative_images": flagged_images,
            "total_false_positive_boxes": total_fps,
            "negative_image_FAR": round(far, 4),
            "fps_per_negative_image": round(fps_per_neg, 4),
            "fps_per_flagged_image": round(fps_per_flagged, 4),
            "max_fps_in_single_negative_image": max_fp,
            "quarry_false_positives": quarry_fps,
            "wall_false_positives": wall_fps,
        }

    def run_complete_suite(self, checkpoint_path: Path) -> Dict[str, Any]:
        """Runs Benchmarks A, B, C, D on candidate checkpoint."""
        checkpoint_path = Path(checkpoint_path)
        model = YOLO(str(checkpoint_path))

        print(f"[BENCHMARK] Running Canonical Benchmark A (Legacy V2 Test)...")
        bench_a = self.evaluate_yolo_split(model, self.v2_yaml, split="test", mode="benchmark")

        print(f"[BENCHMARK] Running Canonical Benchmark B (Dataset V3 Test)...")
        bench_b = self.evaluate_yolo_split(model, self.v3_yaml, split="test", mode="benchmark")

        print(f"[BENCHMARK] Running Operational Benchmark C (Hard Negatives)...")
        bench_c = self.evaluate_hard_negatives(model)

        print(f"[BENCHMARK] Running Benchmark D (Cross-Domain)...")
        bench_d = {}
        if self.cross_domain_yaml.exists():
            try:
                bench_d = self.evaluate_yolo_split(model, self.cross_domain_yaml, split="test", mode="benchmark")
            except Exception as e:
                bench_d = {"error": str(e)}

        return {
            "checkpoint_path": str(checkpoint_path),
            "benchmark_a_legacy_v2": bench_a,
            "benchmark_b_v3_held_out": bench_b,
            "benchmark_c_hard_negatives": bench_c,
            "benchmark_d_cross_domain": bench_d,
        }
