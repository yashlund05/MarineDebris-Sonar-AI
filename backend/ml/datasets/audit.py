"""
MarineDebris-Sonar-AI: Comprehensive Annotation Auditor
Validates bounding box geometry, label consistency, normalized coordinate bounds,
object scale distribution, and flags labeling anomalies.
"""

from pathlib import Path
from typing import Dict, List, Any, Tuple
import json


class AnnotationAuditor:
    def __init__(self, valid_class_ids: List[int]):
        self.valid_class_ids = set(valid_class_ids)

    def validate_yolo_bbox(
        self,
        cls_id: int,
        xc: float,
        yc: float,
        w: float,
        h: float,
        canvas_size: int = 640,
    ) -> Tuple[bool, List[str]]:
        """Validates a single YOLO bounding box."""
        errors = []

        if cls_id not in self.valid_class_ids:
            errors.append(f"Invalid class_id: {cls_id} (allowed: {self.valid_class_ids})")

        if not (0.0 <= xc <= 1.0):
            errors.append(f"x_center out of bounds: {xc}")
        if not (0.0 <= yc <= 1.0):
            errors.append(f"y_center out of bounds: {yc}")

        if w <= 0.0 or h <= 0.0:
            errors.append(f"Zero or negative dimension: w={w}, h={h}")
        if w > 1.0 or h > 1.0:
            errors.append(f"Dimension exceeds canvas: w={w}, h={h}")

        # Check reconstructed corners
        xmin = xc - w / 2.0
        xmax = xc + w / 2.0
        ymin = yc - h / 2.0
        ymax = yc + h / 2.0

        if xmin < -0.05 or ymin < -0.05 or xmax > 1.05 or ymax > 1.05:
            errors.append(f"Box significantly extends beyond canvas: [{xmin:.3f}, {ymin:.3f}, {xmax:.3f}, {ymax:.3f}]")

        return len(errors) == 0, errors

    @staticmethod
    def categorize_scale(w: float, h: float, canvas_size: int = 640) -> str:
        max_side_px = max(w, h) * canvas_size
        if max_side_px < 32:
            return "tiny"
        elif max_side_px < 64:
            return "small"
        elif max_side_px < 128:
            return "medium"
        else:
            return "large"

    def audit_dataset_directory(
        self,
        dataset_root: Path,
        split_names: List[str] = ["train", "val", "test"],
    ) -> Dict[str, Any]:
        """Audits an entire YOLO dataset directory."""
        dataset_root = Path(dataset_root)
        total_images = 0
        total_annotations = 0
        total_negatives = 0
        errors = []
        scale_dist = {"tiny": 0, "small": 0, "medium": 0, "large": 0}
        class_dist: Dict[int, int] = {c: 0 for c in self.valid_class_ids}
        split_stats = {}

        for split in split_names:
            img_dir = dataset_root / "images" / split
            lbl_dir = dataset_root / "labels" / split

            if not img_dir.exists():
                continue

            images = sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg")))
            split_boxes = 0
            split_negs = 0

            for img_p in images:
                total_images += 1
                txt_p = lbl_dir / f"{img_p.stem}.txt"

                if not txt_p.exists() or txt_p.stat().st_size == 0:
                    total_negatives += 1
                    split_negs += 1
                    continue

                with open(txt_p, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, 1):
                        parts = line.strip().split()
                        if not parts:
                            continue
                        if len(parts) != 5:
                            errors.append(f"{txt_p.name}:{line_no}: Malformed line (expected 5 tokens, got {len(parts)})")
                            continue

                        try:
                            cid = int(parts[0])
                            xc, yc, w, h = map(float, parts[1:])
                        except ValueError as e:
                            errors.append(f"{txt_p.name}:{line_no}: Parse error ({e})")
                            continue

                        is_valid, errs = self.validate_yolo_bbox(cid, xc, yc, w, h)
                        if not is_valid:
                            errors.extend([f"{txt_p.name}:{line_no}: {err}" for err in errs])
                        else:
                            total_annotations += 1
                            split_boxes += 1
                            class_dist[cid] = class_dist.get(cid, 0) + 1
                            scale_tag = self.categorize_scale(w, h)
                            scale_dist[scale_tag] += 1

            split_stats[split] = {
                "images": len(images),
                "annotations": split_boxes,
                "negatives": split_negs,
            }

        return {
            "total_images": total_images,
            "total_annotations": total_annotations,
            "total_negatives": total_negatives,
            "splits": split_stats,
            "class_distribution": class_dist,
            "scale_distribution": scale_dist,
            "error_count": len(errors),
            "errors": errors[:50],  # cap display
            "status": "PASS" if len(errors) == 0 else "FAIL",
        }
