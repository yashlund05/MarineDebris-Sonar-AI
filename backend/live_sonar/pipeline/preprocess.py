"""Sonar Preprocessing Profiles for Live Streaming.

Implements REALTIME, BALANCED, and QUALITY preprocessing profiles reusing
existing components from backend/preprocessing/ while preserving raw frame immutability.
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional, Tuple
import cv2
import numpy as np

from backend.preprocessing.clahe import apply_clahe
from backend.preprocessing.denoising import denoise
from backend.preprocessing.normalization import normalize

logger = logging.getLogger(__name__)


class PreprocessingProfile(str, Enum):
    REALTIME = "REALTIME"
    BALANCED = "BALANCED"
    QUALITY = "QUALITY"


def preprocess_live_image(
    raw_image: np.ndarray,
    profile: PreprocessingProfile | str = PreprocessingProfile.REALTIME,
) -> np.ndarray:
    """Preprocess a raw sonar image for live display and AI inference.

    CRITICAL SAFETY REQUIREMENT:
    Never mutates raw_image in place. Always works on a copy.

    Profiles:
    - REALTIME: Fast normalization and lightweight CLAHE for minimal latency.
    - BALANCED: Normalization, CLAHE, and median denoising (standard existing pipeline).
    - QUALITY: Full enhancement with adaptive CLAHE, denoising, and contrast stretching.
    """
    if not isinstance(raw_image, np.ndarray) or raw_image.size == 0:
        return np.zeros((1, 1), dtype=np.uint8)

    # Work strictly on a copy to preserve raw frame immutability
    image = raw_image.copy()

    # Ensure grayscale 2D uint8
    if image.ndim == 3:
        if image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        else:
            image = image[:, :, 0]

    if image.dtype != np.uint8:
        if image.max() <= 1.0:
            image = (image * 255.0).clip(0, 255).astype(np.uint8)
        else:
            image = image.clip(0, 255).astype(np.uint8)

    profile_str = str(profile).upper()
    if profile_str.endswith(".REALTIME"):
        profile_str = "REALTIME"
    elif profile_str.endswith(".BALANCED"):
        profile_str = "BALANCED"
    elif profile_str.endswith(".QUALITY"):
        profile_str = "QUALITY"

    if profile_str == PreprocessingProfile.REALTIME.value:
        # Minimal processing: Fast min-max normalization + fast CLAHE
        norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        processed = clahe.apply(norm)
        return processed

    elif profile_str == PreprocessingProfile.BALANCED.value:
        # Reuses existing backend/preprocessing pipeline blocks
        norm = normalize(image)
        enhanced = apply_clahe(norm, clip_limit=2.5, tile_grid_size=(8, 8))
        denoised = denoise(enhanced, method="median", kernel_size=3)
        return denoised

    elif profile_str == PreprocessingProfile.QUALITY.value:
        # Highest fidelity: Bilateral filtering + dual-pass CLAHE + intensity stretching
        denoised = cv2.bilateralFilter(image, d=5, sigmaColor=50, sigmaSpace=50)
        norm = normalize(denoised)
        clahe1 = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe1.apply(norm)
        # Unsharp mask for high-frequency acoustic edges
        gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
        sharpened = cv2.addWeighted(enhanced, 1.3, gaussian, -0.3, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)

    else:
        # Default fallback to REALTIME
        norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        return norm
