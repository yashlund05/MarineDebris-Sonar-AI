"""
MarineDebris-Sonar-AI: Confidence & NMS Threshold Calibration Engine
Evaluates fine-grained confidence and IoU operating points on validation sets,
identifying High-Recall, Balanced, and High-Precision operating modes.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
import numpy as np
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[3]


class ThresholdCalibrator:
    def __init__(self, model_path: Path, data_yaml: Path):
        self.model_path = Path(model_path)
        self.data_yaml = Path(data_yaml)
        self.model = YOLO(str(self.model_path))

    def run_confidence_sweep(
        self,
        thresholds: List[float] = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80],
        split: str = "val",
        imgsz: int = 640,
        iou: float = 0.45,
    ) -> List[Dict[str, Any]]:
        """Sweeps confidence thresholds on validation set."""
        sweep_results = []
        print(f"[CALIB] Sweeping {len(thresholds)} confidence thresholds on split='{split}'...")

        for conf in thresholds:
            res = self.model.val(
                data=str(self.data_yaml),
                split=split,
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                device="cpu",
                verbose=False,
                plots=False,
            )
            rd = res.results_dict
            p = float(rd.get("metrics/precision(B)", 0.0))
            r = float(rd.get("metrics/recall(B)", 0.0))
            m50 = float(rd.get("metrics/mAP50(B)", 0.0))
            m50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
            f1 = float((2 * p * r) / (p + r)) if (p + r) > 0 else 0.0

            sweep_results.append({
                "confidence_threshold": conf,
                "precision": round(p, 4),
                "recall": round(r, 4),
                "f1": round(f1, 4),
                "mAP50": round(m50, 4),
                "mAP50_95": round(m50_95, 4),
            })

        return sweep_results

    def run_nms_sweep(
        self,
        iou_thresholds: List[float] = [0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70],
        conf: float = 0.25,
        split: str = "val",
        imgsz: int = 640,
    ) -> List[Dict[str, Any]]:
        """Sweeps NMS IoU thresholds on validation set."""
        nms_results = []
        print(f"[CALIB] Sweeping {len(iou_thresholds)} NMS IoU thresholds on split='{split}'...")

        for iou in iou_thresholds:
            res = self.model.val(
                data=str(self.data_yaml),
                split=split,
                imgsz=imgsz,
                conf=conf,
                iou=iou,
                device="cpu",
                verbose=False,
                plots=False,
            )
            rd = res.results_dict
            p = float(rd.get("metrics/precision(B)", 0.0))
            r = float(rd.get("metrics/recall(B)", 0.0))
            m50 = float(rd.get("metrics/mAP50(B)", 0.0))
            m50_95 = float(rd.get("metrics/mAP50-95(B)", 0.0))
            f1 = float((2 * p * r) / (p + r)) if (p + r) > 0 else 0.0

            nms_results.append({
                "nms_iou_threshold": iou,
                "precision": round(p, 4),
                "recall": round(r, 4),
                "f1": round(f1, 4),
                "mAP50": round(m50, 4),
                "mAP50_95": round(m50_95, 4),
            })

        return nms_results

    @staticmethod
    def identify_operating_points(conf_sweep: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Selects optimal operating points."""
        # 1. Balanced: Highest F1
        balanced = max(conf_sweep, key=lambda x: x["f1"])

        # 2. High Recall: Max recall where precision >= 0.75
        high_recall_cands = [x for x in conf_sweep if x["precision"] >= 0.75]
        high_recall = max(high_recall_cands, key=lambda x: x["recall"]) if high_recall_cands else conf_sweep[0]

        # 3. High Precision: Max precision where recall >= 0.70
        high_prec_cands = [x for x in conf_sweep if x["recall"] >= 0.70]
        high_prec = max(high_prec_cands, key=lambda x: x["precision"]) if high_prec_cands else conf_sweep[-1]

        return {
            "BALANCED_OPERATING_POINT": balanced,
            "HIGH_RECALL_OPERATING_POINT": high_recall,
            "HIGH_PRECISION_OPERATING_POINT": high_prec,
        }

    def generate_calibration_reports(
        self,
        output_json: Path = Path("reports/model_optimization/threshold_calibration.json"),
        output_md: Path = Path("reports/model_optimization/threshold_calibration.md"),
    ) -> Dict[str, Any]:
        """Runs sweeps, identifies operating points, and authors calibration reports."""
        output_json = Path(output_json)
        output_md = Path(output_md)
        output_json.parent.mkdir(parents=True, exist_ok=True)

        conf_sweep = self.run_confidence_sweep()
        nms_sweep = self.run_nms_sweep()
        operating_points = self.identify_operating_points(conf_sweep)

        report_data = {
            "model_path": str(self.model_path),
            "data_yaml": str(self.data_yaml),
            "operating_points": operating_points,
            "confidence_sweep": conf_sweep,
            "nms_iou_sweep": nms_sweep,
        }

        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

        with open(output_md, "w", encoding="utf-8") as f:
            f.write("# MarineDebris-Sonar-AI — Confidence & NMS Threshold Calibration Report\n\n")
            f.write(f"**Model:** `{self.model_path.name}`  \n")
            f.write(f"**Validation Dataset:** `{self.data_yaml.name}`\n\n")
            f.write("## 1. Calibrated Operating Points\n\n")
            f.write("| Mode | Conf Threshold | Precision | Recall | F1 Score | mAP50 | Use Case |\n")
            f.write("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |\n")
            b = operating_points["BALANCED_OPERATING_POINT"]
            hr = operating_points["HIGH_RECALL_OPERATING_POINT"]
            hp = operating_points["HIGH_PRECISION_OPERATING_POINT"]
            f.write(f"| **Balanced** | **{b['confidence_threshold']}** | {b['precision']:.2%} | {b['recall']:.2%} | **{b['f1']:.4f}** | {b['mAP50']:.2%} | General AUV Survey & Mapping |\n")
            f.write(f"| **High Recall** | **{hr['confidence_threshold']}** | {hr['precision']:.2%} | {hr['recall']:.2%} | {hr['f1']:.4f} | {hr['mAP50']:.2%} | Search & Rescue / Hazard Warning |\n")
            f.write(f"| **High Precision** | **{hp['confidence_threshold']}** | {hp['precision']:.2%} | {hp['recall']:.2%} | {hp['f1']:.4f} | {hp['mAP50']:.2%} | Automated Recovery / ROV Grasping |\n\n")
            f.write("## 2. Confidence Sweep (IoU = 0.45)\n\n")
            f.write("| Conf Threshold | Precision | Recall | F1 Score | mAP50 | mAP50-95 |\n")
            f.write("| :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for row in conf_sweep:
                f.write(f"| {row['confidence_threshold']:.2f} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['mAP50']:.4f} | {row['mAP50_95']:.4f} |\n")
            f.write("\n## 3. NMS IoU Sweep (Conf = 0.25)\n\n")
            f.write("| NMS IoU | Precision | Recall | F1 Score | mAP50 | mAP50-95 |\n")
            f.write("| :---: | :---: | :---: | :---: | :---: | :---: |\n")
            for row in nms_sweep:
                f.write(f"| {row['nms_iou_threshold']:.2f} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['mAP50']:.4f} | {row['mAP50_95']:.4f} |\n")

        print(f"[CALIB] Saved calibration reports to {output_json} and {output_md}")
        return report_data
