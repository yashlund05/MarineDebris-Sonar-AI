"""
MarineDebris-Sonar-AI: Intelligent Hard-Negative Sampler
Categorizes verified negative sonar frames (natural quarry seabed vs watertank wall reverberation)
and manages false-positive memory to prioritize recurrent failure modes.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[3]
FP_REGISTRY_PATH = ROOT_DIR / "reports" / "model_optimization_phase3" / "mining" / "false_positive_registry.jsonl"


class HardNegativeSampler:
    def __init__(
        self,
        negatives_dir: Path = ROOT_DIR / "datasets" / "sonar_debris_v3" / "hard_negatives",
        fp_registry_path: Path = FP_REGISTRY_PATH,
    ):
        self.negatives_dir = Path(negatives_dir)
        self.fp_registry_path = Path(fp_registry_path)
        self.fp_registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        all_neg = sorted(list(self.negatives_dir.glob("*.png")) + list(self.negatives_dir.glob("*.jpg")))
        # Strictly exclude any images present in V3 validation or test splits to enforce zero leakage
        v3_val = {p.name for p in (ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "val").glob("*.*")}
        v3_test = {p.name for p in (ROOT_DIR / "datasets" / "sonar_debris_v3" / "images" / "test").glob("*.*")}
        self.negative_images = [p for p in all_neg if p.name not in v3_val and p.name not in v3_test]

    def categorize_negative(self, image_path: Path) -> str:
        name = image_path.name.lower()
        if "wall" in name or "tank" in name or "reverb" in name:
            return "hard_negative_wall"
        elif "quarry" in name or "2016" in name or "frame" in name:
            return "hard_negative_quarry_seabed"
        elif "boundary" in name:
            return "hard_negative_boundary"
        return "hard_negative_other"

    def record_false_positive(
        self,
        image_id: str,
        model_id: str,
        confidence: float,
        bbox: List[float],
        source: str = "hard_negatives",
    ):
        category = self.categorize_negative(Path(image_id))
        record = {
            "image_id": image_id,
            "source": source,
            "model_id": model_id,
            "confidence": round(confidence, 4),
            "bbox": bbox,
            "negative_category": category,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.fp_registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def get_flagged_fp_images(self) -> List[str]:
        if not self.fp_registry_path.exists():
            return []
        flagged = set()
        with open(self.fp_registry_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    data = json.loads(line)
                    flagged.add(data["image_id"])
        return sorted(list(flagged))

    def sample_negatives(
        self,
        target_count: int,
        strategy: str = "fp_mining",
        fp_boost: float = 2.0,
    ) -> List[Path]:
        """
        Samples negatives according to the selected strategy:
        - 'uniform': equal probability
        - 'category_balanced': equal representation of quarry seabed and wall reverberation
        - 'fp_mining': higher probability for images that previously triggered false alarms
        """
        if not self.negative_images:
            return []

        flagged_set = set(self.get_flagged_fp_images())
        quarry = [p for p in self.negative_images if self.categorize_negative(p) == "hard_negative_quarry_seabed"]
        wall = [p for p in self.negative_images if self.categorize_negative(p) != "hard_negative_quarry_seabed"]

        sampled = []
        if strategy == "category_balanced":
            half = target_count // 2
            # Cycle through quarry and wall
            for i in range(half):
                sampled.append(quarry[i % len(quarry)])
            for i in range(target_count - half):
                sampled.append(wall[i % len(wall)])
        elif strategy == "fp_mining":
            # Priority to flagged images
            flagged_paths = [p for p in self.negative_images if p.name in flagged_set]
            non_flagged = [p for p in self.negative_images if p.name not in flagged_set]
            
            # Boost flagged
            pool = []
            for _ in range(int(fp_boost)):
                pool.extend(flagged_paths)
            pool.extend(non_flagged)
            if not pool:
                pool = self.negative_images

            for i in range(target_count):
                sampled.append(pool[i % len(pool)])
        else:  # uniform
            for i in range(target_count):
                sampled.append(self.negative_images[i % len(self.negative_images)])

        return sampled
