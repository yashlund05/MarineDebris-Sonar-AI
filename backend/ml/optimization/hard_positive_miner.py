"""
MarineDebris-Sonar-AI: Hard-Positive Miner & Registry
Identifies, categorizes, and boosts difficult marine debris targets:
- Faint debris (low contrast backscatter)
- Small targets (<40 px)
- Long-range contacts (>3.5 m range)
- Low-confidence detections (<0.40 confidence)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).resolve().parents[3]
HARD_POS_REGISTRY_PATH = ROOT_DIR / "reports" / "model_optimization_phase3" / "mining" / "hard_positive_registry.jsonl"


class HardPositiveMiner:
    def __init__(self, registry_path: Path = HARD_POS_REGISTRY_PATH):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

    def record_hard_positive(
        self,
        image_id: str,
        sequence_id: str,
        gt_bbox: List[float],
        failure_type: str,  # faint, small, long_range, low_confidence
        production_conf: float = 0.0,
        candidate_conf: float = 0.0,
        bbox_dim_px: float = 0.0,
    ):
        record = {
            "image_id": image_id,
            "sequence_id": sequence_id,
            "gt_bbox": gt_bbox,
            "failure_type": failure_type,
            "production_confidence": round(production_conf, 4),
            "candidate_confidence": round(candidate_conf, 4),
            "bbox_dim_px": round(bbox_dim_px, 1),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with open(self.registry_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def load_hard_positive_images(self) -> Dict[str, float]:
        """
        Returns a mapping of image_name -> sampling_weight boost.
        Default boost is 2.0x for hard positives.
        """
        if not self.registry_path.exists():
            # Seed with hard positive mining from Phase 2
            p2_mining = ROOT_DIR / "reports" / "model_optimization" / "hard_positive_mining.json"
            if p2_mining.exists():
                try:
                    with open(p2_mining, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    for item in data.get("missed_debris_samples", []):
                        self.record_hard_positive(
                            image_id=item["image"],
                            sequence_id="mined_p2",
                            gt_bbox=[],
                            failure_type="missed_debris",
                            bbox_dim_px=item.get("max_dim_px", 0.0),
                        )
                    for item in data.get("low_confidence_samples", []):
                        self.record_hard_positive(
                            image_id=item["image"],
                            sequence_id="mined_p2",
                            gt_bbox=[],
                            failure_type="low_confidence",
                            production_conf=item.get("confidence", 0.0),
                            bbox_dim_px=item.get("max_dim_px", 0.0),
                        )
                except Exception:
                    pass

        weights = {}
        if self.registry_path.exists():
            with open(self.registry_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        entry = json.loads(line)
                        img_id = entry["image_id"]
                        weights[img_id] = 2.0
        return weights
