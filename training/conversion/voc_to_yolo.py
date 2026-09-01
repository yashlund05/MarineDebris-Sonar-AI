"""Pascal VOC XML annotation format to YOLO TXT format converter.

Converts bounding boxes from:
  <bndbox> <xmin>, <ymin>, <xmax>, <ymax> </bndbox> (absolute pixels)
to:
  [class_id, x_center, y_center, width, height] (normalized [0, 1])

Follows canonical 5-class marine debris taxonomy per PRD.md §4.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List, Optional

CANONICAL_CLASSES: list[str] = [
    "derelict_fishing_gear",
    "general_marine_debris",
    "shipwreck",
    "pipe_or_cylinder",
    "other_man_made_target",
]


def convert_voc_xml_to_yolo(
    xml_file_path: str,
    output_dir: str,
    class_mapping: Optional[dict[str, str]] = None,
) -> bool:
    """Convert a single Pascal VOC XML file to YOLO text format.

    Args:
        xml_file_path: Path to .xml file.
        output_dir: Destination directory for .txt file.
        class_mapping: Optional label mapping dict.

    Returns:
        True if successfully converted.
    """
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    size = root.find("size")
    if size is None:
        return False

    width_elem = size.find("width")
    height_elem = size.find("height")
    if width_elem is None or height_elem is None:
        return False

    width = float(width_elem.text or "0")
    height = float(height_elem.text or "0")

    if width <= 0 or height <= 0:
        return False

    stem = Path(xml_file_path).stem
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_txt_file = out_dir / f"{stem}.txt"

    lines: list[str] = []

    for obj in root.findall("object"):
        name_elem = obj.find("name")
        if name_elem is None or not name_elem.text:
            continue

        raw_name = name_elem.text.lower().strip().replace(" ", "_").replace("-", "_")
        if class_mapping and raw_name in class_mapping:
            raw_name = class_mapping[raw_name]

        if raw_name not in CANONICAL_CLASSES:
            continue

        class_id = CANONICAL_CLASSES.index(raw_name)

        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue

        xmin = float(bndbox.findtext("xmin", "0"))
        ymin = float(bndbox.findtext("ymin", "0"))
        xmax = float(bndbox.findtext("xmax", "0"))
        ymax = float(bndbox.findtext("ymax", "0"))

        w = xmax - xmin
        h = ymax - ymin

        if w <= 0 or h <= 0:
            continue

        x_center = (xmin + w / 2.0) / width
        y_center = (ymin + h / 2.0) / height
        norm_w = w / width
        norm_h = h / height

        x_center = max(0.0, min(1.0, x_center))
        y_center = max(0.0, min(1.0, y_center))
        norm_w = max(0.0, min(1.0, norm_w))
        norm_h = max(0.0, min(1.0, norm_h))

        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

    with open(out_txt_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))

    return True
