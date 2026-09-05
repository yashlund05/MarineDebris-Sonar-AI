"""
Automated Test Suite for Model Optimization Framework (Phase 2).
Validates baseline freeze locks, promotion criteria, experiment registry,
threshold calibration logic, error mining, and the formal promotion gate.
"""

import os
import json
import pytest
from pathlib import Path

from backend.ml.experiments.config import (
    ExperimentConfig,
    PromotionCriteria,
    verify_production_lock,
    PRODUCTION_MODEL_PATH,
    PRODUCTION_MODEL_SHA256,
    BASELINE_DATASET_PATH,
    PROTECTION_LOCK_FILE,
)
from backend.ml.experiments.registry import (
    ExperimentRecord,
    ExperimentRegistry,
    get_git_commit,
)
from backend.ml.experiments.calibration import ThresholdCalibrator
from backend.ml.experiments.comparison import ModelComparisonDashboard
from backend.ml.experiments.seeds import MultiSeedEvaluator


def test_production_lock_enforcement():
    """Verify that protection lock file and production model integrity are intact."""
    assert PROTECTION_LOCK_FILE.exists(), "PROTECTION_LOCK file must exist"
    assert PRODUCTION_MODEL_PATH.exists(), "Production model weights must exist"
    assert BASELINE_DATASET_PATH.exists(), "Baseline dataset directory must exist"

    # Verify programmatic lock function passes
    lock_info = verify_production_lock()
    assert lock_info["status"] == "LOCKED_AND_VERIFIED"
    assert lock_info["baseline_dataset_frozen"] is True
    assert lock_info["production_model_frozen"] is True


def test_promotion_criteria_defaults():
    """Verify strict promotion gate thresholds."""
    criteria = PromotionCriteria()
    assert criteria.max_legacy_map50_regression == 0.015  # <= 1.5% regression allowed
    assert criteria.max_legacy_f1_regression == 0.020
    assert criteria.min_v3_map50_gain == 0.005  # >= 0.5% gain required
    assert criteria.max_hard_negative_far == 0.05  # <= 5% false alarm rate
    assert criteria.max_cpu_latency_ms == 125.0


def test_experiment_registry(tmp_path):
    """Verify that experiments can be registered, saved, and retrieved without collision."""
    registry_file = tmp_path / "test_registry.json"
    registry = ExperimentRegistry(registry_file=registry_file)

    rec = ExperimentRecord(
        experiment_id="TEST_EXP_001",
        category="BALANCED_TRAINING",
        description="Unit test run",
        timestamp="2026-09-04T00:00:00Z",
        git_commit=get_git_commit(),
        dataset_manifest_hash="test_manifest_hash",
        dataset_variant="v3_a",
        model_architecture="YOLOv8n",
        pretrained_checkpoint="yolov8n.pt",
        seed=42,
        image_size=640,
        batch_size=8,
        epochs=10,
        optimizer="AdamW",
        learning_rate=0.001,
        scheduler="cosine",
        augmentation_config={"hsv_v": 0.4},
        hardware={"device": "cpu"},
        software_versions={"python": "3.11"},
        training_duration_seconds=120.5,
        validation_metrics={"mAP50": 0.90},
        test_metrics={"mAP50": 0.91},
        checkpoint_hash="testhash123",
        checkpoint_path="test/path.pt",
        status="EXPERIMENTAL",
    )

    registry.register_experiment(rec)
    loaded = registry.get_experiment("TEST_EXP_001")
    assert loaded is not None
    assert loaded["experiment_id"] == "TEST_EXP_001"
    assert loaded["category"] == "BALANCED_TRAINING"

    # Attempting to register duplicate ID should raise ValueError
    with pytest.raises(ValueError):
        registry.register_experiment(rec)


def test_threshold_calibration_operating_points():
    """Verify selection of Balanced, High Recall, and High Precision operating points."""
    synthetic_sweep = [
        {"confidence_threshold": 0.10, "precision": 0.70, "recall": 0.95, "f1": 0.806, "mAP50": 0.88, "mAP50_95": 0.60},
        {"confidence_threshold": 0.20, "precision": 0.80, "recall": 0.92, "f1": 0.856, "mAP50": 0.89, "mAP50_95": 0.62},
        {"confidence_threshold": 0.25, "precision": 0.88, "recall": 0.90, "f1": 0.890, "mAP50": 0.90, "mAP50_95": 0.63},
        {"confidence_threshold": 0.35, "precision": 0.94, "recall": 0.82, "f1": 0.876, "mAP50": 0.89, "mAP50_95": 0.63},
        {"confidence_threshold": 0.50, "precision": 0.97, "recall": 0.72, "f1": 0.827, "mAP50": 0.86, "mAP50_95": 0.61},
    ]

    points = ThresholdCalibrator.identify_operating_points(synthetic_sweep)

    assert "BALANCED_OPERATING_POINT" in points
    assert "HIGH_RECALL_OPERATING_POINT" in points
    assert "HIGH_PRECISION_OPERATING_POINT" in points

    # Highest F1 is at conf=0.25 (f1=0.890)
    assert points["BALANCED_OPERATING_POINT"]["confidence_threshold"] == 0.25
    # Max recall with precision >= 0.75 is at conf=0.20 (recall=0.92, prec=0.80)
    assert points["HIGH_RECALL_OPERATING_POINT"]["confidence_threshold"] == 0.20
    # Max precision with recall >= 0.70 is at conf=0.50 (prec=0.97, recall=0.72)
    assert points["HIGH_PRECISION_OPERATING_POINT"]["confidence_threshold"] == 0.50


