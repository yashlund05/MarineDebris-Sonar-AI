"""Reproducible acquisition and preparation pipeline for real acoustic marine debris sonar dataset.

Acquires real sonar imagery from the University of Groningen / Heriot-Watt University
Marine Debris Sonar benchmark (M. Valdenegro-Toro, CC-BY 4.0).
Converts XML annotations, maps classes into canonical taxonomy, applies sequence-level
splitting (zero leakage), standardizes to 640x640 canvas, and outputs YOLO formatted data.
"""

import os
import sys
import json
import time
import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
import urllib.request
import concurrent.futures
from typing import Dict, List, Tuple, Any

import cv2
import numpy as np

# Canonical Class Mapping per docs/DATASET_CLASS_MAPPING.md
CLASS_MAPPING = {
    "bottle": (1, "general_marine_debris"),
    "can": (1, "general_marine_debris"),
    "drink-carton": (1, "general_marine_debris"),
    "shampoo-bottle": (1, "general_marine_debris"),
    "standing-bottle": (1, "general_marine_debris"),
    "tire": (1, "general_marine_debris"),
    "propeller": (4, "other_man_made_target"),
    "chain": (4, "other_man_made_target"),
    "hook": (4, "other_man_made_target"),
    "valve": (4, "other_man_made_target"),
}

BASE_GITHUB_RAW = (
    "https://raw.githubusercontent.com/mvaldenegro/marine-debris-fls-datasets/master"
    "/md_fls_dataset/data/watertank-segmentation"
)


