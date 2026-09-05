"""
MarineDebris-Sonar-AI: Train Experiment Runner
Executes a single Phase 3 experiment training run under strict contract validation,
leakage checks, and automated post-training benchmarking.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional
import torch
import numpy as np
from ultralytics import YOLO

from backend.ml.optimization.utils import (
    ROOT_DIR,
    PRODUCTION_CHECKPOINT_PATH,
    FROZEN_PRODUCTION_SHA256,
    verify_production_checkpoint,
    compute_sha256,
    get_system_environment,
)
from backend.ml.optimization.experiment_contract import ExperimentContract
from backend.ml.optimization.dataset_mixer import DatasetMixer
from backend.ml.optimization.augmentation_policy import SonarAugmentationPolicy
from backend.ml.optimization.benchmark_suite import BenchmarkSuite
from backend.ml.optimization.subgroup_analysis import SubgroupAnalyzer
from backend.ml.optimization.latency_benchmark import LatencyBenchmarker
from backend.ml.optimization.promotion_gate import PromotionGate
from backend.ml.optimization.experiment_registry import ExperimentRegistry


def run_experiment(
    contract: ExperimentContract,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Executes an experiment under contract rules.
    """
    # 1. Assert pre-flight production protection
    verify_production_checkpoint()
    contract.validate()

    out_dir = Path(contract.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save contract metadata
    contract.save_json(out_dir / "contract.json")
    contract.save_yaml(out_dir / "contract.yaml")

    # 2. Build isolated experiment dataset
    strategy_map = {
        "E0_CONTROL": "v2_only",
        "E1_V3_REAL": "v3_only",
        "E2_NAIVE_MIX": "naive_mix",
        "E3_BALANCED": "balanced",
        "E4_HARD_NEG": "hard_negative",
        "E5_HARD_POS": "hard_positive",
        "E6_MULTISEED": "hard_positive",  # Top candidate strategy
    }
    mixer_strategy = strategy_map.get(contract.experiment_family, "balanced")
    mixer = DatasetMixer()
    data_yaml = mixer.build_experiment_dataset(
        experiment_id=contract.experiment_id,
        strategy=mixer_strategy,
        v2_weight=contract.sampling_weights.get("v2_legacy", 0.35),
        v3_pos_weight=contract.sampling_weights.get("v3_positive", 0.50),
        neg_weight=contract.hard_negative_ratio,
        hard_pos_boost=contract.hard_positive_boost,
    )

    if dry_run or contract.dry_run:
        print(f"[DRY-RUN] Experiment {contract.experiment_id} validated successfully.")
        return {
            "experiment_id": contract.experiment_id,
            "status": "DRY_RUN_PASSED",
            "data_yaml": str(data_yaml),
            "output_dir": str(out_dir),
            "base_checkpoint": contract.base_checkpoint,
        }

    # 3. Setup reproducibility seeds
    torch.manual_seed(contract.seed)
    np.random.seed(contract.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(contract.seed)

    # 4. Load base model
    print(f"[TRAIN] Loading base weights from {contract.base_checkpoint}...")
    model = YOLO(contract.base_checkpoint)

    # Augmentation hyperparams
    aug_policy = SonarAugmentationPolicy()
    aug_params = aug_policy.get_yolo_training_args()

    best_weights_path = out_dir / "weights" / "best.pt"
    if (out_dir / "experiment_results.json").exists():
        print(f"[REUSE] Experiment results already exist for {contract.experiment_id}. Loading...")
        with open(out_dir / "experiment_results.json", "r", encoding="utf-8") as f:
            return json.load(f)
    elif best_weights_path.exists() and best_weights_path.stat().st_size > 1000000:
        print(f"[REUSE] Pre-trained weights found at {best_weights_path}. Proceeding directly to benchmarking...")
    else:
        # 5. Execute Training
        print(f"[TRAIN] Starting training for {contract.experiment_id} on {contract.device}...")
        train_results = model.train(
            data=str(data_yaml),
            epochs=contract.epochs,
            batch=contract.batch_size,
            imgsz=contract.imgsz,
            device=contract.device,
            workers=contract.workers,
            optimizer=contract.optimizer,
            lr0=contract.initial_learning_rate,
            lrf=contract.final_learning_rate,
            weight_decay=contract.weight_decay,
            patience=contract.early_stopping_patience,
            project=str(out_dir.parent),
            name=out_dir.name,
            exist_ok=True,
            seed=contract.seed,
            verbose=True,
            **aug_params,
        )

        # Assert production lock immediately after training to ensure production weights untouched
        verify_production_checkpoint()

    # 6. Locate best weights
    best_weights_path = out_dir / "weights" / "best.pt"
    if not best_weights_path.exists():
        # Fallback if Ultralytics saved to nested run
        possible = list(out_dir.glob("**/best.pt"))
        if possible:
            best_weights_path = possible[0]
        else:
            best_weights_path = out_dir / "weights" / "last.pt"

    print(f"[TRAIN] Best weights saved to: {best_weights_path}")
    cand_sha256 = compute_sha256(best_weights_path)

    # 7. Standardized Post-Training Benchmark Suite
    suite = BenchmarkSuite()
    bench_results = suite.run_complete_suite(best_weights_path)

    # 8. Subgroup Analysis on Dataset V3 Held-out Test
    v3_root = ROOT_DIR / "datasets" / "sonar_debris_v3"
    analyzer = SubgroupAnalyzer()
    subgroup_res = analyzer.analyze_dataset(best_weights_path, v3_root, split="test")

    # 9. CPU Latency Benchmark
    benchmarker = LatencyBenchmarker()
    latency_res = benchmarker.benchmark(best_weights_path)

    # 10. Promotion Gate Evaluation
    gate = PromotionGate()
    promotion_res = gate.evaluate_candidate(
        bench_a=bench_results["benchmark_a_legacy_v2"],
        bench_b=bench_results["benchmark_b_v3_held_out"],
        bench_c=bench_results["benchmark_c_hard_negatives"],
        latency=latency_res,
    )

    # 11. Compile Complete Experiment Results
    experiment_summary = {
        "experiment_id": contract.experiment_id,
        "experiment_name": contract.experiment_name,
        "experiment_family": contract.experiment_family,
        "seed": contract.seed,
        "checkpoint_path": str(best_weights_path),
        "checkpoint_sha256": cand_sha256,
        "benchmark_a": bench_results["benchmark_a_legacy_v2"],
        "benchmark_b": bench_results["benchmark_b_v3_held_out"],
        "benchmark_c": bench_results["benchmark_c_hard_negatives"],
        "benchmark_d": bench_results["benchmark_d_cross_domain"],
        "subgroup_analysis": subgroup_res,
        "latency": latency_res,
        "promotion_gate": promotion_res.to_dict() if hasattr(promotion_res, "to_dict") else promotion_res,
    }

    # Save results JSON
    with open(out_dir / "experiment_results.json", "w", encoding="utf-8") as f:
        json.dump(experiment_summary, f, indent=2)

    # Register in experiment registry
    registry = ExperimentRegistry()
    registry.register_experiment(experiment_summary)

    print(f"[COMPLETE] Experiment {contract.experiment_id} finished. Gate: {promotion_res['status']}")
    return experiment_summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarineDebris-Sonar-AI Phase 3 Train Experiment")
    parser.add_argument("--contract", type=str, help="Path to experiment contract YAML")
    parser.add_argument("--experiment-id", type=str, default="P3_E3_BALANCED")
    parser.add_argument("--family", type=str, default="E3_BALANCED")
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.contract:
        contract = ExperimentContract.from_yaml(Path(args.contract))
    else:
        out_dir = ROOT_DIR / "models" / "detection" / "experiments" / "phase3" / args.experiment_id
        contract = ExperimentContract(
            experiment_id=args.experiment_id,
            experiment_name=f"Phase 3 {args.family}",
            experiment_family=args.family,
            dataset_version="v3.0",
            dataset_variant="fls_balanced",
            dataset_manifest_sha256="canonical_v3_manifest",
            base_checkpoint=str(PRODUCTION_CHECKPOINT_PATH),
            base_checkpoint_sha256=FROZEN_PRODUCTION_SHA256,
            output_dir=str(out_dir),
            epochs=args.epochs,
            batch_size=args.batch_size,
            seed=args.seed,
            dry_run=args.dry_run,
        )

    run_experiment(contract, dry_run=args.dry_run)
