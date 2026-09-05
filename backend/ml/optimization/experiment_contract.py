"""
MarineDebris-Sonar-AI: Immutable Experiment Contract
Codifies experiment configuration, preventing runtime drift and ensuring full reproducibility.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from backend.ml.optimization.utils import (
    ROOT_DIR,
    PRODUCTION_CHECKPOINT_PATH,
    FROZEN_PRODUCTION_SHA256,
    verify_production_checkpoint,
    compute_sha256,
    get_system_environment,
)


@dataclass
class ExperimentContract:
    experiment_id: str
    experiment_name: str
    experiment_family: str  # E0_CONTROL, E1_V3_REAL, E2_NAIVE_MIX, E3_BALANCED, E4_HARD_NEG, E5_HARD_POS, E6_MULTISEED
    dataset_version: str
    dataset_variant: str
    dataset_manifest_sha256: str
    base_checkpoint: str
    base_checkpoint_sha256: str
    output_dir: str
    architecture: str = "YOLOv8n"
    model_size: str = "3.01M"
    imgsz: int = 640
    seed: int = 42
    epochs: int = 12
    batch_size: int = 16
    workers: int = 2
    optimizer: str = "AdamW"
    initial_learning_rate: float = 0.001
    final_learning_rate: float = 0.01
    weight_decay: float = 0.0005
    early_stopping_patience: int = 4
    sampling_strategy: str = "uniform"  # uniform, balanced, hard_negative_weighted, hard_positive_weighted
    sampling_weights: Dict[str, float] = field(default_factory=lambda: {"v2_legacy": 0.35, "v3_positive": 0.50, "v3_negative": 0.15})
    hard_negative_ratio: float = 0.15
    hard_positive_ratio: float = 0.0
    hard_positive_boost: float = 2.0
    dry_run: bool = False
    device: str = "cpu"
    augmentations: Dict[str, Any] = field(default_factory=dict)
    environment: Dict[str, Any] = field(default_factory=dict)

    def validate(self):
        """Validates contract integrity and asserts production protection."""
        verify_production_checkpoint()

        # Protection against overwriting production path
        out_p = Path(self.output_dir).resolve()
        prod_p = PRODUCTION_CHECKPOINT_PATH.resolve()
        if out_p == prod_p or out_p == prod_p.parent:
            raise ValueError(
                f"CRITICAL VIOLATION: Output directory '{out_p}' conflicts with production path '{prod_p}'!"
            )

        if not (0.0 <= self.hard_negative_ratio <= 0.50):
            raise ValueError(f"Invalid hard_negative_ratio: {self.hard_negative_ratio}. Must be in [0.0, 0.50].")

        if self.imgsz not in [640, 768]:
            raise ValueError(f"Unsupported image size: {self.imgsz}. Supported: [640, 768].")

    def save_yaml(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def save_json(self, path: Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = asdict(self)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_yaml(cls, path: Path) -> "ExperimentContract":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return cls(**data)
