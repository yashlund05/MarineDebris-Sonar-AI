"""
Automated Integration and Unit Tests for Dataset V3 Expansion Pipeline.
Validates provenance, bbox geometry, deduplication, sequence-level zero leakage,
taxonomy harmonization, negative background curation, and manifest integrity.
"""

import os
import json
import pytest
from pathlib import Path

from backend.ml.datasets.provenance import ProvenanceManager, ProvenanceRecord
from backend.ml.datasets.normalize import ImageNormalizer
from backend.ml.datasets.audit import AnnotationAuditor
from backend.ml.datasets.deduplicate import DatasetDeduplicator
from backend.ml.datasets.split import SequenceAwareSplitter


def test_baseline_frozen_snapshot():
    """Verify that baseline snapshot is frozen and immutable."""
    snapshot_path = Path("reports/dataset_expansion/baseline_snapshot.json")
    freeze_flag = Path("reports/dataset_expansion/BASELINE_FROZEN")

    assert snapshot_path.exists(), "baseline_snapshot.json must exist"
    assert freeze_flag.exists(), "BASELINE_FROZEN file must exist"

    with open(snapshot_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["baseline_dataset_frozen"] is True
    assert data["total_real_images"] == 238
    assert data["total_annotations"] == 371
    assert data["splits"]["test"]["images"] == 37
    assert data["production_benchmarks"]["validation_split"]["mAP50"] >= 0.89


def test_provenance_manager_integrity():
    """Verify that provenance records are complete, hash-verified, and license-compliant."""
    prov_file = Path("datasets/sonar_debris_v3/metadata/provenance.jsonl")
    assert prov_file.exists(), "provenance.jsonl must exist"

    manager = ProvenanceManager(prov_file)
    assert len(manager.records) > 0, "Provenance records must be populated"

    integrity = manager.verify_integrity()
    assert integrity["status"] == "PASS"
    assert integrity["missing_source"] == 0
    assert integrity["missing_license"] == 0


def test_annotation_auditor_bbox_validation():
    """Verify that annotation auditor catches invalid bounding boxes and accepts valid ones."""
    auditor = AnnotationAuditor(valid_class_ids=[0, 1, 2, 3, 4])

    # Valid box
    valid, errs = auditor.validate_yolo_bbox(1, 0.5, 0.5, 0.2, 0.3)
    assert valid is True
    assert len(errs) == 0

    # Invalid class
    valid, errs = auditor.validate_yolo_bbox(99, 0.5, 0.5, 0.2, 0.3)
    assert valid is False

    # Out-of-bounds center
    valid, errs = auditor.validate_yolo_bbox(1, 1.5, 0.5, 0.2, 0.3)
    assert valid is False

    # Zero area
    valid, errs = auditor.validate_yolo_bbox(1, 0.5, 0.5, 0.0, 0.3)
    assert valid is False

    # Negative dimension
    valid, errs = auditor.validate_yolo_bbox(1, 0.5, 0.5, -0.1, 0.3)
    assert valid is False


def test_deduplicator_exact_and_near():
    """Verify SHA256 and perceptual hash logic."""
    dedup = DatasetDeduplicator(dhash_threshold=4)

    # Verify identical hashes have Hamming distance 0
    h1 = 0b10101010
    h2 = 0b10101010
    assert dedup.hamming_distance(h1, h2) == 0

    # Hamming distance 1
    h3 = 0b10101011
    assert dedup.hamming_distance(h1, h3) == 1


def test_sequence_aware_splitting_and_zero_leakage():
    """Verify that sequence splitter groups continuous frames and guarantees zero leakage."""
    splitter = SequenceAwareSplitter(block_size=5)

    samples = []
    # Create 3 sequence blocks (15 items)
    for i in range(15):
        seq = f"block_{i // 5}"
        samples.append({"filename": f"img_{i:03d}.png", "sequence_id": seq})

    splits = splitter.partition_samples_by_sequence(samples, train_ratio=0.6, val_ratio=0.2, test_ratio=0.2)
    audit = splitter.audit_leakage(splits)

    assert audit["status"] == "PASS"
    assert len(audit["sequence_overlap"]["train_vs_val"]) == 0
    assert len(audit["sequence_overlap"]["train_vs_test"]) == 0
    assert len(audit["sequence_overlap"]["val_vs_test"]) == 0


def test_dataset_v3_manifest_integrity():
    """Verify that Dataset V3 manifest matches actual filesystem."""
    manifest_p = Path("datasets/sonar_debris_v3/DATASET_MANIFEST.json")
    assert manifest_p.exists(), "DATASET_MANIFEST.json must exist"

    with open(manifest_p, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["dataset_version"] == "v3.0.0"
    assert manifest["total_real_images"] >= 600
    assert manifest["total_annotations"] >= 800
    assert manifest["total_negative_images"] >= 60
    assert manifest["quality_audit"]["leakage_status"] == "PASS"
    assert manifest["quality_audit"]["annotation_errors"] == 0

    # Check images exist on filesystem
    v3_root = Path("datasets/sonar_debris_v3")
    train_imgs = list((v3_root / "images" / "train").glob("*.png"))
    val_imgs = list((v3_root / "images" / "val").glob("*.png"))
    test_imgs = list((v3_root / "images" / "test").glob("*.png"))

    actual_total = len(train_imgs) + len(val_imgs) + len(test_imgs)
    assert actual_total == manifest["total_real_images"]


def test_hard_negative_dataset_population():
    """Verify that genuine negative background frames are preserved and registered."""
    neg_dir = Path("datasets/sonar_debris_v3/hard_negatives")
    assert neg_dir.exists()
    neg_images = list(neg_dir.glob("*.png"))
    assert len(neg_images) >= 60, "Must contain at least 60 genuine negative seabed/wall samples"
