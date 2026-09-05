"""
MarineDebris-Sonar-AI: Phase 3 Experiment Matrix Orchestrator
Sequentially executes and tracks Experiments E0 through E5:
- E0: V2 Legacy Training Control (genuine training control)
- E1: V3 Real-Only Training
- E2: Naive V2 + V3 Mix (Unweighted)
- E3: Balanced Sampling (35% V2 / 50% V3 Pos / 15% Neg)
- E4: Hard-Negative Aware Sampling (Clutter & reverberation focus)
- E5: Hard-Positive Aware Mining (Faint, small, far-range boost)

Supports --dry-run for complete configuration, path, and leakage verification before training.
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

from backend.ml.optimization.utils import (
    ROOT_DIR,
    PRODUCTION_CHECKPOINT_PATH,
    FROZEN_PRODUCTION_SHA256,
    verify_production_checkpoint,
)
from backend.ml.optimization.experiment_contract import ExperimentContract
from backend.ml.optimization.train_experiment import run_experiment
from backend.ml.optimization.candidate_ranker import CandidateRanker


EXPERIMENT_CONFIGS = [
    {
        "experiment_id": "P3_E0_V2_CONTROL",
        "experiment_name": "Phase 3 E0: V2 Legacy Training Control",
        "experiment_family": "E0_CONTROL",
        "hard_negative_ratio": 0.0,
        "sampling_weights": {"v2_legacy": 1.0, "v3_positive": 0.0, "v3_negative": 0.0},
        "hard_positive_boost": 1.0,
        "epochs": 5,
    },
    {
        "experiment_id": "P3_E1_V3_REAL",
        "experiment_name": "Phase 3 E1: V3 Real-Only Training",
        "experiment_family": "E1_V3_REAL",
        "hard_negative_ratio": 0.15,
        "sampling_weights": {"v2_legacy": 0.0, "v3_positive": 0.85, "v3_negative": 0.15},
        "hard_positive_boost": 1.0,
        "epochs": 5,
    },
    {
        "experiment_id": "P3_E2_NAIVE_MIX",
        "experiment_name": "Phase 3 E2: Naive V2+V3 Unweighted Mix",
        "experiment_family": "E2_NAIVE_MIX",
        "hard_negative_ratio": 0.12,
        "sampling_weights": {"v2_legacy": 0.35, "v3_positive": 0.53, "v3_negative": 0.12},
        "hard_positive_boost": 1.0,
        "epochs": 5,
    },
    {
        "experiment_id": "P3_E3_BALANCED",
        "experiment_name": "Phase 3 E3: Balanced Domain Sampling",
        "experiment_family": "E3_BALANCED",
        "hard_negative_ratio": 0.15,
        "sampling_weights": {"v2_legacy": 0.35, "v3_positive": 0.50, "v3_negative": 0.15},
        "hard_positive_boost": 1.0,
        "epochs": 5,
    },
    {
        "experiment_id": "P3_E4_HARD_NEGATIVE",
        "experiment_name": "Phase 3 E4: Hard-Negative Aware Sampling",
        "experiment_family": "E4_HARD_NEG",
        "hard_negative_ratio": 0.20,
        "sampling_weights": {"v2_legacy": 0.35, "v3_positive": 0.45, "v3_negative": 0.20},
        "hard_positive_boost": 1.0,
        "epochs": 5,
    },
    {
        "experiment_id": "P3_E5_HARD_POSITIVE",
        "experiment_name": "Phase 3 E5: Hard-Positive & Negative Mining",
        "experiment_family": "E5_HARD_POS",
        "hard_negative_ratio": 0.15,
        "sampling_weights": {"v2_legacy": 0.35, "v3_positive": 0.50, "v3_negative": 0.15},
        "hard_positive_boost": 2.0,
        "epochs": 5,
    },
]


def run_matrix(dry_run: bool = False, epochs_override: int = None) -> Dict[str, Any]:
    """Runs the entire Phase 3 experiment matrix."""
    print("=" * 70)
    print("  MarineDebris-Sonar-AI: Phase 3 Experiment Matrix Runner")
    print(f"  Dry-Run Mode: {dry_run}")
    print("=" * 70)

    verify_production_checkpoint()
    results = []

    for cfg in EXPERIMENT_CONFIGS:
        exp_id = cfg["experiment_id"]
        out_dir = ROOT_DIR / "models" / "detection" / "experiments" / "phase3" / exp_id
        epochs = epochs_override if epochs_override is not None else cfg["epochs"]

        contract = ExperimentContract(
            experiment_id=exp_id,
            experiment_name=cfg["experiment_name"],
            experiment_family=cfg["experiment_family"],
            dataset_version="v3.0",
            dataset_variant=cfg["experiment_family"].lower(),
            dataset_manifest_sha256="canonical_v3_manifest",
            base_checkpoint=str(PRODUCTION_CHECKPOINT_PATH),
            base_checkpoint_sha256=FROZEN_PRODUCTION_SHA256,
            output_dir=str(out_dir),
            epochs=epochs,
            batch_size=16,
            seed=42,
            sampling_weights=cfg["sampling_weights"],
            hard_negative_ratio=cfg["hard_negative_ratio"],
            hard_positive_boost=cfg["hard_positive_boost"],
            dry_run=dry_run,
        )

        print(f"\n--- Launching {exp_id} ({cfg['experiment_family']}) ---")
        exp_res = run_experiment(contract, dry_run=dry_run)
        results.append(exp_res)

    if dry_run:
        print("\n[DRY-RUN COMPLETE] All 6 experiment configurations validated successfully!")
        return {"status": "ALL_DRY_RUNS_PASSED", "experiments": results}

    # Rank candidates if not dry run
    ranker = CandidateRanker()
    ranked_candidates = ranker.rank_candidates(results)

    print("\n" + "=" * 70)
    print("  PHASE 3 MATRIX EXECUTION COMPLETE — CANDIDATE RANKINGS")
    print("=" * 70)
    for c in ranked_candidates:
        print(f"Rank {c['rank']}: {c['experiment_id']} | Score: {c['composite_score']} | Status: {c['promotion_gate']['status']}")

    return {
        "status": "MATRIX_TRAINED_AND_EVALUATED",
        "ranked_candidates": ranked_candidates,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3 Experiment Matrix Runner")
    parser.add_argument("--dry-run", action="store_true", help="Validate configurations without training")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of training epochs")
    args = parser.parse_args()

    run_matrix(dry_run=args.dry_run, epochs_override=args.epochs)
