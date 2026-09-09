"""
Image Export and Colormap Rendering for Sonar Enhancement.
Provides display-only false-color visualization and PNG encoding.
Strictly separated from acoustic signal processing.
"""

import base64
from io import BytesIO
from pathlib import Path
from typing import Union, Tuple, Optional
import cv2
import numpy as np

from .config import ColormapName


def create_amber_palette() -> np.ndarray:
    """
    Creates a specialized 256-color oceanographic Amber/Copper lookup table.
    Ramps smoothly from deep acoustic shadow (black) -> deep bronze -> warm amber -> bright yellow-white.
    Standard display standard for high-resolution imaging sonar (ARIS / DIDSON).
    """
    lut = np.zeros((256, 1, 3), dtype=np.uint8)
    for i in range(256):
        norm = i / 255.0
        if norm < 0.35:
            # Shadow to deep bronze (B, G, R)
            t = norm / 0.35
            b = 0
            g = int(30 * t)
            r = int(90 * t)
        elif norm < 0.75:
            # Bronze to vivid amber
            t = (norm - 0.35) / 0.40
            b = int(20 * t)
            g = int(30 + 130 * t)
            r = int(90 + 150 * t)
        else:
            # Amber to high-intensity highlight (warm yellow-white)
            t = (norm - 0.75) / 0.25
            b = int(20 + 180 * t)
            g = int(160 + 95 * t)
            r = 255
        lut[i, 0] = [b, g, r]
    return lut


# Cache amber LUT
_AMBER_LUT = create_amber_palette()


def apply_sonar_colormap(
    gray_u8: np.ndarray,
    colormap: Union[ColormapName, str] = ColormapName.AMBER,
) -> np.ndarray:
    """
    Applies display-only pseudocolor mapping to an 8-bit grayscale acoustic array.
    Returns 3-channel BGR uint8 array suitable for display or PNG encoding.
    
    CRITICAL: Output is strictly presentation-only and must NEVER be passed to ML models.
    """
    if gray_u8.ndim == 3:
        if gray_u8.shape[2] == 1:
            gray_u8 = gray_u8.squeeze(2)
        elif gray_u8.shape[2] == 3:
            gray_u8 = cv2.cvtColor(gray_u8, cv2.COLOR_BGR2GRAY)

    if gray_u8.dtype != np.uint8:
        gray_u8 = np.clip(gray_u8, 0, 255).astype(np.uint8)

    cmap_str = colormap.value if isinstance(colormap, ColormapName) else str(colormap).lower()

    if cmap_str == ColormapName.GRAYSCALE.value:
        return cv2.cvtColor(gray_u8, cv2.COLOR_GRAY2BGR)
    elif cmap_str == ColormapName.AMBER.value:
        return cv2.applyColorMap(gray_u8, _AMBER_LUT)
    elif cmap_str == ColormapName.VIRIDIS.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_VIRIDIS)
    elif cmap_str == ColormapName.INFERNO.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_INFERNO)
    elif cmap_str == ColormapName.MAGMA.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_MAGMA)
    elif cmap_str == ColormapName.PLASMA.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_PLASMA)
    elif cmap_str == ColormapName.TURBO.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_TURBO)
    elif cmap_str == ColormapName.COPPER.value:
        return cv2.applyColorMap(gray_u8, cv2.COLORMAP_COPPER)
    else:
        # Default fallback to Amber
        return cv2.applyColorMap(gray_u8, _AMBER_LUT)


def encode_to_png_bytes(image: np.ndarray) -> bytes:
    """Encodes 2D grayscale or 3D BGR image to PNG byte buffer."""
    success, buffer = cv2.imencode(".png", image, [cv2.IMWRITE_PNG_COMPRESSION, 4])
    if not success:
        raise ValueError("Failed to encode image to PNG format")
    return buffer.tobytes()


def encode_to_base64_data_url(image: np.ndarray) -> str:
    """Encodes image array to a data:image/png;base64,... URI."""
    png_bytes = encode_to_png_bytes(image)
    b64_str = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64_str}"


def save_png(image: np.ndarray, file_path: Union[str, Path]) -> Path:
    """Writes image array to PNG file on disk."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    png_bytes = encode_to_png_bytes(image)
    path.write_bytes(png_bytes)
    return path
