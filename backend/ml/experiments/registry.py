"""
MarineDebris-Sonar-AI: Machine-Readable Experiment Registry
Maintains immutable logs of every model experiment, ensuring complete traceability,
reproducibility metadata, and preventing overwriting of prior trials.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone


def get_git_commit() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
        return res.stdout.strip() or "UNKNOWN_UNTRACKED"
    except Exception:
        return "UNKNOWN_UNTRACKED"


@dataclass
class ExperimentRecord:
    experiment_id: str
    category: str
    description: str
    timestamp: str
    git_commit: str
    dataset_manifest_hash: str
    dataset_variant: str
    model_architecture: str
    pretrained_checkpoint: str
    seed: int
    image_size: int
    batch_size: int
    epochs: int
    optimizer: str
    learning_rate: float
    scheduler: str
    augmentation_config: Dict[str, Any]
    hardware: Dict[str, Any]
    software_versions: Dict[str, str]
    training_duration_seconds: float
    validation_metrics: Dict[str, Any]
    test_metrics: Dict[str, Any]  # legacy_v2, v3, hard_negatives, cross_domain
    checkpoint_hash: str
    checkpoint_path: str
    status: str  # CONTROL, EXPERIMENTAL, PROMISING, REGRESSION, ARCHIVED, PRODUCTION_CANDIDATE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ExperimentRegistry:
    def __init__(self, registry_file: Path = Path("reports/model_optimization/experiment_registry.json")):
        self.registry_file = Path(registry_file)
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        self.records: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.registry_file.exists():
            try:
                with open(self.registry_file, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception:
                self.records = {}

    def save(self):
        with open(self.registry_file, "w", encoding="utf-8") as f:
            json.dump(self.records, f, indent=2)

    def register_experiment(self, record: ExperimentRecord, allow_overwrite: bool = False):
        if record.experiment_id in self.records and not allow_overwrite:
            raise ValueError(f"Experiment '{record.experiment_id}' already registered! Overwrites forbidden.")
        self.records[record.experiment_id] = record.to_dict()
        self.save()

    def get_experiment(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        return self.records.get(experiment_id)

    def list_experiments(self) -> List[Dict[str, Any]]:
        return list(self.records.values())
