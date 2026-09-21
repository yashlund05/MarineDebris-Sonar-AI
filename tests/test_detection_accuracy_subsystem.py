"""
Tests for Detection Accuracy Subsystem:
Validates dataset audit, quality screening, hard-negative mining,
promotion gate logic, and production checkpoint cryptographic immutability.
"""

import hashlib
from pathlib import Path
import pytest
import numpy as np

from backend.ml.datasets.audit import AnnotationAuditor
from backend.ml.mining.hard_negative_miner import HardNegativeMiner
from backend.ml.synthetic.quality_screener import SyntheticQualityScreener, SyntheticScreeningStatus
from backend.ml.optimization.promotion_gate import PromotionGate, FROZEN_BASELINE

EXPECTED_PRODUCTION_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"


def test_production_model_immutability():
    """CRITICAL SAFEGUARD: Asserts byte-identical hash for production checkpoint."""
    model_path = Path("models/detection/sonar_yolov8_fls_trained.pt")
    assert model_path.exists(), "Production checkpoint missing!"
    current_hash = hashlib.sha256(model_path.read_bytes()).hexdigest()
    assert current_hash == EXPECTED_PRODUCTION_SHA256, (
        f"CRITICAL VIOLATION: Production model checkpoint has been modified!\n"
        f"Expected: {EXPECTED_PRODUCTION_SHA256}\n"
        f"Actual:   {current_hash}"
    )


def test_annotation_auditor_geometry_validation():
    """Validates that auditor catches invalid or out-of-bounds bounding boxes."""
    auditor = AnnotationAuditor(valid_class_ids=[0, 1, 2, 3, 4])

    # Valid box
    is_valid, errors = auditor.validate_yolo_bbox(1, 0.5, 0.5, 0.2, 0.2)
    assert is_valid
    assert len(errors) == 0

    # Negative width
    is_valid, errors = auditor.validate_yolo_bbox(1, 0.5, 0.5, -0.1, 0.2)
    assert not is_valid

    # Center out of bounds
    is_valid, errors = auditor.validate_yolo_bbox(1, 1.2, 0.5, 0.2, 0.2)
    assert not is_valid

    # Invalid class ID
    is_valid, errors = auditor.validate_yolo_bbox(99, 0.5, 0.5, 0.2, 0.2)
    assert not is_valid


def test_synthetic_quality_screener_flat_image():
    """Asserts that flat or low-variance degenerate images are rejected."""
    screener = SyntheticQualityScreener()
    tmp_img = Path("reports/temp_flat_test.png")
    tmp_img.parent.mkdir(parents=True, exist_ok=True)
    import cv2
    cv2.imwrite(str(tmp_img), np.full((640, 640), 128, dtype=np.uint8))

    try:
        res = screener.screen_sample(tmp_img)
        assert res.status == SyntheticScreeningStatus.REJECTED
        assert any("flat" in r.lower() or "missing label" in r.lower() for r in res.rejection_reasons)
    finally:
        if tmp_img.exists():
            tmp_img.unlink()


def test_hard_negative_miner_categorization():
    """Validates spatial and naming categorization of false alarms."""
    miner = HardNegativeMiner()

    cat_wall = miner.categorize_false_positive("tank_wall_sweep_01.png", [0.5, 0.5, 0.2, 0.2], (640, 640))
    assert cat_wall == "ACOUSTIC_WALL"

    cat_border = miner.categorize_false_positive("random_survey.png", [0.01, 0.5, 0.05, 0.2], (640, 640))
    assert cat_border == "IMAGE_BORDER"

    cat_water = miner.categorize_false_positive("random_survey.png", [0.5, 0.08, 0.1, 0.1], (640, 640))
    assert cat_water == "WATER_COLUMN_NOISE"


def test_promotion_gate_decision_logic():
    """Asserts that PromotionGate strictly approves superior candidates and rejects regressed models."""
    gate = PromotionGate()

    # Superior candidate
    bench_a_good = {"mAP50": 0.940, "recall": 0.910}
    bench_b_good = {"mAP50": 0.950}
    bench_c_good = {"negative_image_FAR": 0.100, "total_false_positive_boxes": 8}
    lat_good = {"latency_p95_ms": 50.0, "fps": 20.0}
    res_good = gate.evaluate_candidate(bench_a_good, bench_b_good, bench_c_good, lat_good)
    assert res_good.overall_pass is True
    assert res_good.status == "ELIGIBLE_FOR_PROMOTION"

    # Regressed candidate (V2 Recall drops by 15%)
    bench_a_bad = {"mAP50": 0.890, "recall": 0.750}
    res_bad = gate.evaluate_candidate(bench_a_bad, bench_b_good, bench_c_good, lat_good)
    assert res_bad.overall_pass is False
    assert res_bad.status == "REJECTED"
