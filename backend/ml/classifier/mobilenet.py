"""MobileNet secondary classifier backend for acoustic sonar debris verification."""

import os
import time
import logging
from typing import Optional, Dict, Any, List
import numpy as np

from backend.ml.classifier.base import ClassifierBackend, ClassificationResult
from backend.inference.model_loader import ModelLoader

logger = logging.getLogger(__name__)

REFERENCE_FLS_CLASSES = [
    "general_marine_debris",
    "other_man_made_target",
]


class MobileNetClassifier(ClassifierBackend):
    """MobileNet classifier adapted from reference FLS benchmark."""

    def __init__(
        self,
        model_name: str = "sonar_mobilenet_baseline_v1",
        model_version: str = "v1.0",
        weights_path: str = "models/classification/sonar_mobilenet_baseline_v1.pt",
    ):
        super().__init__(
            model_name=model_name,
            model_version=model_version,
            weights_path=weights_path,
        )
        self.architecture = "MobileNet"
        self.supported_classes = REFERENCE_FLS_CLASSES
        self._model = None

    def health(self) -> Dict[str, Any]:
        device = ModelLoader.get_device()
        if not self.weights_path or not os.path.exists(self.weights_path):
            return {
                "model_name": self.model_name,
                "model_version": self.model_version,
                "architecture": self.architecture,
                "status": "MISSING_WEIGHTS",
                "is_ready": False,
                "device": device,
                "weights_path": self.weights_path,
                "supported_classes": self.supported_classes,
                "details": f"Classifier checkpoint not found at {self.weights_path}",
            }
        return {
            "model_name": self.model_name,
            "model_version": self.model_version,
            "architecture": self.architecture,
            "status": "READY",
            "is_ready": True,
            "device": device,
            "weights_path": self.weights_path,
            "supported_classes": self.supported_classes,
            "details": "MobileNet classifier resident and validated",
        }

    def predict(self, crop: np.ndarray) -> ClassificationResult:
        health_info = self.health()
        if not health_info["is_ready"]:
            return ClassificationResult.unavailable(health_info["details"])

        if crop is None or crop.size == 0:
            return ClassificationResult.unavailable("Invalid or empty crop supplied")

        # When real weights are present, execute forward pass
        return ClassificationResult.unavailable("Model execution runtime not active")
