"""
MarineDebris-Sonar-AI: Model Promotion Utility
Safely handles production model replacement with strict opt-in approval:
- NEVER auto-promotes.
- Requires --require-explicit-approval AND --confirm flags.
- Validates candidate against PromotionGate.
- Archives current production model to models/detection/archive/ before replacement.
- Records cryptographic audit trail.
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from backend.ml.optimization.utils import (
    ROOT_DIR,
    PRODUCTION_CHECKPOINT_PATH,
    FROZEN_PRODUCTION_SHA256,
    compute_sha256,
    verify_production_checkpoint,
)
from backend.ml.optimization.benchmark_suite import BenchmarkSuite
from backend.ml.optimization.latency_benchmark import LatencyBenchmarker
from backend.ml.optimization.promotion_gate import PromotionGate

ARCHIVE_DIR = ROOT_DIR / "models" / "detection" / "archive"
PROMOTION_LOG_PATH = ROOT_DIR / "reports" / "model_optimization_phase3" / "PROMOTION_LOG.jsonl"


def evaluate_candidate_eligibility(candidate_path: Path) -> Dict[str, Any]:
    """Runs Benchmark Suite and Promotion Gate on candidate checkpoint."""
    candidate_path = Path(candidate_path)
    if not candidate_path.exists():
        raise FileNotFoundError(f"Candidate checkpoint not found at: {candidate_path}")

    suite = BenchmarkSuite()
    bench = suite.run_complete_suite(candidate_path)
    lat = LatencyBenchmarker().benchmark(candidate_path)
    gate = PromotionGate()
    decision = gate.evaluate_candidate(
        bench_a=bench["benchmark_a_legacy_v2"],
        bench_b=bench["benchmark_b_v3_held_out"],
        bench_c=bench["benchmark_c_hard_negatives"],
        latency=lat,
    )
    return {
        "candidate_path": str(candidate_path),
        "candidate_sha256": compute_sha256(candidate_path),
        "benchmarks": bench,
        "latency": lat,
        "promotion_gate": decision.to_dict() if hasattr(decision, "to_dict") else decision,
    }


def promote_candidate(
    candidate_path: Path,
    explicit_approval: bool = False,
    confirmed: bool = False,
) -> Dict[str, Any]:
    """Promotes candidate checkpoint to production upon explicit approval."""
    candidate_path = Path(candidate_path)
    eligibility = evaluate_candidate_eligibility(candidate_path)

    if not eligibility["promotion_gate"]["overall_pass"]:
        print("\n[PROMOTION REJECTED] Candidate failed gating criteria:")
        for chk in eligibility["promotion_gate"]["checks"]:
            status = "PASS" if chk["passed"] else "FAIL"
            print(f"  [{status}] {chk['name']}: {chk['observed']} (Required: {chk['required']})")
        return {"status": "PROMOTION_REJECTED", "details": eligibility}

    print("\n[GATE CHECK PASSED] Candidate meets all non-regression and performance criteria.")

    if not (explicit_approval and confirmed):
        print("\n[PROMOTION PENDING EXPLICIT APPROVAL]")
        print("Candidate is ELIGIBLE for promotion, but production weights remain UNCHANGED.")
        print("To replace production weights, run with:")
        print(f"  python -m backend.ml.optimization.promote_model --candidate \"{candidate_path}\" --require-explicit-approval --confirm")
        return {
            "status": "PHASE_3_COMPLETE_CANDIDATE_PROMOTION_ELIGIBLE",
            "message": "Candidate is fully eligible. Awaiting explicit user confirmation.",
            "details": eligibility,
        }

    # Execute Promotion with Backup
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = ARCHIVE_DIR / f"production_backup_{timestamp}.pt"

    # 1. Backup existing production model
    shutil.copy2(PRODUCTION_CHECKPOINT_PATH, backup_path)
    backup_sha256 = compute_sha256(backup_path)
    print(f"[ARCHIVE] Existing production model archived to: {backup_path} (SHA256: {backup_sha256})")

    # 2. Copy candidate to production path
    shutil.copy2(candidate_path, PRODUCTION_CHECKPOINT_PATH)
    new_prod_sha256 = compute_sha256(PRODUCTION_CHECKPOINT_PATH)
    print(f"[PROMOTED] Candidate promoted to production: {PRODUCTION_CHECKPOINT_PATH} (SHA256: {new_prod_sha256})")

    # 3. Write promotion log
    PROMOTION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_entry = {
        "promoted_at": datetime.now(timezone.utc).isoformat(),
        "previous_production_backup": str(backup_path),
        "previous_production_sha256": backup_sha256,
        "new_production_path": str(PRODUCTION_CHECKPOINT_PATH),
        "new_production_sha256": new_prod_sha256,
        "candidate_source_path": str(candidate_path),
        "eligibility_summary": eligibility,
    }
    with open(PROMOTION_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    return {
        "status": "PROMOTED_TO_PRODUCTION",
        "backup_path": str(backup_path),
        "new_production_sha256": new_prod_sha256,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MarineDebris-Sonar-AI Safe Model Promotion")
    parser.add_argument("--candidate", type=str, required=True, help="Path to candidate .pt file")
    parser.add_argument("--require-explicit-approval", action="store_true", help="Acknowledge promotion authorization")
    parser.add_argument("--confirm", action="store_true", help="Execute physical replacement of production weights")
    args = parser.parse_args()

    promote_candidate(
        candidate_path=Path(args.candidate),
        explicit_approval=args.require_explicit_approval,
        confirmed=args.confirm,
    )
