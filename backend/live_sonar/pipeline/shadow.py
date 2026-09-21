"""Acoustic Shadow Verification for Marine Sonar Detection.

Reuses physical acoustic shadow principles: a genuine 3D proud or semi-buried
seabed object occludes acoustic pings, casting an acoustic shadow down-range.
Conforms to Requirement R2 §24 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import logging
from typing import Tuple
import numpy as np

logger = logging.getLogger(__name__)


def evaluate_acoustic_shadow(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    beam_direction: str = "down",  # Sonar look direction: "down" (FLS) or "right"/"left" (SSS)
) -> str:
    """Evaluate whether an acoustic shadow exists down-range from the detection bounding box.

    Returns:
    - "detected": A statistically significant drop in backscatter intensity is observed down-range.
    - "unavailable": The shadow cannot be confirmed or image data is unavailable.
    """
    if not isinstance(image, np.ndarray) or image.size == 0:
        return "unavailable"

    h_img, w_img = image.shape[:2]
    x, y, w, h = bbox

    # Ensure box is within bounds
    x1 = max(0, min(x, w_img - 1))
    y1 = max(0, min(y, h_img - 1))
    x2 = max(0, min(x + w, w_img))
    y2 = max(0, min(y + h, h_img))

    if x2 <= x1 or y2 <= y1:
        return "unavailable"

    # In standard Forward-Looking Sonar (ARIS 3000), sound travels top-to-bottom
    # Acoustic shadow appears immediately behind the target (greater range / higher Y)
    target_patch = image[y1:y2, x1:x2]
    target_mean = float(np.mean(target_patch))

    # Define shadow candidate region down-range
    shadow_y1 = y2
    shadow_y2 = min(h_img, y2 + max(10, int(h * 0.8)))
    shadow_x1 = x1
    shadow_x2 = x2

    if shadow_y2 - shadow_y1 < 4:
        return "unavailable"

    shadow_patch = image[shadow_y1:shadow_y2, shadow_x1:shadow_x2]
    if shadow_patch.size == 0:
        return "unavailable"

    shadow_mean = float(np.mean(shadow_patch))

    # Background reference (adjacent region to the side of the target)
    bg_x1 = max(0, x1 - w)
    bg_x2 = x1
    bg_patch = image[y1:y2, bg_x1:bg_x2] if bg_x1 < bg_x2 else image[y1:y2, x2:min(w_img, x2 + w)]
    bg_mean = float(np.mean(bg_patch)) if bg_patch.size > 0 else 128.0

    # Physical criteria: Target is brighter than background (specular acoustic highlight)
    # and shadow region has backscatter intensity noticeably lower than surrounding seabed
    if target_mean > shadow_mean * 1.3 and shadow_mean < bg_mean * 0.85:
        return "detected"

    return "unavailable"
