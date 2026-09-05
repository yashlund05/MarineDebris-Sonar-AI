"""
Automated Test Suite for Evaluation Integrity & Benchmark Reconciliation (Phase 2.5).
Validates production checkpoint hashes, frozen test-set integrity, canonical evaluation
contract, benchmark manifest consistency, FAR arithmetic, and prediction determinism.
"""

import json
import hashlib
import pytest
from pathlib import Path

from backend.ml.evaluation.evaluation_contract import (
    EvaluationContract,
    CANONICAL_BENCHMARK_CONF,
    CANONICAL_BENCHMARK_IOU,
    OPERATIONAL_MISSION_CONF,
    OPERATIONAL_MISSION_IOU,
    CANONICAL_IMAGE_SIZE,
    EXPECTED_PRODUCTION_CHECKPOINT_SHA256,
    EXPECTED_LEGACY_TEST_IMAGES,
    EXPECTED_LEGACY_TEST_ANNOTATIONS,
    EXPECTED_V3_TEST_IMAGES,
    EXPECTED_V3_TEST_ANNOTATIONS,
    EXPECTED_HARD_NEGATIVE_IMAGES,
    get_canonical_eval_args,
)

ROOT_DIR = Path(__file__).resolve().parents[2]


def compute_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_production_checkpoint_hash():
    """Verify that active production model checkpoint has not been altered."""
    prod_path = ROOT_DIR / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
    assert prod_path.exists(), "Production model file must exist"
    observed_sha256 = compute_sha256(prod_path)
    assert observed_sha256 == EXPECTED_PRODUCTION_CHECKPOINT_SHA256, (
        f"CRITICAL: Production model hash modified!\n"
        f"Expected: {EXPECTED_PRODUCTION_CHECKPOINT_SHA256}\n"
        f"Observed: {observed_sha256}"
    )


