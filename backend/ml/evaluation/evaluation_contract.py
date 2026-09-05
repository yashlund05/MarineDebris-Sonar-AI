"""
MarineDebris-Sonar-AI: Canonical Evaluation Contract
Establishes a single, immutable, scientifically trustworthy evaluation specification.
Guarantees that all evaluation callers across the repository use identical parameters.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List

ROOT_DIR = Path(__file__).resolve().parents[3]

# Immutable canonical evaluation constants
CANONICAL_BENCHMARK_CONF: float = 0.001    # Standard Ultralytics / COCO / VOC PR-curve integration threshold
CANONICAL_BENCHMARK_IOU: float = 0.70     # Standard Ultralytics validation NMS IoU threshold
OPERATIONAL_MISSION_CONF: float = 0.25    # Calibrated deployment threshold for AUV / ROV surveys
OPERATIONAL_MISSION_IOU: float = 0.45     # Calibrated operational NMS threshold
CANONICAL_IMAGE_SIZE: int = 640           # Square 640x640 letterboxed input
MAX_DETECTIONS: int = 300                 # Maximum detections per image

CANONICAL_CLASS_MAPPING: Dict[int, str] = {
    0: "derelict_fishing_gear",
    1: "general_marine_debris",
    2: "shipwreck",
    3: "pipe_or_cylinder",
    4: "other_man_made_target",
}

EXPECTED_PRODUCTION_CHECKPOINT_SHA256: str = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"
EXPECTED_LEGACY_TEST_IMAGES: int = 37
EXPECTED_LEGACY_TEST_ANNOTATIONS: int = 54
EXPECTED_V3_TEST_IMAGES: int = 80
EXPECTED_V3_TEST_ANNOTATIONS: int = 127
EXPECTED_HARD_NEGATIVE_IMAGES: int = 84


@dataclass(frozen=True)
class EvaluationContract:
    dataset_version: str = "Dataset V3 & Legacy V2 Clean"
    model_version: str = "YOLOv8n-FLS-Production"
    image_size: int = CANONICAL_IMAGE_SIZE
    benchmark_conf: float = CANONICAL_BENCHMARK_CONF
    benchmark_iou: float = CANONICAL_BENCHMARK_IOU
    operational_conf: float = OPERATIONAL_MISSION_CONF
    operational_iou: float = OPERATIONAL_MISSION_IOU
    max_detections: int = MAX_DETECTIONS
    device: str = "cpu"
    classes: Dict[int, str] = field(default_factory=lambda: dict(CANONICAL_CLASS_MAPPING))

    def get_val_args(self, mode: str = "benchmark") -> Dict[str, Any]:
        """
        Returns validated arguments for model.val().
        mode:
          - 'benchmark': Standard ranking metric evaluation (conf=0.001, iou=0.60)
          - 'operational': Mission operational threshold (conf=0.25, iou=0.45)
        """
        if mode == "benchmark":
            return {
                "imgsz": self.image_size,
                "conf": self.benchmark_conf,
                "iou": self.benchmark_iou,
                "max_det": self.max_detections,
                "device": self.device,
                "verbose": False,
                "plots": False,
            }
        elif mode == "operational":
            return {
                "imgsz": self.image_size,
                "conf": self.operational_conf,
                "iou": self.operational_iou,
                "max_det": self.max_detections,
                "device": self.device,
                "verbose": False,
                "plots": False,
            }
        else:
            raise ValueError(f"Unknown evaluation mode: {mode}. Must be 'benchmark' or 'operational'.")


def get_canonical_eval_args(mode: str = "benchmark") -> Dict[str, Any]:
    contract = EvaluationContract()
    return contract.get_val_args(mode=mode)