def test_multi_seed_aggregation():
    """Verify multi-seed statistical calculation."""
    seed_records = [
        {"precision": 0.88, "recall": 0.85, "f1": 0.865, "mAP50": 0.895, "mAP50_95": 0.61},
        {"precision": 0.89, "recall": 0.86, "f1": 0.875, "mAP50": 0.902, "mAP50_95": 0.62},
        {"precision": 0.88, "recall": 0.85, "f1": 0.865, "mAP50": 0.898, "mAP50_95": 0.615},
    ]
    stats = MultiSeedEvaluator.aggregate_seed_metrics(seed_records)

    assert "mAP50" in stats
    assert stats["mAP50"]["mean"] == pytest.approx(0.8983, abs=1e-4)
    assert stats["mAP50"]["worst"] == 0.895
    assert stats["mAP50"]["best"] == 0.902
    assert "std" in stats["mAP50"]


def test_model_comparison_promotion_gate(tmp_path):
    """Verify promotion decision gate rejects legacy regression and excessive false alarms."""
    dashboard = ModelComparisonDashboard()

    control_model = {
        "model_name": "sonar_yolov8_fls_trained.pt",
        "dataset": "V2 Baseline",
        "legacy_mAP50": 0.7772,
        "legacy_f1": 0.8669,
        "v3_mAP50": 0.8588,
        "v3_f1": 0.9016,
        "hard_negative_far": 0.2143,
        "cross_domain_mAP": 0.3380,
        "latency_ms": 108.8,
        "fps": 9.2,
        "status": "CONTROL",
    }

    # Candidate 1: Regressed on legacy V2 (> 1.5% regression)
    candidate_regressed = {
        "model_name": "yolov8_fls_v3_candidate.pt",
        "dataset": "V3-A",
        "legacy_mAP50": 0.6898,  # regression = 8.74%
        "legacy_f1": 0.7969,
        "v3_mAP50": 0.6513,
        "v3_f1": 0.7760,
        "hard_negative_far": 0.1429,
        "cross_domain_mAP": 0.2550,
        "latency_ms": 110.2,
        "fps": 9.1,
        "status": "EXPERIMENTAL",
    }

    # Candidate 2: High false alarm rate (> 5%)
    candidate_high_far = {
        "model_name": "yolov8_fls_v3_high_far.pt",
        "dataset": "V3-NoNegatives",
        "legacy_mAP50": 0.7750,
        "legacy_f1": 0.8650,
        "v3_mAP50": 0.8700,
        "v3_f1": 0.9100,
        "hard_negative_far": 0.0850,  # 8.5% FAR > 5% limit
        "cross_domain_mAP": 0.3400,
        "latency_ms": 109.0,
        "fps": 9.2,
        "status": "EXPERIMENTAL",
    }

    json_path = tmp_path / "test_comparison.json"
    md_path = tmp_path / "test_comparison.md"
    decision_path = tmp_path / "test_decision.md"

    results = dashboard.generate_comparison_table(
        production_control=control_model,
        candidate_experiments=[candidate_regressed, candidate_high_far],
        output_json=json_path,
        output_md=md_path,
    )

    models = results["models"]
    assert len(models) == 3

    reg_entry = [m for m in models if m["model_name"] == "yolov8_fls_v3_candidate.pt"][0]
    assert reg_entry["status"] == "REGRESSION"
    assert "REJECTED (LEGACY REGRESSION)" in reg_entry["promotion_verdict"]

    far_entry = [m for m in models if m["model_name"] == "yolov8_fls_v3_high_far.pt"][0]
    assert far_entry["status"] == "HIGH_FALSE_ALARM"
    assert "REJECTED (EXCESSIVE FALSE ALARMS)" in far_entry["promotion_verdict"]

    # Test decision document generation
    dashboard.generate_promotion_decision(results, output_file=decision_path)
    assert decision_path.exists()
    decision_text = decision_path.read_text(encoding="utf-8")
    assert "VERDICT: PRODUCTION MODEL RETAINED" in decision_text
