"""Base interface and data structures for sonar acoustic segmentation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import numpy as np


@dataclass
class SegmentationResult:
    status: str  # 'available', 'unavailable', 'failed'
    confidence: Optional[float] = None
    mask_area: Optional[float] = None
    mask_rle: Optional[str] = None
    contour: Optional[List[List[int]]] = None
    refined_bbox: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None

    @classmethod
    def unavailable(cls, reason: str = "Segmentation weights not installed") -> "SegmentationResult":
        return cls(status="unavailable", error_message=reason)


class BaseSegmenter(ABC):
    """Abstract interface for semantic segmentation models."""

    def __init__(self, model_name: str, weights_path: Optional[str] = None):
        self.model_name = model_name
        self.weights_path = weights_path

    @abstractmethod
    def predict(self, tile: np.ndarray, bbox: Dict[str, int]) -> SegmentationResult:
        """Segment the detected object within the provided tile and bounding box."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Return truthful runtime status and device availability."""
        pass
