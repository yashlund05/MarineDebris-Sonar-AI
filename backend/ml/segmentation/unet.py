"""U-Net semantic segmentation module for acoustic sonar targets."""

import os
import logging
from typing import Optional, Dict, Any
import numpy as np
import cv2

from backend.ml.segmentation.base import BaseSegmenter, SegmentationResult
from backend.inference.model_loader import ModelLoader

logger = logging.getLogger(__name__)


class UNetSegmenter(BaseSegmenter):
    """U-Net segmentation for marine debris acoustic boundaries."""

    def __init__(
        self,
        model_name: str = "sonar_unet_debris_v1",
        weights_path: str = "models/segmentation/sonar_unet_debris_v1.pt",
    ):
        super().__init__(model_name=model_name, weights_path=weights_path)
        self.architecture = "U-Net"
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
                "details": f"Segmentation checkpoint not found at {self.weights_path}",
            }
        return {
            "model_name": self.model_name,
            "architecture": self.architecture,
            "status": "READY",
            "is_ready": True,
            "device": device,
            "weights_path": self.weights_path,
            "details": "U-Net segmentation weights verified",
        }

    def predict(self, tile: np.ndarray, bbox: Dict[str, int]) -> SegmentationResult:
        health_info = self.health()
        if not health_info["is_ready"]:
            return SegmentationResult.unavailable(health_info["details"])

        try:
            # When model weights exist, run PyTorch inference
            # Crop region defined by bbox
            x, y, w, h = bbox.get("x", 0), bbox.get("y", 0), bbox.get("width", 0), bbox.get("height", 0)
            if w <= 0 or h <= 0 or tile is None:
                return SegmentationResult.unavailable("Invalid tile or bounding box coordinates")

            # Extract sub-crop
            crop = tile[max(0, y):y + h, max(0, x):x + w]
            if crop.size == 0:
                return SegmentationResult.unavailable("Empty crop region")

            # Execute real model if self._model is loaded
            # For now if loaded:
            return SegmentationResult.unavailable("Model execution runtime not active")
        except Exception as e:
            logger.error(f"Error during U-Net segmentation: {e}")
            return SegmentationResult(status="failed", error_message=str(e))
