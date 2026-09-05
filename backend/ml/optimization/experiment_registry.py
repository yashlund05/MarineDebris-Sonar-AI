"""
MarineDebris-Sonar-AI: Machine-Readable Experiment Registry
Maintains an append-only/auditable JSONL record of all optimization runs.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_REGISTRY_PATH = ROOT_DIR / "reports" / "model_optimization_phase3" / "EXPERIMENT_REGISTRY.jsonl"


@dataclass
class OptimizationRecord:
    experiment_id: str
    status: str  # CREATED, TRAINING, COMPLETED, FAILED, EVALUATED, REJECTED, SHORTLISTED, PROMOTION_ELIGIBLE
    seed: int
    dataset_variant: str
    strategy: str
    checkpoint_path: Optional[str] = None
    checkpoint_sha256: Optional[str] = None
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    training_duration_seconds: float = 0.0
    validation_metrics: Dict[str, Any] = field(default_factory=dict)
    canonical_metrics: Dict[str, Any] = field(default_factory=dict)
    operational_metrics: Dict[str, Any] = field(default_factory=dict)
    promotion_verdict: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExperimentRegistry:
    def __init__(self, registry_file: Path = DEFAULT_REGISTRY_PATH):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)

    def load_records(self) -> List[Dict[str, Any]]:
        if not self.registry_file.exists():
            return []
        records = []
        with open(self.registry_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records

    def register(self, record: OptimizationRecord):
        records = self.load_records()
        existing_idx = next((i for i, r in enumerate(records) if r["experiment_id"] == record.experiment_id), None)

        record_dict = record.to_dict()
        if existing_idx is not None:
            records[existing_idx] = record_dict
        else:
            records.append(record_dict)

        with open(self.registry_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def register_experiment(self, summary: Dict[str, Any]):
        records = self.load_records()
        exp_id = summary.get("experiment_id")
        existing_idx = next((i for i, r in enumerate(records) if r.get("experiment_id") == exp_id), None)
        if existing_idx is not None:
            records[existing_idx] = summary
        else:
            records.append(summary)

        with open(self.registry_file, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")

    def get_record(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        records = self.load_records()
        for r in records:
            if r["experiment_id"] == experiment_id:
                return r
        return None
