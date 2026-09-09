"""
SidescanTools Sonar Image Enhancement Service.
Provides domain-aware acoustic radiometric filtering, dB conversion, 2D-FFT stripe suppression,
CLAHE, homomorphic sharpening, and display-only false-color visualization.
"""

from .config import SonarEnhancementConfig, ColormapName, DetectionInputMode
from .exceptions import (
    SonarEnhancementError,
    UnsupportedFormatError,
    MetadataMissingError,
    ProcessingTimeoutError,
    CorruptImageError,
)
from .sidescan_adapter import SidescanToolsAdapter
from .pipeline import SonarEnhancementPipeline
from .processor import SonarEnhancementProcessor
from .quality_metrics import compute_acoustic_quality_metrics

__all__ = [
    "SonarEnhancementConfig",
    "ColormapName",
    "DetectionInputMode",
    "SonarEnhancementError",
    "UnsupportedFormatError",
    "MetadataMissingError",
    "ProcessingTimeoutError",
    "CorruptImageError",
    "SidescanToolsAdapter",
    "SonarEnhancementPipeline",
    "SonarEnhancementProcessor",
    "compute_acoustic_quality_metrics",
]
