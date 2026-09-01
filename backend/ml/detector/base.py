"""Base detector contract for acoustic sonar target detection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from backend.inference.detector import RawDetection, CLASS_NAMES


@dataclass
class DetectorHealth:
    model_name: str
    architecture: str
    status: str  # 'READY', 'MISSING_WEIGHTS', 'INVALID_WEIGHTS', 'EXPERIMENTAL'
    device: str
    weights_path: Optional[str]
    is_ready: bool
    details: str
    supported_classes: List[str]


class BaseDetector(ABC):
    """Abstract interface for sonar object detectors."""

    def __init__(self, model_name: str, weights_path: Optional[str] = None):
        self.model_name = model_name
        self.weights_path = weights_path
        self.supported_classes: List[str] = []

    @abstractmethod
    def predict(
        self,
        tiles: List[Any],
        conf_threshold: float = 0.35,
        device: Optional[str] = None,
    ) -> List[List[RawDetection]]:
        """Run batch inference on acoustic image tiles."""
        pass

    @abstractmethod
    def health(self) -> DetectorHealth:
        """Inspect and return truthful runtime health."""
        pass
