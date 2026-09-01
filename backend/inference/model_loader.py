import logging
from backend.config import get_settings

logger = logging.getLogger(__name__)

class ModelLoader:
    _detection_model = None
    _segmentation_model = None
    _device = None
    
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
    def load_detection_model(cls, model_path: str):
        """Load YOLOv8 detection model."""
        try:
            from ultralytics import YOLO
            model = YOLO(model_path)
            # send to device
            model.to(cls.get_device())
            logger.info(f"Successfully loaded detection model from {model_path}")
            return model
        except ImportError:
            logger.warning("ultralytics package not found. Detection model not loaded.")
            return None
        except Exception as e:
            logger.error(f"Failed to load detection model from {model_path}: {e}")
            return None
    
    @classmethod
    def load_segmentation_model(cls, model_path: str):
        """Load segmentation model."""
        # Placeholder for segmentation model
        logger.info(f"Loading segmentation model from {model_path} (Not implemented)")
        return None
    
    @classmethod
    def get_detection_model(cls):
        """Get or load the detection model singleton."""
        if cls._detection_model is None:
            settings = get_settings()
            # Attempt to get model path, fallback if not in settings yet
            model_path = getattr(settings, "DETECTION_MODEL_PATH", "models/best.pt")
            cls._detection_model = cls.load_detection_model(model_path)
        return cls._detection_model
