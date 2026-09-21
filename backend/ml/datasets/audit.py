"""
MarineDebris-Sonar-AI: Comprehensive Dataset and Annotation Auditor
Validates bounding box geometry, label consistency, normalized coordinate bounds,
object scale distribution, cross-split sequence leakage, exact duplicate hashes,
and generates formal audit manifests.
"""

import os
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set, Optional
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
            errors.append(f"Invalid class_id: {cls_id} (allowed: {sorted(list(self.valid_class_ids))})")

        if not (0.0 <= xc <= 1.0):
            errors.append(f"x_center out of bounds: {xc:.4f}")
        if not (0.0 <= yc <= 1.0):
            errors.append(f"y_center out of bounds: {yc:.4f}")

        if w <= 0.0 or h <= 0.0:
            errors.append(f"Zero or negative dimension: w={w:.4f}, h={h:.4f}")
        if w > 1.0 or h > 1.0:
            errors.append(f"Dimension exceeds canvas: w={w:.4f}, h={h:.4f}")

        # Check reconstructed corners
        xmin = xc - w / 2.0
        xmax = xc + w / 2.0
        ymin = yc - h / 2.0
        ymax = yc + h / 2.0

        if xmin < -0.05 or ymin < -0.05 or xmax > 1.05 or ymax > 1.05:
            errors.append(f"Box significantly extends beyond canvas: [{xmin:.3f}, {ymin:.3f}, {xmax:.3f}, {ymax:.3f}]")

        # Aspect ratio and degenerate box check
        if w > 0 and h > 0:
            aspect = max(w / h, h / w)
            if aspect > 50.0:
                errors.append(f"Extreme aspect ratio anomaly: {aspect:.1f}:1")
            area_px = (w * canvas_size) * (h * canvas_size)
            if area_px < 4.0:
                errors.append(f"Extremely degenerate box area: {area_px:.1f} px^2")

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

    @staticmethod
    def extract_sequence_id(filename: str) -> str:
        """Extracts continuous acoustic ping acquisition sequence identifier."""
        stem = Path(filename).stem
        # e.g., 2016-06-22_113541-frame00010 -> 2016-06-22_113541
        if "-frame" in stem:
            return stem.split("-frame")[0]
        if "_frame" in stem:
            return stem.split("_frame")[0]
        parts = stem.split("_")
        if len(parts) >= 2:
            return "_".join(parts[:2])
        return stem

    def audit_leakage(
        self,
        dataset_root: Path,
        split_names: List[str] = ["train", "val", "test"],
    ) -> Dict[str, Any]:
        """
        Audits sequence-level and byte-level duplicates across dataset splits
        to ensure zero data leakage.
        """
        dataset_root = Path(dataset_root)
        split_hashes: Dict[str, Dict[str, str]] = {}  # split -> {hash: filename}
        split_sequences: Dict[str, Set[str]] = {}     # split -> set of seq_ids

        for split in split_names:
            img_dir = dataset_root / "images" / split
            split_hashes[split] = {}
            split_sequences[split] = set()

            if not img_dir.exists():
                continue

            for p in sorted(list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg"))):
                with open(p, "rb") as f:
                    file_hash = hashlib.sha256(f.read()).hexdigest()
                split_hashes[split][file_hash] = p.name
                seq_id = self.extract_sequence_id(p.name)
                split_sequences[split].add(seq_id)

        # 1. Exact duplicate hash check
        exact_leakage = []
        for i, s1 in enumerate(split_names):
            for s2 in split_names[i+1:]:
                overlap_hashes = set(split_hashes[s1].keys()) & set(split_hashes[s2].keys())
                for h in overlap_hashes:
                    exact_leakage.append({
                        "hash": h,
                        "split_1": s1,
                        "file_1": split_hashes[s1][h],
                        "split_2": s2,
                        "file_2": split_hashes[s2][h],
                    })

        # 2. Sequence-level cross-split leakage check
        sequence_leakage = []
        for i, s1 in enumerate(split_names):
            for s2 in split_names[i+1:]:
                overlap_seqs = split_sequences[s1] & split_sequences[s2]
                for seq in overlap_seqs:
                    sequence_leakage.append({
                        "sequence_id": seq,
                        "split_1": s1,
                        "split_2": s2,
                    })

        return {
            "exact_duplicate_count": len(exact_leakage),
            "exact_leakage_cases": exact_leakage,
            "sequence_leakage_count": len(sequence_leakage),
            "sequence_leakage_cases": sequence_leakage,
            "sequence_counts_per_split": {s: len(split_sequences[s]) for s in split_names},
            "leakage_status": "PASS" if (len(exact_leakage) == 0 and len(sequence_leakage) == 0) else "FAIL",
        }

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
        warnings = []
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

        leakage_results = self.audit_leakage(dataset_root, split_names)

        return {
            "dataset_root": str(dataset_root),
            "total_images": total_images,
            "total_annotations": total_annotations,
            "total_negatives": total_negatives,
            "splits": split_stats,
            "class_distribution": class_dist,
            "scale_distribution": scale_dist,
            "error_count": len(errors),
            "errors": errors[:50],
            "leakage": leakage_results,
            "status": "PASS" if len(errors) == 0 and leakage_results["leakage_status"] == "PASS" else "FAIL",
        }
