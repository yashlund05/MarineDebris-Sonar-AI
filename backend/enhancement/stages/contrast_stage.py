"""
Adaptive contrast and dynamic-range enhancement stage.

Implements Requirement R12:
- Parameterized CLAHE equalization
- Controlled unsharp masking with halo suppression
- Power-law gamma dynamic mapping
- Safeguards against false boundary and halo artifact creation.
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, List
import numpy as np
import cv2

from backend.enhancement.pipeline_base import (
    SonarEnhancementStage,
    SonarEnhancementContext,
)


class AdaptiveContrastStage(SonarEnhancementStage):
    """
    Equalizes local acoustic contrast with controlled clipping to protect acoustic shadows.
    """

    def __init__(
        self,
        clip_limit: float = 1.8,
        tile_grid_size: Tuple[int, int] = (8, 8),
        gamma: float = 1.0,
        unsharp_amount: float = 0.0,  # 0.0 = disabled
        unsharp_sigma: float = 1.0,
        name: str = "AdaptiveContrastStage",
    ):
        # If unsharp amount > 0.4, it can create artificial edge halos unsafe for YOLO detectors
        is_safe = (unsharp_amount <= 0.3 and clip_limit <= 2.5)
        super().__init__(name=name, is_ai_safe_default=is_safe)
        self.clip_limit = clip_limit
        self.tile_grid_size = tile_grid_size
        self.gamma = gamma
        self.unsharp_amount = unsharp_amount
        self.unsharp_sigma = unsharp_sigma

    def validate_input(self, image: np.ndarray, context: SonarEnhancementContext) -> bool:
        return image is not None and image.ndim == 2 and image.size > 0

    def process(
        self, image: np.ndarray, context: SonarEnhancementContext
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        img = np.clip(image, 0.0, 1.0).astype(np.float32)

        # 1. CLAHE in 8-bit integer space
        img_u8 = (img * 255.0).astype(np.uint8)
        clahe = cv2.createCLAHE(
            clipLimit=self.clip_limit, tileGridSize=self.tile_grid_size
        )
        equalized_u8 = clahe.apply(img_u8)
        equalized = (equalized_u8.astype(np.float32) / 255.0)

        # 2. Optional Gamma correction
        if abs(self.gamma - 1.0) > 0.01:
            equalized = np.power(equalized, self.gamma)

        # 3. Optional controlled unsharp masking with halo clipping
        if self.unsharp_amount > 0.01:
            blurred = cv2.GaussianBlur(
                equalized, (0, 0), sigmaX=self.unsharp_sigma, sigmaY=self.unsharp_sigma
            )
            detail = equalized - blurred
            # Soft clamp detail to prevent ringing halos around high-reflectivity targets
            detail = np.clip(detail, -0.15, 0.15)
            sharpened = equalized + self.unsharp_amount * detail
            equalized = np.clip(sharpened, 0.0, 1.0)

        diff = np.abs(equalized - img)
        metrics = {
            "clip_limit": self.clip_limit,
            "tile_grid": list(self.tile_grid_size),
            "gamma": self.gamma,
            "unsharp_amount": self.unsharp_amount,
            "mean_contrast_delta": float(np.mean(diff)),
            "max_contrast_delta": float(np.max(diff)),
        }

        return equalized.astype(np.float32), metrics
