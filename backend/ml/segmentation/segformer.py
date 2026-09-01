"""SegFormer transformer-based segmentation for acoustic sonar targets."""

import os
import logging
from typing import Optional, Dict, Any
import numpy as np

from backend.ml.segmentation.base import BaseSegmenter, SegmentationResult
from backend.inference.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class SegFormerSegmenter(BaseSegmenter):
    """Transformer-based segmentation interface."""

    def __init__(
        self,
        model_name: str = "sonar_segformer_debris_v1",
        weights_path: str = "models/segmentation/sonar_segformer_debris_v1.pt",
    ):
        super().__init__(model_name=model_name, weights_path=weights_path)
        self.architecture = "SegFormer"
        self._model = None

    def health(self) -> Dict[str, Any]:
        device = ModelLoader.get_device()
        if not self.weights_path or not os.path.exists(self.weights_path):
            return {
                "model_name": self.model_name,
                "architecture": self.architecture,
                "status": "MISSING_WEIGHTS",
                "is_ready": False,
                "device": device,
                "weights_path": self.weights_path,
                "details": f"SegFormer checkpoint not found at {self.weights_path}",
            }
        return {
            "model_name": self.model_name,
            "architecture": self.architecture,
            "status": "READY",
            "is_ready": True,
            "device": device,
            "weights_path": self.weights_path,
            "details": "SegFormer weights verified",
        }

    def predict(self, tile: np.ndarray, bbox: Dict[str, int]) -> SegmentationResult:
        health_info = self.health()
        if not health_info["is_ready"]:
            return SegmentationResult.unavailable(health_info["details"])
        return SegmentationResult.unavailable("SegFormer execution runtime not active")
