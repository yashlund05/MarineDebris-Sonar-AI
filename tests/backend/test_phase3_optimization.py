"""
MarineDebris-Sonar-AI: Phase 3 Model Optimization Test Suite
Comprehensive 20-point test suite validating contract immutability,
acoustic augmentation physics, zero-leakage enforcement, subgroup profiling,
promotion gating, and multi-seed stability.
"""

import os
import shutil
import pytest
from pathlib import Path
from typing import Dict, Any

from backend.ml.optimization.utils import (
    ROOT_DIR,
    PRODUCTION_CHECKPOINT_PATH,
    FROZEN_PRODUCTION_SHA256,
    verify_production_checkpoint,
    compute_sha256,
)
from backend.ml.optimization.experiment_contract import ExperimentContract
from backend.ml.optimization.augmentation_policy import SonarAugmentationPolicy
from backend.ml.optimization.experiment_manifest import ExperimentDatasetAuditor
from backend.ml.optimization.hard_negative_sampler import HardNegativeSampler
from backend.ml.optimization.hard_positive_miner import HardPositiveMiner
from backend.ml.optimization.dataset_mixer import DatasetMixer
from backend.ml.optimization.subgroup_analysis import SubgroupAnalyzer, calculate_iou
from backend.ml.optimization.latency_benchmark import LatencyBenchmarker
from backend.ml.optimization.promotion_gate import PromotionGate, PromotionResult
from backend.ml.optimization.candidate_ranker import CandidateRanker
from backend.ml.optimization.promote_model import promote_candidate


