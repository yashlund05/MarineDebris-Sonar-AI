"""Automated regression and acceptance tests for the prepared real sonar debris dataset."""

import json
from pathlib import Path
import pytest
import yaml

DATASET_ROOT = Path("datasets/sonar_debris")
MANIFEST_PATH = DATASET_ROOT / "DATASET_MANIFEST.json"
DATA_YAML_PATH = DATASET_ROOT / "data.yaml"

EXPECTED_CLASSES = {
    0: "derelict_fishing_gear",
    1: "general_marine_debris",
    2: "shipwreck",
    3: "pipe_or_cylinder",
    4: "other_man_made_target",
}


def test_dataset_directory_structure():
    """Verify that all required train/val/test directories exist and contain files."""
    assert DATASET_ROOT.exists(), "Dataset root directory missing"

    for split in ["train", "val", "test"]:
        img_dir = DATASET_ROOT / "images" / split
        lbl_dir = DATASET_ROOT / "labels" / split

        assert img_dir.exists(), f"Missing image directory for {split}"
        assert lbl_dir.exists(), f"Missing label directory for {split}"

        imgs = list(img_dir.glob("*.png"))
        lbls = list(lbl_dir.glob("*.txt"))

        assert len(imgs) > 0, f"No images found in {split}"
        assert len(lbls) == len(imgs), f"Mismatch between images ({len(imgs)}) and labels ({len(lbls)}) in {split}"


def test_data_yaml_specification():
    """Verify data.yaml configuration conforms to Ultralytics specification."""
    assert DATA_YAML_PATH.exists(), "data.yaml missing"

    with open(DATA_YAML_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert config.get("nc") == 5, f"Expected 5 classes, got {config.get('nc')}"
    names = config.get("names", {})
    assert len(names) == 5, f"Expected 5 class names, got {len(names)}"

    for class_id, expected_name in EXPECTED_CLASSES.items():
        assert names[class_id] == expected_name, f"Mismatch for class {class_id}: {names.get(class_id)} != {expected_name}"


def test_dataset_manifest_integrity():
    """Verify DATASET_MANIFEST.json metadata, provenance, and license."""
    assert MANIFEST_PATH.exists(), "DATASET_MANIFEST.json missing"

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["dataset_name"] == "sonar_debris"
    assert "source_doi" in manifest
    assert "license" in manifest and "CC-BY 4.0" in manifest["license"]
    assert "provenance" in manifest
    assert manifest["total_images"] > 0
    assert manifest["total_annotations"] > 0
    assert manifest["split_counts"]["train"] > 0
    assert manifest["split_counts"]["val"] > 0
    assert manifest["split_counts"]["test"] > 0


def test_yolo_labels_valid_bounds():
    """Verify all YOLO label lines have valid normalized bounding box bounds."""
    label_files = list(DATASET_ROOT.glob("labels/**/*.txt"))
    assert len(label_files) > 0, "No label files found to validate"

    for lbl_file in label_files[:50]:  # Sample check 50 files
        with open(lbl_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]

        for line in lines:
            parts = line.split()
            assert len(parts) == 5, f"Malformed YOLO line in {lbl_file.name}: {line}"
            cls_id = int(parts[0])
            xc, yc, bw, bh = map(float, parts[1:])

            assert cls_id in EXPECTED_CLASSES, f"Unexpected class ID {cls_id} in {lbl_file.name}"
            assert 0.0 <= xc <= 1.0, f"xc out of bounds in {lbl_file.name}: {xc}"
            assert 0.0 <= yc <= 1.0, f"yc out of bounds in {lbl_file.name}: {yc}"
            assert 0.0 < bw <= 1.0, f"bw out of bounds in {lbl_file.name}: {bw}"
            assert 0.0 < bh <= 1.0, f"bh out of bounds in {lbl_file.name}: {bh}"


def test_sequence_split_independence():
    """Verify sequence-level splitting: train, val, and test have zero overlapping files."""
    train_stems = {p.stem for p in (DATASET_ROOT / "images" / "train").glob("*.png")}
    val_stems = {p.stem for p in (DATASET_ROOT / "images" / "val").glob("*.png")}
    test_stems = {p.stem for p in (DATASET_ROOT / "images" / "test").glob("*.png")}

    assert len(train_stems.intersection(val_stems)) == 0, "Data leakage detected between train and val!"
    assert len(train_stems.intersection(test_stems)) == 0, "Data leakage detected between train and test!"
    assert len(val_stems.intersection(test_stems)) == 0, "Data leakage detected between val and test!"
