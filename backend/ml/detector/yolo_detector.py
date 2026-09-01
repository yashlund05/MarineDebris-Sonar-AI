"""Ultralytics YOLOv8m detector implementation for acoustic sonar."""

import os
import logging
from typing import List, Any, Optional

from backend.ml.detector.base import BaseDetector, DetectorHealth
from backend.inference.detector import RawDetection, CLASS_NAMES, detect_tiles
from backend.inference.model_loader import ModelLoader

logger = logging.getLogger(__name__)

# Canonical trained classes for the current FLS sonar dataset
FLS_TRAINED_CLASSES = [
    "general_marine_debris",
    "other_man_made_target",
]


class YOLOv8Detector(BaseDetector):
    """Primary acoustic detector utilizing YOLOv8m."""

    def __init__(
        self,
        model_name: str = "sonar_yolov8m_ghostpot_v1",
        weights_path: str = "models/detection/sonar_yolov8m_ghostpot_v1.pt",
    ):
        super().__init__(model_name=model_name, weights_path=weights_path)
        self.architecture = "YOLOv8m"
        self._model = None
        self.supported_classes = FLS_TRAINED_CLASSES

    def _ensure_loaded(self) -> Optional[Any]:
        if self._model is None and self.weights_path and os.path.exists(self.weights_path):
            self._model = ModelLoader.load_detection_model(self.weights_path)
        return self._model

    def health(self) -> DetectorHealth:
        device = ModelLoader.get_device()
        if not self.weights_path or not os.path.exists(self.weights_path):
            return DetectorHealth(
                model_name=self.model_name,
                architecture=self.architecture,
                status="MISSING_WEIGHTS",
                device=device,
                weights_path=self.weights_path,
                is_ready=False,
                details=f"Checkpoint file not found at {self.weights_path}. Model un-trained.",
                supported_classes=self.supported_classes,
            )

        model = self._ensure_loaded()
        if model is None:
            return DetectorHealth(
                model_name=self.model_name,
                architecture=self.architecture,
                status="INVALID_WEIGHTS",
                device=device,
                weights_path=self.weights_path,
                is_ready=False,
                details="Failed to initialize YOLO model from weights file",
                supported_classes=self.supported_classes,
            )

        return DetectorHealth(
            model_name=self.model_name,
            architecture=self.architecture,
            status="READY",
            device=device,
            weights_path=self.weights_path,
            is_ready=True,
            details="YOLOv8m weights validated and resident on device",
            supported_classes=self.supported_classes,
        )

    def predict(
        self,
        tiles: List[Any],
        conf_threshold: float = 0.35,
        device: Optional[str] = None,
    ) -> List[List[RawDetection]]:
        model = self._ensure_loaded()
        if model is None:
            logger.warning(
                "YOLOv8Detector invoked with MISSING_WEIGHTS. Returning truthful empty detections."
            )
            return [[] for _ in tiles]

        target_device = device or ModelLoader.get_device()
        return detect_tiles(tiles, model=model, conf_threshold=conf_threshold, device=target_device)
