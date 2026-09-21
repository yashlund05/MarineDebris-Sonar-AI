"""
MarineDebris-Sonar-AI: Hard-Negative Mining Engine
Identifies, categorizes, and curates acoustic false alarms (quarry sediment,
tank boundary walls, reverberation clutter) for model retraining.
"""

import os
import json
import shutil
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from backend.ml.optimization.utils import ROOT_DIR


@dataclass
class MinedFalsePositive:
    image_path: str
    image_name: str
    category: str
    box_xywh: List[float]
    confidence: float
    predicted_class: int
    predicted_label: str
    crop_saved_path: Optional[str] = None


@dataclass
class HardNegativeMiningReport:
    total_images_scanned: int
    flagged_images_count: int
    total_false_positives: int
    false_alarm_rate: float
    category_counts: Dict[str, int]
    mined_samples: List[Dict[str, Any]]
    output_dir: str


class HardNegativeMiner:
    """
    Mines false alarms from non-debris sonar surveys and produces curated
    YOLO-compliant background negative training datasets.
    """

    CATEGORIES = [
        "ACOUSTIC_WALL",
        "SEDIMENT_REVERBERATION",
        "WATER_COLUMN_NOISE",
        "IMAGE_BORDER",
        "UNCLASSIFIED_CLUTTER",
    ]

    CLASS_NAMES = {
        0: "derelict_fishing_gear",
        1: "general_marine_debris",
        2: "shipwreck",
        3: "pipe_or_cylinder",
        4: "other_man_made_target",
    }

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        conf_threshold: float = 0.15,
        iou_threshold: float = 0.45,
    ):
        self.output_dir = Path(output_dir or (ROOT_DIR / "reports" / "hard_negative_mining"))
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold

    def categorize_false_positive(self, img_name: str, bbox: List[float], img_shape: Tuple[int, int]) -> str:
        """Categorizes false alarms using acoustic spatial context and source provenance."""
        name_lower = img_name.lower()
        h, w = img_shape[:2]
        xc, yc, bw, bh = bbox

        # Check if source is known tank wall sweep
        if "wall" in name_lower or "tank" in name_lower or "boundary" in name_lower:
            return "ACOUSTIC_WALL"

        # Check image border clipping (near edge)
        if xc - bw / 2.0 < 0.03 or xc + bw / 2.0 > 0.97 or yc - bh / 2.0 < 0.03 or yc + bh / 2.0 > 0.97:
            return "IMAGE_BORDER"

        # Check near-range water column (top 15% of frame in FLS)
        if yc < 0.15:
            return "WATER_COLUMN_NOISE"

        # Default quarry / sediment acoustic clutter
        if "2016-06-22" in name_lower or "quarry" in name_lower or "sediment" in name_lower:
            return "SEDIMENT_REVERBERATION"

        return "UNCLASSIFIED_CLUTTER"

    def mine_negatives(
        self,
        model_path: Path,
        negative_images_dir: Path,
        save_crops: bool = True,
    ) -> HardNegativeMiningReport:
        """
        Executes mining on negative directory, returning structured report.
        """
        model_path = Path(model_path)
        negative_images_dir = Path(negative_images_dir)
        crops_dir = self.output_dir / "mined_fp_crops"
        if save_crops:
            crops_dir.mkdir(parents=True, exist_ok=True)

        model = YOLO(str(model_path))

        image_files = sorted(
            list(negative_images_dir.glob("*.png")) + list(negative_images_dir.glob("*.jpg"))
        )
        total_scanned = len(image_files)
        flagged_count = 0
        mined_items: List[MinedFalsePositive] = []
        cat_counts = {cat: 0 for cat in self.CATEGORIES}

        for p in image_files:
            img = cv2.imread(str(p))
            if img is None:
                continue

            results = model.predict(
                str(p),
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                verbose=False,
            )[0]

            boxes = results.boxes
            n_boxes = len(boxes) if boxes is not None else 0

            if n_boxes > 0:
                flagged_count += 1
                for i in range(n_boxes):
                    b = boxes[i]
                    cls_id = int(b.cls.item())
                    conf_val = float(b.conf.item())
                    # Normalized xywh
                    xywh = b.xywhn[0].cpu().numpy().tolist()
                    xyxy_px = b.xyxy[0].cpu().numpy().astype(int)

                    category = self.categorize_false_positive(p.name, xywh, img.shape)
                    cat_counts[category] = cat_counts.get(category, 0) + 1

                    crop_path = None
                    if save_crops:
                        x1, y1, x2, y2 = np.clip(xyxy_px[0], 0, img.shape[1]), np.clip(xyxy_px[1], 0, img.shape[0]), np.clip(xyxy_px[2], 0, img.shape[1]), np.clip(xyxy_px[3], 0, img.shape[0])
                        if x2 > x1 and y2 > y1:
                            crop = img[y1:y2, x1:x2]
                            crop_fname = f"fp_{p.stem}_box{i}_{category}.png"
                            crop_path = str(crops_dir / crop_fname)
                            cv2.imwrite(crop_path, crop)

                    mined_items.append(
                        MinedFalsePositive(
                            image_path=str(p),
                            image_name=p.name,
                            category=category,
                            box_xywh=xywh,
                            confidence=round(conf_val, 4),
                            predicted_class=cls_id,
                            predicted_label=self.CLASS_NAMES.get(cls_id, f"class_{cls_id}"),
                            crop_saved_path=crop_path,
                        )
                    )

        far = flagged_count / total_scanned if total_scanned > 0 else 0.0

        report = HardNegativeMiningReport(
            total_images_scanned=total_scanned,
            flagged_images_count=flagged_count,
            total_false_positives=len(mined_items),
            false_alarm_rate=round(far, 4),
            category_counts=cat_counts,
            mined_samples=[asdict(m) for m in mined_items],
            output_dir=str(self.output_dir),
        )

        # Save report JSON
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(self.output_dir / "hard_negative_mining_report.json", "w", encoding="utf-8") as f:
            json.dump(asdict(report), f, indent=2)

        return report