class TestPhase3Optimization:
    def test_01_production_lock_integrity(self):
        """1. Asserts immutable production checkpoint SHA256 matches frozen baseline."""
        assert PRODUCTION_CHECKPOINT_PATH.exists()
        current_sha = compute_sha256(PRODUCTION_CHECKPOINT_PATH)
        assert current_sha == FROZEN_PRODUCTION_SHA256
        assert verify_production_checkpoint() is True

    def test_02_contract_path_conflict_protection(self, tmp_path):
        """2. Asserts contract raises ValueError if output conflicts with production path."""
        contract = ExperimentContract(
            experiment_id="P3_TEST_CONFLICT",
            experiment_name="Conflict Test",
            experiment_family="E0_CONTROL",
            dataset_version="v3.0",
            dataset_variant="fls",
            dataset_manifest_sha256="test_sha",
            base_checkpoint=str(PRODUCTION_CHECKPOINT_PATH),
            base_checkpoint_sha256=FROZEN_PRODUCTION_SHA256,
            output_dir=str(PRODUCTION_CHECKPOINT_PATH.parent),  # Path conflict
        )
        with pytest.raises(ValueError, match="CRITICAL VIOLATION"):
            contract.validate()

    def test_03_acoustic_augmentation_physics(self):
        """3. Enforces acoustic sonar augmentation constraints (no vertical flips or optical color shifts)."""
        policy = SonarAugmentationPolicy()
        args = policy.get_yolo_training_args()
        assert args["flipud"] == 0.0, "Vertical flip violates acoustic grazing incidence physics!"
        assert args["hsv_h"] == 0.0, "Optical hue shift violates single-channel sonar physics!"
        assert args["hsv_s"] == 0.0, "Optical saturation shift violates single-channel sonar physics!"
        assert args["fliplr"] == 0.50, "Port/starboard swath horizontal reflection must be permitted"

    def test_04_dataset_auditor_flags_leakage(self, tmp_path):
        """4. Asserts ExperimentDatasetAuditor catches and flags cross-split image leakage."""
        auditor = ExperimentDatasetAuditor()
        img1 = tmp_path / "img1.png"
        img2 = tmp_path / "img2.png"
        img1.touch()
        img2.touch()

        # Leakage: img1 in train and test
        with pytest.raises(RuntimeError, match="DATA LEAKAGE DETECTED"):
            auditor.audit_splits(train_images=[img1, img2], val_images=[], test_images=[img1])

    def test_05_dataset_auditor_passes_clean_splits(self, tmp_path):
        """5. Asserts ExperimentDatasetAuditor passes when splits are completely disjoint."""
        auditor = ExperimentDatasetAuditor()
        t1 = tmp_path / "t1.png"
        v1 = tmp_path / "v1.png"
        te1 = tmp_path / "te1.png"
        t1.touch()
        v1.touch()
        te1.touch()

        res = auditor.audit_splits(train_images=[t1], val_images=[v1], test_images=[te1])
        assert res["status"] == "ZERO_LEAKAGE_VERIFIED"
        assert res["train_val_overlap"] == 0
        assert res["train_test_overlap"] == 0

    def test_06_hard_negative_categorization(self, tmp_path):
        """6. Asserts HardNegativeSampler categorizes quarry vs wall reverberation."""
        sampler = HardNegativeSampler()
        quarry_p = Path("sonar_quarry_frame_01.png")
        wall_p = Path("watertank_wall_echo_02.png")
        assert sampler.categorize_negative(quarry_p) == "hard_negative_quarry_seabed"
        assert sampler.categorize_negative(wall_p) == "hard_negative_wall"

    def test_07_hard_negative_split_isolation(self):
        """7. Verifies that validation and test negatives are strictly excluded from the training sampler."""
        sampler = HardNegativeSampler()
        v3_val = {p.name for p in (ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "val").glob("*.*")}
        v3_test = {p.name for p in (ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "test").glob("*.*")}
        
        for p in sampler.negative_images:
            assert p.name not in v3_val, f"Validation image {p.name} leaked into training negative sampler!"
            assert p.name not in v3_test, f"Test image {p.name} leaked into training negative sampler!"

    def test_08_hard_positive_miner_boost(self, tmp_path):
        """8. Asserts HardPositiveMiner registers hard positives and applies 2.0x boost."""
        reg_file = tmp_path / "hard_pos.jsonl"
        miner = HardPositiveMiner(registry_path=reg_file)
        miner.record_hard_positive(
            image_id="faint_sample_01.png",
            sequence_id="seq_faint",
            gt_bbox=[0.5, 0.5, 0.05, 0.05],
            failure_type="faint",
        )
        weights = miner.load_hard_positive_images()
        assert "faint_sample_01.png" in weights
        assert weights["faint_sample_01.png"] == 2.0

    def test_09_dataset_mixer_v2_only_dry_run(self, tmp_path):
        """9. Asserts DatasetMixer builds isolated V2-only training dataset."""
        mixer = DatasetMixer(exp_data_root=tmp_path)
        yaml_p = mixer.build_experiment_dataset("EXP_TEST_V2", strategy="v2_only")
        assert yaml_p.exists()
        train_imgs = list((tmp_path / "EXP_TEST_V2" / "images" / "train").glob("*.*"))
        assert len(train_imgs) == 166

    def test_10_dataset_mixer_balanced_dry_run(self, tmp_path):
        """10. Asserts DatasetMixer builds balanced dataset with 0 leakage."""
        mixer = DatasetMixer(exp_data_root=tmp_path)
        yaml_p = mixer.build_experiment_dataset("EXP_TEST_BALANCED", strategy="balanced")
        assert yaml_p.exists()
        train_imgs = list((tmp_path / "EXP_TEST_BALANCED" / "images" / "train").glob("*.*"))
        assert len(train_imgs) == 400

    def test_11_calculate_iou_correctness(self):
        """11. Asserts calculate_iou computes exact bounding box intersections."""
        box1 = [10.0, 10.0, 30.0, 30.0]  # area = 400
        box2 = [20.0, 10.0, 40.0, 30.0]  # area = 400, inter = 10 * 20 = 200
        iou = calculate_iou(box1, box2)
        assert abs(iou - (200.0 / 600.0)) < 1e-4

        # Non-overlapping
        box3 = [50.0, 50.0, 70.0, 70.0]
        assert calculate_iou(box1, box3) == 0.0

    def test_12_latency_benchmarker_dummy_run(self):
        """12. Verifies LatencyBenchmarker executes on CPU and returns complete statistics."""
        bench = LatencyBenchmarker(warmup_runs=2, timed_runs=5)
        res = bench.benchmark(PRODUCTION_CHECKPOINT_PATH)
        assert "latency_mean_ms" in res
        assert "latency_p95_ms" in res
        assert "fps" in res
        assert res["latency_mean_ms"] > 0
        assert "meets_budget" in res
        assert isinstance(res["meets_budget"], bool)
        assert res["meets_budget"] == (res["latency_p95_ms"] <= bench.budget_ms)

    def test_13_promotion_gate_ideal_pass(self):
        """13. Asserts PromotionGate passes when candidate preserves V2 and improves FAR."""
        gate = PromotionGate()
        bench_a = {"mAP50": 0.8950, "recall": 0.9050}   # Improves V2 baseline (0.8921, 0.9015)
        bench_b = {"mAP50": 0.9250, "recall": 0.9100}   # Improves V3 baseline (0.9192, 0.9024)
        bench_c = {"negative_image_FAR": 0.1500, "total_false_positive_boxes": 14}  # Better than 21.43% / 18
        lat = {"latency_p95_ms": 65.0, "fps": 18.0}
        seed_stats = {"mAP50_std": 0.0080}

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat, seed_stats)
        assert decision.overall_pass is True
        assert decision.status == "ELIGIBLE_FOR_PROMOTION"

    def test_14_promotion_gate_rejects_v2_map50_regression(self):
        """14. Asserts PromotionGate rejects when V2 mAP50 regresses > 1.0% absolute points."""
        gate = PromotionGate()
        # V2 base: 0.8921. Drop to 0.8750 is -1.71% abs regression (> 1.0% abs limit)
        bench_a = {"mAP50": 0.8750, "recall": 0.9000}
        bench_b = {"mAP50": 0.9300, "recall": 0.9100}
        bench_c = {"negative_image_FAR": 0.1000, "total_false_positive_boxes": 8}
        lat = {"latency_p95_ms": 60.0}

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat)
        assert decision.overall_pass is False
        assert decision.status == "REJECTED"

    def test_15_promotion_gate_rejects_v2_recall_regression(self):
        """15. Asserts PromotionGate rejects when V2 Recall regresses > 2.0% absolute points."""
        gate = PromotionGate()
        # V2 recall base: 0.9015. Drop to 0.8700 is -3.15% abs regression (> 2.0% abs limit)
        bench_a = {"mAP50": 0.8921, "recall": 0.8700}
        bench_b = {"mAP50": 0.9200, "recall": 0.9024}
        bench_c = {"negative_image_FAR": 0.1400, "total_false_positive_boxes": 12}
        lat = {"latency_p95_ms": 55.0}

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat)
        assert decision.overall_pass is False
        assert decision.status == "REJECTED"

    def test_16_promotion_gate_rejects_excessive_far(self):
        """16. Asserts PromotionGate rejects when FAR exceeds 21.43%."""
        gate = PromotionGate()
        bench_a = {"mAP50": 0.8921, "recall": 0.9015}
        bench_b = {"mAP50": 0.9200, "recall": 0.9024}
        # FAR: 25.0% (> 21.43% baseline)
        bench_c = {"negative_image_FAR": 0.2500, "total_false_positive_boxes": 22}
        lat = {"latency_p95_ms": 50.0}

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat)
        assert decision.overall_pass is False
        assert decision.status == "REJECTED"

    def test_17_promotion_gate_rejects_excessive_latency(self):
        """17. Asserts PromotionGate rejects when CPU P95 latency exceeds 125.0 ms."""
        gate = PromotionGate()
        bench_a = {"mAP50": 0.8921, "recall": 0.9015}
        bench_b = {"mAP50": 0.9200, "recall": 0.9024}
        bench_c = {"negative_image_FAR": 0.1400, "total_false_positive_boxes": 12}
        lat = {"latency_p95_ms": 145.0}  # Over budget

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat)
        assert decision.overall_pass is False
        assert decision.status == "REJECTED"

    def test_18_promotion_gate_rejects_unstable_seeds(self):
        """18. Asserts PromotionGate rejects when multi-seed mAP50 std exceeds 1.5%."""
        gate = PromotionGate()
        bench_a = {"mAP50": 0.8921, "recall": 0.9015}
        bench_b = {"mAP50": 0.9200, "recall": 0.9024}
        bench_c = {"negative_image_FAR": 0.1400, "total_false_positive_boxes": 12}
        lat = {"latency_p95_ms": 50.0}
        seed_stats = {"mAP50_std": 0.0250}  # 2.5% std dev > 1.5% limit

        decision = gate.evaluate_candidate(bench_a, bench_b, bench_c, lat, seed_stats)
        assert decision.overall_pass is False
        assert decision.status == "REJECTED"

    def test_19_candidate_ranker_ordering(self):
        """19. Asserts CandidateRanker orders candidate models by multi-objective score."""
        ranker = CandidateRanker()
        cands = [
            {
                "experiment_id": "MOD_POOR",
                "benchmark_a": {"mAP50": 0.80},
                "benchmark_b": {"mAP50": 0.80},
                "benchmark_c": {"negative_image_FAR": 0.30},
            },
            {
                "experiment_id": "MOD_EXCELLENT",
                "benchmark_a": {"mAP50": 0.90},
                "benchmark_b": {"mAP50": 0.93},
                "benchmark_c": {"negative_image_FAR": 0.12},
            },
        ]
        ranked = ranker.rank_candidates(cands)
        assert ranked[0]["experiment_id"] == "MOD_EXCELLENT"
        assert ranked[0]["rank"] == 1
        assert ranked[1]["experiment_id"] == "MOD_POOR"
        assert ranked[1]["rank"] == 2

    def test_20_promote_model_blocks_without_confirmation(self, tmp_path, monkeypatch):
        """20. Asserts promote_model leaves production weights untouched without explicit confirmation."""
        initial_sha = compute_sha256(PRODUCTION_CHECKPOINT_PATH)
        fake_cand = tmp_path / "fake_cand.pt"
        shutil.copy2(PRODUCTION_CHECKPOINT_PATH, fake_cand)

        # Mock evaluate_candidate_eligibility to simulate an eligible candidate
        mock_eligibility = {
            "candidate_path": str(fake_cand),
            "candidate_sha256": compute_sha256(fake_cand),
            "promotion_gate": {
                "overall_pass": True,
                "promotion_eligible": True,
                "checks": [],
            },
        }
        monkeypatch.setattr(
            "backend.ml.optimization.promote_model.evaluate_candidate_eligibility",
            lambda cand: mock_eligibility,
        )

        # Call promote without --confirm
        res = promote_candidate(fake_cand, explicit_approval=True, confirmed=False)
        assert res["status"] == "PHASE_3_COMPLETE_CANDIDATE_PROMOTION_ELIGIBLE"
        
        # Verify production weights strictly unchanged
        assert compute_sha256(PRODUCTION_CHECKPOINT_PATH) == initial_sha
