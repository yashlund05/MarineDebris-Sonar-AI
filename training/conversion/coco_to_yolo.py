"""COCO JSON annotation format to YOLO TXT format converter.

Converts bounding boxes from:
  [x_min, y_min, width, height] (absolute pixels)
to:
  [class_id, x_center, y_center, width, height] (normalized [0, 1])

Follows canonical 5-class marine debris taxonomy per PRD.md §4.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


CANONICAL_CLASSES: list[str] = [
    "derelict_fishing_gear",
    "general_marine_debris",
    "shipwreck",
    "pipe_or_cylinder",
    "other_man_made_target",
]


def convert_coco_to_yolo(
    coco_json_path: str,
    output_dir: str,
    class_mapping: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """Convert COCO annotations to YOLO format text files.

    Args:
        coco_json_path: Path to COCO JSON annotation file.
        output_dir: Directory where YOLO format .txt label files will be saved.
        class_mapping: Optional mapping from source dataset category names to canonical taxonomy.

    Returns:
        Summary statistics dict of converted images and annotations.
    """
    with open(coco_json_path, "r", encoding="utf-8") as f:
        coco_data = json.load(f)

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Build image index: id -> {file_name, width, height}
    images_by_id: dict[int, dict[str, Any]] = {
        img["id"]: img for img in coco_data.get("images", [])
    }

    # Build category index: id -> canonical_class_id (0-4)
    cat_to_class_id: dict[int, int] = {}
    for cat in coco_data.get("categories", []):
        cat_name = cat["name"].lower().replace(" ", "_").replace("-", "_")
        if class_mapping and cat_name in class_mapping:
            cat_name = class_mapping[cat_name]

        if cat_name in CANONICAL_CLASSES:
            cat_to_class_id[cat["id"]] = CANONICAL_CLASSES.index(cat_name)

    # Group annotations by image
    annotations_by_image: dict[int, list[dict[str, Any]]] = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann["image_id"]
        annotations_by_image.setdefault(img_id, []).append(ann)

    converted_count = 0
    skipped_count = 0

    for img_id, img_info in images_by_id.items():
        img_width = img_info.get("width")
        img_height = img_info.get("height")
        file_name = img_info.get("file_name", f"{img_id}.png")
        stem = Path(file_name).stem

        if not img_width or not img_height:
            skipped_count += 1
            continue

        anns = annotations_by_image.get(img_id, [])
        label_lines: list[str] = []

        for ann in anns:
            cat_id = ann.get("category_id")
            if cat_id not in cat_to_class_id:
                continue

            target_class_id = cat_to_class_id[cat_id]
            bbox = ann.get("bbox", [])
            if len(bbox) != 4:
                continue

            x_min, y_min, w, h = bbox
            if w <= 0 or h <= 0:
                continue

            # Normalize to center coordinates [0, 1]
            x_center = (x_min + w / 2.0) / img_width
            y_center = (y_min + h / 2.0) / img_height
            norm_w = w / img_width
            norm_h = h / img_height

            # Clamp coordinates to [0, 1]
            x_center = max(0.0, min(1.0, x_center))
            y_center = max(0.0, min(1.0, y_center))
            norm_w = max(0.0, min(1.0, norm_w))
            norm_h = max(0.0, min(1.0, norm_h))

            label_lines.append(
                f"{target_class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}"
            )

        # Write YOLO label file
        label_file = out_path / f"{stem}.txt"
        with open(label_file, "w", encoding="utf-8") as f:
            f.write("\n".join(label_lines) + ("\n" if label_lines else ""))

        converted_count += 1

    return {
        "total_images": len(images_by_id),
        "converted_labels": converted_count,
        "skipped_images": skipped_count,
        "canonical_classes": CANONICAL_CLASSES,
        "output_directory": str(out_path),
    }