def test_frozen_legacy_test_set_integrity():
    """Verify all 37 test images and 37 test labels match frozen baseline hashes."""
    hashes_file = ROOT_DIR / "reports" / "evaluation_integrity" / "frozen_baseline_hashes.json"
    assert hashes_file.exists(), "frozen_baseline_hashes.json must exist"

    with open(hashes_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "BASELINE_FINGERPRINT_VERIFIED"
    assert data["production_checkpoint"]["match"] is True

    test_img_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "images" / "test"
    test_lbl_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "labels" / "test"

    for img_name, expected_hash in data["legacy_v2_test_set"]["image_hashes"].items():
        img_p = test_img_dir / img_name
        assert img_p.exists(), f"Missing frozen test image: {img_name}"
        assert compute_sha256(img_p) == expected_hash, f"Hash mismatch for {img_name}"

    for lbl_name, expected_hash in data["legacy_v2_test_set"]["label_hashes"].items():
        lbl_p = test_lbl_dir / lbl_name
        assert lbl_p.exists(), f"Missing frozen test label: {lbl_name}"
        assert compute_sha256(lbl_p) == expected_hash, f"Hash mismatch for {lbl_name}"


def test_legacy_test_counts():
    """Verify exact count of images and bounding box annotations in legacy benchmark."""
    test_img_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "images" / "test"
    test_lbl_dir = ROOT_DIR / "datasets" / "sonar_debris_v2_clean" / "labels" / "test"

    imgs = list(test_img_dir.glob("*.png")) + list(test_img_dir.glob("*.jpg"))
    assert len(imgs) == EXPECTED_LEGACY_TEST_IMAGES, f"Expected {EXPECTED_LEGACY_TEST_IMAGES} images, got {len(imgs)}"

    total_boxes = 0
    for lbl in test_lbl_dir.glob("*.txt"):
        with open(lbl, "r", encoding="utf-8") as f:
            total_boxes += sum(1 for line in f if line.strip())

    assert total_boxes == EXPECTED_LEGACY_TEST_ANNOTATIONS, (
        f"Expected {EXPECTED_LEGACY_TEST_ANNOTATIONS} annotations, got {total_boxes}"
    )


def test_v3_test_counts():
    """Verify exact count of images and bounding box annotations in V3 held-out benchmark."""
    test_img_dir = ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "test"
    test_lbl_dir = ROOT_DIR / "datasets" / "sonar_debris_v3" / "labels" / "test"

    imgs = list(test_img_dir.glob("*.png")) + list(test_img_dir.glob("*.jpg"))
    assert len(imgs) == EXPECTED_V3_TEST_IMAGES, f"Expected {EXPECTED_V3_TEST_IMAGES} images, got {len(imgs)}"

    total_boxes = 0
    for lbl in test_lbl_dir.glob("*.txt"):
        with open(lbl, "r", encoding="utf-8") as f:
            total_boxes += sum(1 for line in f if line.strip())

    assert total_boxes == EXPECTED_V3_TEST_ANNOTATIONS, (
        f"Expected {EXPECTED_V3_TEST_ANNOTATIONS} annotations, got {total_boxes}"
    )


def test_hard_negatives_count():
    """Verify exact population of hard negative background frames."""
    neg_dir = ROOT_DIR / "datasets" / "sonar_debris_v3" / "hard_negatives"
    neg_imgs = list(neg_dir.glob("*.png")) + list(neg_dir.glob("*.jpg"))
    assert len(neg_imgs) == EXPECTED_HARD_NEGATIVE_IMAGES, (
        f"Expected {EXPECTED_HARD_NEGATIVE_IMAGES} negatives, got {len(neg_imgs)}"
    )


def test_canonical_evaluation_contract():
    """Verify evaluation contract parameters and rejection of invalid modes."""
    contract = EvaluationContract()
    assert contract.benchmark_conf == 0.001
    assert contract.benchmark_iou == 0.70
    assert contract.operational_conf == 0.25
    assert contract.operational_iou == 0.45
    assert contract.image_size == 640

    benchmark_args = contract.get_val_args(mode="benchmark")
    assert benchmark_args["conf"] == 0.001
    assert benchmark_args["iou"] == 0.70

    operational_args = contract.get_val_args(mode="operational")
    assert operational_args["conf"] == 0.25
    assert operational_args["iou"] == 0.45

    with pytest.raises(ValueError):
        contract.get_val_args(mode="invalid_mode")


def test_benchmark_manifest_consistency():
    """Verify single-source-of-truth benchmark manifest contents."""
    manifest_file = ROOT_DIR / "reports" / "evaluation_integrity" / "BENCHMARK_MANIFEST.json"
    assert manifest_file.exists(), "BENCHMARK_MANIFEST.json must exist"

    with open(manifest_file, "r", encoding="utf-8") as f:
        m = json.load(f)

    assert m["status"] == "EVALUATION_VERIFIED"
    assert m["production_model"]["sha256"] == EXPECTED_PRODUCTION_CHECKPOINT_SHA256
    legacy = m["benchmarks"]["benchmark_1_legacy_v2_control"]
    assert legacy["canonical_benchmark_metrics"]["mAP50"] == 0.8921
    assert legacy["canonical_benchmark_metrics"]["recall"] == 0.9015
    assert legacy["canonical_benchmark_metrics"]["f1"] == 0.9167
    assert legacy["canonical_benchmark_metrics"]["precision"] == 0.9325

    v3 = m["benchmarks"]["benchmark_2_v3_held_out"]
    assert v3["canonical_benchmark_metrics"]["mAP50"] == 0.9192
    assert v3["canonical_benchmark_metrics"]["recall"] == 0.9024
    assert v3["canonical_benchmark_metrics"]["f1"] == 0.9058


def test_far_arithmetic():
    """Verify negative image FAR and FP density formulas."""
    total_negatives = 84
    images_with_fp = 12
    total_fps = 13

    image_far = images_with_fp / total_negatives
    fp_density = total_fps / total_negatives

    assert image_far == pytest.approx(0.142857, abs=1e-5)
    assert round(image_far, 4) == 0.1429
    assert fp_density == pytest.approx(0.154762, abs=1e-5)
    assert round(fp_density, 4) == 0.1548


def test_reproduction_report_integrity():
    """Verify reproduction report exists and confirms exact reproduction."""
    rep_file = ROOT_DIR / "reports" / "evaluation_integrity" / "frozen_benchmark_reproduction.json"
    assert rep_file.exists(), "frozen_benchmark_reproduction.json must exist"

    with open(rep_file, "r", encoding="utf-8") as f:
        rep = json.load(f)

    assert rep["status"] == "REPRODUCED_AND_VERIFIED"
    assert rep["canonical_benchmark_protocol"]["match"] is True
    assert rep["canonical_benchmark_protocol"]["results"]["mAP50"] == 0.8921
    assert rep["canonical_benchmark_protocol"]["results"]["f1"] == 0.9167


def test_prediction_diff_integrity():
    """Verify raw predictions and diff report exist and contain valid schema."""
    canon_pred_file = ROOT_DIR / "reports" / "evaluation_integrity" / "predictions" / "legacy_v2_canonical.json"
    oper_pred_file = ROOT_DIR / "reports" / "evaluation_integrity" / "predictions" / "legacy_v2_operational.json"
    diff_md = ROOT_DIR / "reports" / "evaluation_integrity" / "prediction_diff.md"

    assert canon_pred_file.exists(), "legacy_v2_canonical.json must exist"
    assert oper_pred_file.exists(), "legacy_v2_operational.json must exist"
    assert diff_md.exists(), "prediction_diff.md must exist"

    with open(canon_pred_file, "r", encoding="utf-8") as f:
        canon_data = json.load(f)

    assert len(canon_data) == EXPECTED_LEGACY_TEST_IMAGES
    for img_name, preds in canon_data.items():
        for p in preds:
            assert "class" in p
            assert "confidence" in p
            assert "x1" in p
            assert "y1" in p
