"""
Abstract Base Class and Interface for Sonar Image Enhancement Providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import numpy as np
from backend.enhancement.types import EnhancementResult


class EnhancementProvider(ABC):
    """Abstract interface implemented by classical and learned enhancement backends."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique provider identifier."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Semantic version of the provider algorithm/weights."""
        pass

    @property
    @abstractmethod
    def provider_type(self) -> str:
        """Type category: 'classical' or 'learned'."""
        pass

    @property
    @abstractmethod
    def validation_status(self) -> str:
        """Validation status: 'PRODUCTION', 'VALIDATED', 'EXPERIMENTAL', or 'UNAVAILABLE'."""
        pass

    @abstractmethod
    def supports(self, image: np.ndarray) -> bool:
        """Validates that the input image meets numeric, dimensional, and dtype criteria."""
        pass

    @abstractmethod
    def enhance(self, image: np.ndarray, parameters: Optional[Dict[str, Any]] = None) -> EnhancementResult:
        """
        Executes enhancement, returning canonical float32 [0, 1] grayscale image.
        Must preserve exact spatial dimensions (H x W).
        """
        pass

    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Returns provider specifications, provenance, and parameters."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Verifies runtime dependencies, weights availability, and memory readiness."""
        pass
