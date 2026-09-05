"""
Unit and Integration Tests for ML Training, Evaluation, and Benchmarking Engine.
"""

import os
import pytest
from pathlib import Path
from backend.ml.training.dataset_audit import audit_dataset
from backend.ml.training.evaluate_yolo import evaluate_model
from backend.ml.training.benchmark import benchmark_model_latency
from backend.ml.training.error_analysis import perform_error_analysis


def test_dataset_audit_and_integrity():
    res = audit_dataset("datasets/sonar_debris_v2_clean")
    assert res["total_images"] == 238
    assert res["total_annotations"] == 371
    assert "train" in res["splits"]
    assert "val" in res["splits"]
    assert "test" in res["splits"]
    assert res["splits"]["train"]["images"] == 166
    assert res["splits"]["val"]["images"] == 35
    assert res["splits"]["test"]["images"] == 37
    # Zero leakage check
    assert len(res["split_leakage_check"]["train_vs_val"]) == 0
    assert len(res["split_leakage_check"]["train_vs_test"]) == 0
    assert len(res["split_leakage_check"]["val_vs_test"]) == 0
    assert len(res["label_issues"]) == 0


def test_promoted_model_loading_and_evaluation():
    model_path = "models/detection/sonar_yolov8_fls_trained.pt"
    assert os.path.exists(model_path)

    report = evaluate_model(
        model_path=model_path,
        data_yaml="datasets/sonar_debris_v2_clean/data.yaml",
        split="val",
        imgsz=640,
        batch=8,
        conf_thresholds=[0.30],
        device="cpu",
    )
    assert "overall_metrics" in report
    metrics = report["overall_metrics"]
    assert metrics["mAP50"] >= 0.85
    assert metrics["mAP50_95"] >= 0.55
    assert metrics["precision"] >= 0.85
    assert metrics["recall"] >= 0.80


def test_latency_benchmarking():
    model_path = "models/detection/sonar_yolov8_fls_trained.pt"
    res = benchmark_model_latency(model_path=model_path, num_runs=5, imgsz=640)
    assert res["num_runs"] == 5
    assert "stages" in res
    assert "inference" in res["stages"]
    assert res["stages"]["inference"]["mean_ms"] > 0
    assert res["throughput_fps"] > 0


def test_error_analysis_execution(tmp_path):
    model_path = "models/detection/sonar_yolov8_fls_trained.pt"
    analysis = perform_error_analysis(
        model_path=model_path,
        dataset_dir="datasets/sonar_debris_v2_clean",
        split="val",
        conf_threshold=0.30,
        save_dir=str(tmp_path),
    )
    assert analysis["counts"]["total_ground_truth"] == 51
    assert analysis["counts"]["true_positives"] > 35
    assert (tmp_path / "error_analysis_report.md").exists()
