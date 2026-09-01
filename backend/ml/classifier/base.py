"""Base interface and data contracts for secondary crop classification."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import numpy as np


@dataclass
class ClassificationResult:
    status: str  # 'available', 'unavailable', 'failed'
    class_name: Optional[str] = None
    confidence: Optional[float] = None
    inference_time_ms: Optional[float] = None
    error_message: Optional[str] = None

    @classmethod
    def unavailable(cls, reason: str = "Classifier weights not installed") -> "ClassificationResult":
        return cls(status="unavailable", error_message=reason)


class ClassifierBackend(ABC):
    """Abstract interface for secondary candidate crop classifiers."""

    def __init__(
        self,
        model_name: str,
        model_version: str = "v1.0",
        weights_path: Optional[str] = None,
    ):
        self.model_name = model_name
        self.model_version = model_version
        self.weights_path = weights_path
        self.supported_classes: List[str] = []

    @abstractmethod
    def predict(self, crop: np.ndarray) -> ClassificationResult:
        """Classify a single detected object crop."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Inspect and return runtime status without fabrication."""
        pass