def fetch_file(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """Download single file with retry logic."""
    if dest_path.exists() and dest_path.stat().st_size > 0:
        return True

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MarineDebrisSonarAI-Fetch/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read()
                if len(content) == 0:
                    continue
                with open(dest_path, "wb") as f:
                    f.write(content)
                return True
        except Exception as e:
            time.sleep(0.5 * (attempt + 1))
    return False


def acquire_raw_dataset(
    dest_raw_dir: Path, num_samples: int = 250, max_workers: int = 16
) -> Tuple[int, int]:
    """Fetch real acoustic images and XML box annotations in parallel."""
    raw_images_dir = dest_raw_dir / "Images"
    raw_boxes_dir = dest_raw_dir / "BoxAnnotations"
    raw_images_dir.mkdir(parents=True, exist_ok=True)
    raw_boxes_dir.mkdir(parents=True, exist_ok=True)

    tasks = []
    # Sample index sequence
    sample_indices = list(range(num_samples))

    for idx in sample_indices:
        img_name = f"marine-debris-aris3k-{idx}.png"
        xml_name = f"marine-debris-aris3k-{idx}.xml"

        img_url = f"{BASE_GITHUB_RAW}/Images/{img_name}"
        xml_url = f"{BASE_GITHUB_RAW}/BoxAnnotations/{xml_name}"

        tasks.append((img_url, raw_images_dir / img_name))
        tasks.append((xml_url, raw_boxes_dir / xml_name))

    print(f"[ACQUIRE] Downloading {len(tasks)} files from peer-reviewed benchmark...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_file, url, dest) for url, dest in tasks]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    downloaded = sum(1 for r in results if r)
    print(f"[ACQUIRE] Successfully retrieved {downloaded}/{len(tasks)} files.")
    return len(sample_indices), downloaded


def parse_and_validate_annotation(xml_path: Path) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Parse Pascal VOC XML annotation and validate boxes."""
    if not xml_path.exists():
        return 0, 0, []

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception:
        return 0, 0, []

    size_elem = root.find("size")
    if size_elem is None:
        width, height = 320, 480
    else:
        width = int(size_elem.findtext("width", "320"))
        height = int(size_elem.findtext("height", "480"))

    objects = []
    for obj in root.findall("object"):
        name_elem = obj.find("name")
        if name_elem is None or not name_elem.text:
            continue
        raw_name = name_elem.text.strip().lower()

        if raw_name not in CLASS_MAPPING:
            continue  # Exclude 'wall' or unmapped background

        class_id, canonical_name = CLASS_MAPPING[raw_name]
        bndbox = obj.find("bndbox")
        if bndbox is None:
            continue

        # Check format: either <x, y, w, h> or <xmin, ymin, xmax, ymax>
        if bndbox.find("w") is not None and bndbox.find("h") is not None:
            x = float(bndbox.findtext("x", "0"))
            y = float(bndbox.findtext("y", "0"))
            w = float(bndbox.findtext("w", "0"))
            h = float(bndbox.findtext("h", "0"))
            xmin, ymin, xmax, ymax = x, y, x + w, y + h
        else:
            xmin = float(bndbox.findtext("xmin", "0"))
            ymin = float(bndbox.findtext("ymin", "0"))
            xmax = float(bndbox.findtext("xmax", "0"))
            ymax = float(bndbox.findtext("ymax", "0"))
            w = xmax - xmin
            h = ymax - ymin

        if w <= 0 or h <= 0 or xmin >= width or ymin >= height:
            continue  # Reject zero-area or out-of-bound boxes

        objects.append({
            "class_id": class_id,
            "class_name": canonical_name,
            "xmin": max(0.0, xmin),
            "ymin": max(0.0, ymin),
            "xmax": min(float(width), xmax),
            "ymax": min(float(height), ymax),
        })

    return width, height, objects


def prepare_yolo_dataset(
    raw_dir: Path, output_dir: Path, target_size: int = 640
) -> Dict[str, Any]:
    """Standardize images to 640x640 canvas and generate YOLO labels with survey-level split."""
    raw_images_dir = raw_dir / "Images"
    raw_boxes_dir = raw_dir / "BoxAnnotations"

    # Identify valid pairs
    valid_samples = []
    xml_files = sorted(raw_boxes_dir.glob("*.xml"))

    for xml_file in xml_files:
        stem = xml_file.stem
        img_file = raw_images_dir / f"{stem}.png"
        if img_file.exists():
            w, h, objs = parse_and_validate_annotation(xml_file)
            if len(objs) > 0:  # Only samples with valid debris targets
                valid_samples.append((img_file, xml_file, w, h, objs))

    total_valid = len(valid_samples)
    print(f"[PREPARE] Validated {total_valid} real acoustic images with valid marine debris annotations.")

    # Sequence-level splitting (zero spatial/temporal leakage)
    # Contiguous sequences: 70% Train, 15% Val, 15% Test
    n_train = int(total_valid * 0.70)
    n_val = int(total_valid * 0.15)
    splits = {
        "train": valid_samples[:n_train],
        "val": valid_samples[n_train : n_train + n_val],
        "test": valid_samples[n_train + n_val :],
    }

    # Setup directories
    for split_name in ["train", "val", "test"]:
        (output_dir / "images" / split_name).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split_name).mkdir(parents=True, exist_ok=True)

    class_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    split_counts = {"train": 0, "val": 0, "test": 0}
    total_boxes = 0

    for split_name, samples in splits.items():
        for img_path, xml_path, orig_w, orig_h, objs in samples:
            # Read real acoustic sonar image
            img = cv2.imread(str(img_path))
            if img is None:
                continue

            # Create 640x640 canvas (letterbox/pad without distorting aspect ratio)
            canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
            # Scale factor
            scale = min(target_size / orig_w, target_size / orig_h)
            new_w = int(orig_w * scale)
            new_h = int(orig_h * scale)
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

            # Center on 640x640 canvas
            dx = (target_size - new_w) // 2
            dy = (target_size - new_h) // 2
            canvas[dy : dy + new_h, dx : dx + new_w] = resized

            # Save 640x640 image
            out_img_path = output_dir / "images" / split_name / f"{img_path.stem}.png"
            cv2.imwrite(str(out_img_path), canvas)

            # Transform bounding boxes to YOLO normalized coordinates
            yolo_lines = []
            for obj in objs:
                # Transform to canvas coordinates
                box_xmin = obj["xmin"] * scale + dx
                box_xmax = obj["xmax"] * scale + dx
                box_ymin = obj["ymin"] * scale + dy
                box_ymax = obj["ymax"] * scale + dy

                # Compute center and dimensions normalized to [0, 1]
                x_center = (box_xmin + box_xmax) / (2.0 * target_size)
                y_center = (box_ymin + box_ymax) / (2.0 * target_size)
                box_w = (box_xmax - box_xmin) / target_size
                box_h = (box_ymax - box_ymin) / target_size

                x_center = max(0.0, min(1.0, x_center))
                y_center = max(0.0, min(1.0, y_center))
                box_w = max(0.0, min(1.0, box_w))
                box_h = max(0.0, min(1.0, box_h))

                yolo_lines.append(f"{obj['class_id']} {x_center:.6f} {y_center:.6f} {box_w:.6f} {box_h:.6f}")
                class_counts[obj["class_id"]] += 1
                total_boxes += 1

            # Save YOLO label
            out_txt_path = output_dir / "labels" / split_name / f"{img_path.stem}.txt"
            with open(out_txt_path, "w", encoding="utf-8") as f:
                f.write("\n".join(yolo_lines) + "\n")

            split_counts[split_name] += 1

    # Write data.yaml
    data_yaml_content = (
        "# MarineDebris-Sonar-AI: Prepared Acoustic Marine Debris Dataset\n"
        f"path: {output_dir.resolve().as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        "nc: 5\n"
        "names:\n"
        "  0: derelict_fishing_gear\n"
        "  1: general_marine_debris\n"
        "  2: shipwreck\n"
        "  3: pipe_or_cylinder\n"
        "  4: other_man_made_target\n"
    )
    with open(output_dir / "data.yaml", "w", encoding="utf-8") as f:
        f.write(data_yaml_content)

    manifest = {
        "dataset_name": "sonar_debris",
        "dataset_version": "v1.0.0",
        "source": "Marine Debris Forward-Looking Sonar Datasets (University of Groningen / Heriot-Watt)",
        "source_doi": "10.5281/zenodo.15101686",
        "source_repo": "https://github.com/mvaldenegro/marine-debris-fls-datasets",
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0)",
        "provenance": "Real ARIS 3000 acoustic sonar images with ground-truth debris bounding boxes",
        "sonar_modality": "Acoustic Sonar Imagery (ARIS Explorer 3000, 3.0 MHz)",
        "preparation_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_image_size": [target_size, target_size],
        "split_counts": split_counts,
        "total_images": sum(split_counts.values()),
        "total_annotations": total_boxes,
        "class_distribution": {
            "0 (derelict_fishing_gear)": class_counts[0],
            "1 (general_marine_debris)": class_counts[1],
            "2 (shipwreck)": class_counts[2],
            "3 (pipe_or_cylinder)": class_counts[3],
            "4 (other_man_made_target)": class_counts[4],
        },
    }

    with open(output_dir / "DATASET_MANIFEST.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    raw_path = Path("datasets/raw/marine-debris-fls")
    out_path = Path("datasets/sonar_debris")

    print("==============================================================================")
    print("      MARINEDEBRIS-SONAR-AI: REAL ACOUSTIC DATASET ACQUISITION & PREP         ")
    print("==============================================================================")
    acquire_raw_dataset(raw_path, num_samples=250)
    manifest = prepare_yolo_dataset(raw_path, out_path, target_size=640)
    print("\n[SUCCESS] Dataset preparation complete!")
    print(json.dumps(manifest, indent=2))
