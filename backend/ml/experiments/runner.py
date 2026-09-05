"""
MarineDebris-Sonar-AI: Controlled Experiment Runner
Orchestrates training runs with environment logging, hardware tracking,
automatic evaluation across the four benchmarks, and registry recording.
"""

import os
import sys
import json
import time
import platform
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import torch
from ultralytics import YOLO

ROOT_DIR = Path(__file__).resolve().parents[3]

from backend.ml.experiments.config import (
    ExperimentConfig,
    verify_production_lock,
    compute_sha256,
)
from backend.ml.experiments.registry import (
    ExperimentRegistry,
    ExperimentRecord,
    get_git_commit,
)
from backend.ml.experiments.evaluator import MultiBenchmarkEvaluator


class ExperimentRunner:
    def __init__(self, registry: Optional[ExperimentRegistry] = None):
        self.registry = registry or ExperimentRegistry()
        self.evaluator = MultiBenchmarkEvaluator()

    @staticmethod
    def get_hardware_info() -> Dict[str, Any]:
        return {
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
            "active_torch_threads": torch.get_num_threads(),
            "cuda_available": torch.cuda.is_available(),
            "device": "cuda" if torch.cuda.is_available() else "cpu",
        }

    @staticmethod
    def get_software_versions() -> Dict[str, str]:
        import ultralytics
        import cv2
        return {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "ultralytics": ultralytics.__version__,
            "opencv": cv2.__version__,
            "os": f"{platform.system()} {platform.release()}",
        }

    def run_experiment(self, config: ExperimentConfig) -> ExperimentRecord:
        # Enforce baseline protection lock before launching
        verify_production_lock()

        exp_dir = Path(config.output_dir) / config.experiment_id
        if exp_dir.exists():
            raise ValueError(f"Experiment directory '{exp_dir}' already exists! Aborting to prevent overwrite.")

        exp_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=======================================================")
        print(f"RUNNING EXPERIMENT: {config.experiment_id} ({config.category})")
        print(f"Dataset YAML: {config.data_yaml} | Imgsz: {config.imgsz} | Epochs: {config.epochs}")
        print(f"=======================================================\n")

        t0 = time.perf_counter()

        model = YOLO(config.base_model)
        train_args = {
            "data": str(Path(config.data_yaml).resolve()),
            "epochs": config.epochs,
            "batch": config.batch_size,
            "imgsz": config.imgsz,
            "device": config.device,
            "workers": 2,
            "optimizer": config.optimizer,
            "lr0": config.lr0,
            "lrf": config.lrf,
            "weight_decay": config.weight_decay,
            "box": config.box_loss_weight,
            "cls": config.cls_loss_weight,
            "dfl": config.dfl_loss_weight,
            "hsv_v": config.hsv_v,
            "degrees": config.degrees,
            "translate": config.translate,
            "scale": config.scale,
            "fliplr": config.fliplr,
            "flipud": config.flipud,
            "mosaic": config.mosaic,
            "seed": config.seed,
            "project": str(exp_dir.resolve()),
            "name": "train_run",
            "verbose": False,
            "plots": False,
        }

        train_results = model.train(**train_args)
        duration = round(time.perf_counter() - t0, 2)

        best_pt = exp_dir / "train_run" / "weights" / "best.pt"
        if not best_pt.exists():
            best_pt = exp_dir / "train_run" / "weights" / "last.pt"

        checkpoint_hash = compute_sha256(best_pt) if best_pt.exists() else "NO_CHECKPOINT"

        # Manifest hash
        manifest_p = ROOT_DIR / "datasets" / "sonar_debris_v3" / "DATASET_MANIFEST.json"
        manifest_hash = compute_sha256(manifest_p) if manifest_p.exists() else "UNKNOWN"

        # Multi-benchmark evaluation
        print(f"[RUNNER] Running 4-Benchmark standardized evaluation for {config.experiment_id}...")
        test_metrics = self.evaluator.run_complete_evaluation(best_pt, imgsz=config.imgsz)

        # Validation metrics
        val_eval = self.evaluator.evaluate_yolo_split(model, Path(config.data_yaml), split="val", imgsz=config.imgsz)

        record = ExperimentRecord(
            experiment_id=config.experiment_id,
            category=config.category,
            description=config.description,
            timestamp=datetime.now(timezone.utc).isoformat(),
            git_commit=get_git_commit(),
            dataset_manifest_hash=manifest_hash,
            dataset_variant=Path(config.data_yaml).parent.name,
            model_architecture="YOLOv8n",
            pretrained_checkpoint=config.base_model,
            seed=config.seed,
            image_size=config.imgsz,
            batch_size=config.batch_size,
            epochs=config.epochs,
            optimizer=config.optimizer,
            learning_rate=config.lr0,
            scheduler="cosine",
            augmentation_config={
                "hsv_v": config.hsv_v,
                "degrees": config.degrees,
                "translate": config.translate,
                "scale": config.scale,
                "fliplr": config.fliplr,
                "mosaic": config.mosaic,
            },
            hardware=self.get_hardware_info(),
            software_versions=self.get_software_versions(),
            training_duration_seconds=duration,
            validation_metrics=val_eval,
            test_metrics=test_metrics,
            checkpoint_hash=checkpoint_hash,
            checkpoint_path=str(best_pt),
            status="EXPERIMENTAL",
        )

        self.registry.register_experiment(record)

        # Save individual experiment config and metadata
        with open(exp_dir / "experiment_config.json", "w", encoding="utf-8") as f:
            json.dump(record.to_dict(), f, indent=2)

        print(f"[RUNNER] Experiment {config.experiment_id} completed in {duration}s. Hash: {checkpoint_hash[:12]}")
        return record
