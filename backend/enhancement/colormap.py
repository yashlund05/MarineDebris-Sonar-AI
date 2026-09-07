"""
Display-Only Pseudocolor Palette Transformation Layer.

CRITICAL ARCHITECTURAL RULE:
This colormap module produces DISPLAY-ONLY images for human operator inspection.
The canonical scientific output of all enhancement algorithms is float32 [0, 1] grayscale.
Under NO circumstances should the output of apply_palette() be passed to YOLOv8,
detector scoring, or metric computation routines.
"""

import numpy as np
import cv2
from typing import Dict, List
from backend.enhancement.types import PaletteType


def create_sonar_amber_lut() -> np.ndarray:
    """
    Generates a 256x1x3 BGR lookup table matching the Sound Metrics ARIS 3000 Copper/Amber palette.
    - 0: Pure acoustic shadow / background mute (Black [0, 0, 0])
    - Low: Deep dark sepia / amber
    - Mid: Rich orange/gold
    - High: Brilliant yellow/white specular highlights
    """
    lut = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        norm = i / 255.0
        # Red channel: Rises early, stays high
        r = int(np.clip(norm * 1.55 * 255.0, 0, 255))
        # Green channel: Rises in mid-to-high intensities to create orange/gold
        g = int(np.clip((norm - 0.15) * 1.25 * 255.0, 0, 255)) if norm > 0.15 else 0
        # Blue channel: Only activates at peak specular highlight
        b = int(np.clip((norm - 0.70) * 3.33 * 255.0, 0, 255)) if norm > 0.70 else 0
        lut[i, 0] = [b, g, r]  # OpenCV BGR format
    return lut


def create_thermal_lut() -> np.ndarray:
    """
    Generates a 256x1x3 BGR lookup table designed to preserve monotonic intensity ordering.
    Progression: Black -> Deep Purple/Magenta -> Red -> Amber -> Pale Yellow.
    """
    lut = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        norm = i / 255.0
        # Smooth polynomial transition
        r = int(np.clip(255.0 * (1.5 * norm), 0, 255))
        g = int(np.clip(255.0 * (norm ** 2 * 1.2), 0, 255))
        b = int(np.clip(255.0 * (np.sin(norm * np.pi) * 0.6 + (norm ** 3) * 0.4), 0, 255))
        lut[i, 0] = [b, g, r]
    return lut


def create_inferno_lut() -> np.ndarray:
    """
    Uses OpenCV's standard cv2.COLORMAP_INFERNO.
    """
    gray_ramp = np.arange(256, dtype=np.uint8).reshape((256, 1))
    return cv2.applyColorMap(gray_ramp, cv2.COLORMAP_INFERNO)


# Precomputed static LUT cache
_LUT_CACHE = {
    PaletteType.AMBER: create_sonar_amber_lut(),
    PaletteType.THERMAL: create_thermal_lut(),
    PaletteType.INFERNO: create_inferno_lut(),
}


def apply_palette(
    canonical_gray: np.ndarray,
    palette: PaletteType = PaletteType.AMBER
) -> np.ndarray:
    """
    Applies display pseudocolor LUT to canonical grayscale image.
    
    Args:
        canonical_gray: 2D numpy array, float32 in [0, 1] or uint8 in [0, 255].
        palette: PaletteType enum (AMBER, THERMAL, INFERNO, GRAYSCALE).
        
    Returns:
        3-channel BGR uint8 image suitable for JPEG/PNG encoding and canvas rendering.
    """
    if canonical_gray.size == 0:
        return np.zeros((0, 0, 3), dtype=np.uint8)

    if canonical_gray.ndim != 2:
        raise ValueError(f"apply_palette requires 2D grayscale input, got shape {canonical_gray.shape}")

    # Convert to uint8 domain [0, 255]
    if canonical_gray.dtype == np.float32 or canonical_gray.dtype == np.float64:
        img_u8 = (canonical_gray * 255.0).clip(0, 255).astype(np.uint8)
    else:
        img_u8 = canonical_gray.astype(np.uint8)

    if palette == PaletteType.GRAYSCALE:
        return cv2.cvtColor(img_u8, cv2.COLOR_GRAY2BGR)

    lut = _LUT_CACHE.get(palette)
    if lut is None:
        lut = _LUT_CACHE[PaletteType.AMBER]

    return cv2.applyColorMap(img_u8, lut)


def get_available_palettes() -> List[Dict[str, str]]:
    """Returns list of registered display palettes."""
    return [
        {
            "id": PaletteType.GRAYSCALE.value,
            "name": "Scientific Grayscale",
            "description": "Unmodified single-channel acoustic backscatter intensity"
        },
        {
            "id": PaletteType.AMBER.value,
            "name": "ARIS Copper / Amber",
            "description": "Standard Sound Metrics ARIS 3000 high-visibility palette"
        },
        {
            "id": PaletteType.THERMAL.value,
            "name": "Monotonic Thermal",
            "description": "Luminance-preserving oceanographic thermal progression"
        },
        {
            "id": PaletteType.INFERNO.value,
            "name": "Inferno (Perceptual)",
            "description": "Colorblind-safe perceptually uniform acoustic mapping"
        },
    ]
