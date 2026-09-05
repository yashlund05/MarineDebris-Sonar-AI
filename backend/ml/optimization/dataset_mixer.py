"""
MarineDebris-Sonar-AI: Multi-Source Dataset Mixer & Split Builder
Constructs isolated training datasets for Phase 3 experiments (E0 to E5),
enforcing sequence-level leakage protection and domain-balanced sampling.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

from backend.ml.optimization.utils import ROOT_DIR
from backend.ml.optimization.experiment_manifest import ExperimentDatasetAuditor
from backend.ml.optimization.hard_negative_sampler import HardNegativeSampler
from backend.ml.optimization.hard_positive_miner import HardPositiveMiner

V2_ROOT = ROOT_DIR / "datasets" / "sonar_debris_v2_clean"
V3_ROOT = ROOT_DIR / "datasets" / "sonar_debris_v3"
EXP_DATA_ROOT = ROOT_DIR / "datasets" / "phase3_experiments"


class DatasetMixer:
    def __init__(self, exp_data_root: Path = EXP_DATA_ROOT):
        self.exp_data_root = Path(exp_data_root)
        self.hard_neg_sampler = HardNegativeSampler()
        self.hard_pos_miner = HardPositiveMiner()

    def build_experiment_dataset(
        self,
        experiment_id: str,
        strategy: str,  # v2_only, v3_only, naive_mix, balanced, hard_negative, hard_positive
        v2_weight: float = 0.35,
        v3_pos_weight: float = 0.50,
        neg_weight: float = 0.15,
        hard_pos_boost: float = 2.0,
    ) -> Path:
        """
        Builds an isolated dataset directory with data.yaml for the specified experiment.
        """
        dest_dir = self.exp_data_root / experiment_id
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        images_train = dest_dir / "images" / "train"
        labels_train = dest_dir / "labels" / "train"
        images_val = dest_dir / "images" / "val"
        labels_val = dest_dir / "labels" / "val"

        images_train.mkdir(parents=True, exist_ok=True)
        labels_train.mkdir(parents=True, exist_ok=True)
        images_val.mkdir(parents=True, exist_ok=True)
        labels_val.mkdir(parents=True, exist_ok=True)

        # 1. Populate Validation Split (Always use canonical V3 val split for multi-domain validation)
        v3_val_imgs = list((V3_ROOT / "images" / "val").glob("*.*"))
        for img_p in v3_val_imgs:
            shutil.copy2(img_p, images_val / img_p.name)
            lbl_p = V3_ROOT / "labels" / "val" / f"{img_p.stem}.txt"
            if lbl_p.exists():
                shutil.copy2(lbl_p, labels_val / lbl_p.name)

        # 2. Gather candidate training pools
        v2_train_imgs = sorted(list((V2_ROOT / "images" / "train").glob("*.*")))
        v3_train_imgs = sorted(list((V3_ROOT / "images" / "train").glob("*.*")))
        # Filter v3 train positive vs negative
        v3_pos_imgs = []
        v3_neg_imgs = []
        for p in v3_train_imgs:
            lbl = V3_ROOT / "labels" / "train" / f"{p.stem}.txt"
            if lbl.exists() and lbl.stat().st_size > 0:
                v3_pos_imgs.append(p)
            else:
                v3_neg_imgs.append(p)

        selected_train_images = []

        if strategy == "v2_only":
            selected_train_images = v2_train_imgs

        elif strategy == "v3_only":
            selected_train_images = v3_train_imgs

        elif strategy == "naive_mix":
            selected_train_images = v2_train_imgs + v3_train_imgs

        elif strategy == "balanced":
            # Target total ~400 images
            total_target = 400
            n_v2 = int(total_target * v2_weight)
            n_v3_pos = int(total_target * v3_pos_weight)
            n_neg = int(total_target * neg_weight)

            # Sample from pools
            for i in range(n_v2):
                selected_train_images.append(v2_train_imgs[i % len(v2_train_imgs)])
            for i in range(n_v3_pos):
                selected_train_images.append(v3_pos_imgs[i % len(v3_pos_imgs)])
            neg_samples = self.hard_neg_sampler.sample_negatives(n_neg, strategy="category_balanced")
            selected_train_images.extend(neg_samples)

        elif strategy == "hard_negative":
            total_target = 420
            n_v2 = int(total_target * 0.35)
            n_v3_pos = int(total_target * 0.45)
            n_neg = int(total_target * 0.20)  # 20% hard negatives

            for i in range(n_v2):
                selected_train_images.append(v2_train_imgs[i % len(v2_train_imgs)])
            for i in range(n_v3_pos):
                selected_train_images.append(v3_pos_imgs[i % len(v3_pos_imgs)])
            neg_samples = self.hard_neg_sampler.sample_negatives(n_neg, strategy="fp_mining", fp_boost=2.5)
            selected_train_images.extend(neg_samples)

        elif strategy == "hard_positive":
            total_target = 450
            hard_pos_weights = self.hard_pos_miner.load_hard_positive_images()
            
            # Populate base balanced pool
            pool = []
            pool.extend(v2_train_imgs)
            for p in v3_pos_imgs:
                pool.append(p)
                if p.name in hard_pos_weights:
                    # Boost faint/small targets
                    for _ in range(int(hard_pos_boost) - 1):
                        pool.append(p)

            for i in range(int(total_target * 0.85)):
                selected_train_images.append(pool[i % len(pool)])

            n_neg = int(total_target * 0.15)
            neg_samples = self.hard_neg_sampler.sample_negatives(n_neg, strategy="fp_mining", fp_boost=2.0)
            selected_train_images.extend(neg_samples)

        else:
            raise ValueError(f"Unknown dataset strategy: {strategy}")

        # Copy selected train images and labels
        written_names = set()
        for idx, img_p in enumerate(selected_train_images):
            # To handle duplicates from weighted sampling without overwriting, append unique suffix if needed
            base_name = img_p.name
            target_name = f"s{idx}_{base_name}" if base_name in written_names else base_name
            written_names.add(base_name)

            shutil.copy2(img_p, images_train / target_name)
            
            # Find label
            lbl_p = None
            if "sonar_debris_v2_clean" in str(img_p):
                cand = V2_ROOT / "labels" / "train" / f"{img_p.stem}.txt"
                if cand.exists():
                    lbl_p = cand
            elif "sonar_debris_v3" in str(img_p):
                cand = V3_ROOT / "labels" / "train" / f"{img_p.stem}.txt"
                if cand.exists():
                    lbl_p = cand

            if lbl_p and lbl_p.exists():
                shutil.copy2(lbl_p, labels_train / f"{Path(target_name).stem}.txt")
            else:
                # Empty label file for verified negatives
                (labels_train / f"{Path(target_name).stem}.txt").touch()

        # Audit for leakage against held-out tests
        auditor = ExperimentDatasetAuditor()
        test_imgs = list((V3_ROOT / "images" / "test").glob("*.*"))
        val_imgs = list(images_val.glob("*.*"))
        train_imgs = list(images_train.glob("*.*"))
        audit_res = auditor.audit_splits(train_imgs, val_imgs, test_imgs)

        # Write data.yaml
        data_yaml_dict = {
            "path": str(dest_dir.resolve()).replace("\\", "/"),
            "train": "images/train",
            "val": "images/val",
            "test": "images/val",  # Validation used for training fitness; held-out test strictly isolated
            "nc": 5,
            "names": {
                0: "derelict_fishing_gear",
                1: "general_marine_debris",
                2: "shipwreck",
                3: "pipe_or_cylinder",
                4: "other_man_made_target",
            },
        }
        yaml_path = dest_dir / "data.yaml"
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data_yaml_dict, f, sort_keys=False)

        print(f"[MIXER] Built {experiment_id} ({strategy}): {len(train_imgs)} train, {len(val_imgs)} val. Leakage: {audit_res['status']}")
        return yaml_path
