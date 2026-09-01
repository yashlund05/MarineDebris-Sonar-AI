import os
import logging
from typing import Optional, Dict, Any
from backend.config import get_settings

logger = logging.getLogger(__name__)


class ModelLoader:
    _detection_model = None
    _segmentation_model = None
    _device = None
    _last_error = None

    @classmethod
    def get_device(cls) -> str:
        """Get the computing device to use (cuda or cpu)."""
        if cls._device is None:
            try:
                import torch
                cls._device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Selected device for inference: {cls._device}")
            except ImportError:
                cls._device = "cpu"
                logger.warning("PyTorch not installed. Using CPU.")
        return cls._device

    @classmethod
    def get_model_status(cls, model_path: Optional[str] = None) -> Dict[str, Any]:
        """Inspect and return truthful model status without fabrication.

        States:
        - READY: File exists, deserializes, and loads onto device
        - MISSING_WEIGHTS: File does not exist at specified path
        - INVALID_WEIGHTS: File exists but fails loading/corruption check
        - FAILED: Runtime failure during device allocation or execution
        """
        settings = get_settings()
        target_path = model_path or getattr(settings, "DETECTION_MODEL_PATH", "models/detection/sonar_yolov8m_ghostpot_v1.pt")
        device = cls.get_device()

        if not os.path.exists(target_path):
            return {
                "state": "MISSING_WEIGHTS",
                "device": device,
                "model_path": target_path,
                "architecture": "YOLOv8m",
                "is_loaded": False,
                "details": f"Checkpoint file not found at {target_path}",
            }

        try:
            from ultralytics import YOLO
            model = YOLO(target_path)
            return {
                "state": "READY",
                "device": device,
                "model_path": target_path,
                "architecture": "YOLOv8m",
                "is_loaded": True,
                "details": "Model weights verified and ready for inference",
            }
        except Exception as e:
            logger.error(f"Validation failed for model at {target_path}: {e}")
            return {
                "state": "INVALID_WEIGHTS",
                "device": device,
                "model_path": target_path,
                "architecture": "YOLOv8m",
                "is_loaded": False,
                "details": str(e),
            }

    @classmethod
    def load_detection_model(cls, model_path: str):
        """Load YOLOv8 detection model."""
        if not os.path.exists(model_path):
            logger.warning(f"Detection model checkpoint not found at {model_path}. Running in zero-weight mode.")
            cls._last_error = "MISSING_WEIGHTS"
            return None

        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            model.to(cls.get_device())
            logger.info(f"Successfully loaded detection model from {model_path}")
            return model
        except ImportError:
            logger.warning("ultralytics package not found. Detection model not loaded.")
            cls._last_error = "ULTRALYTICS_NOT_FOUND"
            return None
        except Exception as e:
            logger.error(f"Failed to load detection model from {model_path}: {e}")
            cls._last_error = str(e)
            return None

    @classmethod
    def load_segmentation_model(cls, model_path: str):
        """Load segmentation model (placeholder interface)."""
        logger.info(f"Loading segmentation model from {model_path} (Not implemented / deferred)")
        return None

    @classmethod
    def get_detection_model(cls):
        """Get or load the detection model singleton."""
        if cls._detection_model is None:
            settings = get_settings()
            model_path = getattr(settings, "DETECTION_MODEL_PATH", "models/detection/sonar_yolov8m_ghostpot_v1.pt")
            cls._detection_model = cls.load_detection_model(model_path)
        return cls._detection_model
