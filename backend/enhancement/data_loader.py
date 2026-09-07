"""
Sequence-Aware Dataset Loader for Sonar Enhancement Development and Benchmarking.

Strict Benchmark Data Policy:
1. Development/Tuning: V2 train+val, V3 train+val ONLY.
2. Held-Out Evaluation: V2 test, V3 test, hard negatives ONLY (locked for promotion gates).
3. The sample image (sample_annotation_viz.png) is strictly a smoke-test/demo asset.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np
import cv2

DATASETS_DIR = Path(__file__).resolve().parent.parent.parent / "datasets"
V2_DIR = DATASETS_DIR / "sonar_debris_v2_clean"
V3_DIR = DATASETS_DIR / "sonar_debris_v3"
SAMPLE_VIZ = DATASETS_DIR / "sonar_debris" / "sample_annotation_viz.png"


class BenchmarkDatasetLoader:
    """Manages access to sequence-isolated acoustic datasets."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or DATASETS_DIR
        self.v2_dir = self.base_dir / "sonar_debris_v2_clean"
        self.v3_dir = self.base_dir / "sonar_debris_v3"

    def get_development_samples(
        self,
        dataset_version: str = "v3",
        split: str = "val",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Loads development samples from authorized train/val splits only.
        
        Raises ValueError if 'test' is requested for development.
        """
        if split not in ["train", "val"]:
            raise ValueError(
                f"Development/method tuning cannot use split '{split}'. "
                "Only 'train' and 'val' splits are permitted for development."
            )

        root = self.v3_dir if dataset_version == "v3" else self.v2_dir
        img_dir = root / "images" / split
        lbl_dir = root / "labels" / split

        if not img_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {img_dir}")

        image_files = sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")))
        if limit:
            image_files = image_files[:limit]

        samples = []
        for img_path in image_files:
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            boxes = self._parse_yolo_labels(lbl_path)
            samples.append({
                "dataset_version": dataset_version,
                "split": split,
                "image_path": str(img_path),
                "image_name": img_path.name,
                "label_path": str(lbl_path) if lbl_path.exists() else None,
                "boxes": boxes,  # list of (class_id, cx, cy, w, h)
                "is_held_out": False
            })

        return samples

    def get_held_out_samples(
        self,
        dataset_version: str = "v3",
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Loads held-out test samples. MUST ONLY be called during frozen final evaluation.
        """
        root = self.v3_dir if dataset_version == "v3" else self.v2_dir
        img_dir = root / "images" / "test"
        lbl_dir = root / "labels" / "test"

        if not img_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {img_dir}")

        image_files = sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")))
        if limit:
            image_files = image_files[:limit]

        samples = []
        for img_path in image_files:
            lbl_path = lbl_dir / f"{img_path.stem}.txt"
            boxes = self._parse_yolo_labels(lbl_path)
            samples.append({
                "dataset_version": dataset_version,
                "split": "test",
                "image_path": str(img_path),
                "image_name": img_path.name,
                "label_path": str(lbl_path) if lbl_path.exists() else None,
                "boxes": boxes,
                "is_held_out": True
            })

        return samples

    def get_smoke_test_sample(self) -> Dict[str, Any]:
        """
        Loads the demonstration/sample visualization asset for smoke testing.
        Explicitly marked as NOT for scientific benchmark.
        """
        if not SAMPLE_VIZ.exists():
            raise FileNotFoundError(f"Sample asset not found: {SAMPLE_VIZ}")

        return {
            "dataset_version": "demo_smoke_test",
            "split": "smoke_test_only",
            "image_path": str(SAMPLE_VIZ),
            "image_name": SAMPLE_VIZ.name,
            "label_path": None,
            "boxes": [],
            "is_held_out": False,
            "is_smoke_test_only": True
        }

    @staticmethod
    def load_image_float32(image_path: str) -> np.ndarray:
        """
        Loads a sonar image from disk, converts to grayscale float32 in [0, 1].
        """
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            raise ValueError(f"Could not decode image at {image_path}")
        if img.ndim == 3 and img.shape[2] == 1:
            img = img.squeeze(axis=2)
        return (img.astype(np.float32) / 255.0).clip(0.0, 1.0)

    @staticmethod
    def _parse_yolo_labels(label_path: Path) -> List[Tuple[int, float, float, float, float]]:
        """Parses YOLO format: <class_id> <cx> <cy> <w> <h>"""
        if not label_path.exists():
            return []
        boxes = []
        with open(label_path, "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        cls_id = int(parts[0])
                        cx, cy, w, h = map(float, parts[1:5])
                        boxes.append((cls_id, cx, cy, w, h))
                    except ValueError:
                        continue
        return boxes
