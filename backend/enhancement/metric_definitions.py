"""
Explicit Acoustic Metric Definitions and Deterministic ROI Generation.

This module provides mathematically documented, reproducible metrics for sonar image enhancement:
1. Equivalent Number of Looks (ENL) - on homogeneous background ROIs
2. Contrast-to-Noise Ratio (CNR) - on eroded target center vs surrounding background ring
3. Edge Preservation Index (EPI) - based on ratio of gradient energy with identity verification

NO METRIC FABRICATION:
If validity conditions or input assumptions fail, the functions return MetricStatus.NOT_MEASURABLE
or MetricStatus.INVALID with an explicit failure reason, NEVER an arbitrary or synthetic number.
"""

import numpy as np
import cv2
from typing import Tuple, Optional, List, Dict, Any
from backend.enhancement.types import MetricResult, MetricStatus


def extract_homogeneous_background_roi(
    image: np.ndarray,
    candidate_box: Optional[Tuple[int, int, int, int]] = None,
    min_area: int = 64
) -> Tuple[np.ndarray, MetricStatus, Optional[str]]:
    """
    Extracts a homogeneous background ROI from a 2D float32 [0, 1] sonar frame.
    
    If candidate_box is None, searches for the patch with lowest local variance
    (e.g., uniform water column or uniform sediment) away from extreme boundaries.
    
    Returns:
        (roi_pixels, status, failure_reason)
    """
    if image.size == 0 or image.ndim != 2:
        return np.array([]), MetricStatus.INVALID, "Image array is empty or non-2D"

    H, W = image.shape
    if H < 16 or W < 16:
        return np.array([]), MetricStatus.NOT_MEASURABLE, f"Image dimensions ({H}x{W}) too small for reliable ROI"

    if candidate_box is not None:
        x, y, w, h = candidate_box
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(W, x + w), min(H, y + h)
        roi = image[y1:y2, x1:x2]
        if roi.size < min_area:
            return np.array([]), MetricStatus.NOT_MEASURABLE, f"Specified ROI area ({roi.size}) below minimum ({min_area})"
        return roi.flatten(), MetricStatus.VALID, None

    # Automated search: Divide image into 32x32 blocks, search in lower or middle quadrants
    # avoiding acoustic edges
    block_size = 32
    if H < block_size or W < block_size:
        block_size = 16

    best_roi = None
    min_std = float("inf")

    # Sample non-overlapping blocks
    for r in range(0, H - block_size + 1, block_size):
        for c in range(0, W - block_size + 1, block_size):
            patch = image[r : r + block_size, c : c + block_size]
            # Exclude saturated or completely zero patches (dead acoustic pixels or water column mute)
            mean_val = np.mean(patch)
            if mean_val < 0.02 or mean_val > 0.98:
                continue
            std_val = np.std(patch)
            if 0 < std_val < min_std:
                min_std = std_val
                best_roi = patch

    if best_roi is None or best_roi.size < min_area:
        # Fallback to center 16x16 patch if valid
        cy, cx = H // 2, W // 2
        patch = image[max(0, cy - 8): min(H, cy + 8), max(0, cx - 8): min(W, cx + 8)]
        if patch.size >= min_area and np.std(patch) > 0:
            return patch.flatten(), MetricStatus.VALID, None
        return np.array([]), MetricStatus.NOT_MEASURABLE, "No non-degenerate homogeneous background ROI found"

    return best_roi.flatten(), MetricStatus.VALID, None


def compute_enl(
    image: np.ndarray,
    roi: Optional[np.ndarray] = None,
    candidate_box: Optional[Tuple[int, int, int, int]] = None
) -> MetricResult:
    """
    Computes the Equivalent Number of Looks (ENL).
    
    Formula:
        ENL = (mu_ROI^2) / (sigma_ROI^2)
        
    Assumptions & ROI Requirements:
        - Must be evaluated on a homogeneous background ROI (water column or flat seabed).
        - Full-image ENL is invalid because structural edges corrupt variance.
        
    Validity Conditions:
        - ROI must contain at least 64 pixels.
        - sigma_ROI > 0 (non-constant).
        - mu_ROI > 0.
        
    Interpretation:
        Higher ENL indicates smoother background and lower speckle variance.
        
    Reference:
        Oliver, C., & Quegan, S. (2004). Understanding Synthetic Aperture Radar Images.
    """
    formula_str = "ENL = (mu_ROI^2) / (sigma_ROI^2) on homogeneous background"
    
    if roi is None:
        roi_pixels, status, reason = extract_homogeneous_background_roi(image, candidate_box=candidate_box)
        if status != MetricStatus.VALID:
            return MetricResult(
                name="ENL",
                value=None,
                status=status,
                unit="looks",
                formula=formula_str,
                failure_reason=reason
            )
    else:
        roi_pixels = roi.flatten()

    if roi_pixels.size < 64:
        return MetricResult(
            name="ENL",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="looks",
            formula=formula_str,
            failure_reason=f"ROI pixel count ({roi_pixels.size}) < 64"
        )

    mu = float(np.mean(roi_pixels))
    sigma = float(np.std(roi_pixels))

    if sigma <= 1e-7:
        return MetricResult(
            name="ENL",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="looks",
            formula=formula_str,
            failure_reason="ROI variance is zero (constant region)"
        )

    if mu <= 1e-7:
        return MetricResult(
            name="ENL",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="looks",
            formula=formula_str,
            failure_reason="ROI mean intensity is zero (pure acoustic shadow/mute)"
        )

    enl_val = float((mu ** 2) / (sigma ** 2))
    return MetricResult(
        name="ENL",
        value=round(enl_val, 4),
        status=MetricStatus.VALID,
        unit="looks",
        formula=formula_str,
        metadata={"roi_pixels": roi_pixels.size, "mu": round(mu, 4), "sigma": round(sigma, 4)}
    )


def derive_target_and_background_rois(
    image: np.ndarray,
    bbox_xywh_norm: Tuple[float, float, float, float],
    erosion_margin: float = 0.30,
    ring_expansion: float = 0.60,
    min_pixels: int = 16
) -> Tuple[np.ndarray, np.ndarray, MetricStatus, Optional[str]]:
    """
    Deterministically derives Target ROI and Background Ring ROI from a normalized bounding box.
    
    Geometry:
        - Target ROI: Center-eroded region of the bounding box (shrink box by erosion_margin).
        - Background Ring: Expanded box (by ring_expansion) excluding the original target box.
        
    Returns:
        (target_pixels, background_pixels, status, reason)
    """
    if image.size == 0 or image.ndim != 2:
        return np.array([]), np.array([]), MetricStatus.INVALID, "Image is empty or non-2D"

    H, W = image.shape
    cx_norm, cy_norm, w_norm, h_norm = bbox_xywh_norm

    cx, cy = cx_norm * W, cy_norm * H
    bw, bh = w_norm * W, h_norm * H

    # 1. Target Box
    bx1 = int(round(cx - bw / 2.0))
    by1 = int(round(cy - bh / 2.0))
    bx2 = int(round(cx + bw / 2.0))
    by2 = int(round(cy + bh / 2.0))

    bx1, by1 = max(0, bx1), max(0, by1)
    bx2, by2 = min(W, bx2), min(H, by2)

    box_w = bx2 - bx1
    box_h = by2 - by1

    if box_w < 4 or box_h < 4:
        return np.array([]), np.array([]), MetricStatus.NOT_MEASURABLE, f"Bounding box too small ({box_w}x{box_h})"

    # 2. Eroded Target ROI
    pad_x = int(round(box_w * erosion_margin))
    pad_y = int(round(box_h * erosion_margin))

    tx1 = min(bx2 - 1, bx1 + pad_x)
    ty1 = min(by2 - 1, by1 + pad_y)
    tx2 = max(tx1 + 1, bx2 - pad_x)
    ty2 = max(ty1 + 1, by2 - pad_y)

    target_patch = image[ty1:ty2, tx1:tx2]
    if target_patch.size < min_pixels:
        # Fallback to full box if eroded is too small
        target_patch = image[by1:by2, bx1:bx2]
        if target_patch.size < min_pixels:
            return np.array([]), np.array([]), MetricStatus.NOT_MEASURABLE, f"Target ROI size ({target_patch.size}) < {min_pixels}"

    # 3. Background Ring ROI
    rx1 = max(0, int(round(bx1 - box_w * ring_expansion)))
    ry1 = max(0, int(round(by1 - box_h * ring_expansion)))
    rx2 = min(W, int(round(bx2 + box_w * ring_expansion)))
    ry2 = min(H, int(round(by2 + box_h * ring_expansion)))

    # Mask out the original bounding box area from the expanded region
    outer_region = image[ry1:ry2, rx1:rx2].copy()
    mask = np.ones_like(outer_region, dtype=bool)

    # Coordinates of target box within the expanded window
    inner_y1 = max(0, by1 - ry1)
    inner_y2 = min(outer_region.shape[0], by2 - ry1)
    inner_x1 = max(0, bx1 - rx1)
    inner_x2 = min(outer_region.shape[1], bx2 - rx1)

    mask[inner_y1:inner_y2, inner_x1:inner_x2] = False
    background_pixels = outer_region[mask]

    if background_pixels.size < min_pixels:
        return np.array([]), np.array([]), MetricStatus.NOT_MEASURABLE, f"Background ring size ({background_pixels.size}) < {min_pixels}"

    return target_patch.flatten(), background_pixels.flatten(), MetricStatus.VALID, None


def compute_cnr(
    image: np.ndarray,
    target_pixels: Optional[np.ndarray] = None,
    background_pixels: Optional[np.ndarray] = None,
    bbox_xywh_norm: Optional[Tuple[float, float, float, float]] = None
) -> MetricResult:
    """
    Computes Contrast-to-Noise Ratio (CNR).
    
    Formula:
        CNR = |mu_target - mu_background| / sqrt(sigma_target^2 + sigma_background^2)
        
    Assumptions & ROI Requirements:
        - Target pixels from eroded object interior.
        - Background pixels from surrounding annular ring.
        
    Validity Conditions:
        - Both target and background pixel sets >= 16 pixels.
        - Pooled variance (sigma_t^2 + sigma_b^2) > 0.
        
    Interpretation:
        Higher CNR indicates acoustic debris targets stand out more prominently above seabed/reverberation noise.
    """
    formula_str = "CNR = |mu_tgt - mu_bg| / sqrt(sigma_tgt^2 + sigma_bg^2)"

    if target_pixels is None or background_pixels is None:
        if bbox_xywh_norm is None:
            return MetricResult(
                name="CNR",
                value=None,
                status=MetricStatus.NOT_MEASURABLE,
                unit="ratio",
                formula=formula_str,
                failure_reason="No bounding box or ROI pixels provided"
            )
        target_pixels, background_pixels, status, reason = derive_target_and_background_rois(image, bbox_xywh_norm)
        if status != MetricStatus.VALID:
            return MetricResult(
                name="CNR",
                value=None,
                status=status,
                unit="ratio",
                formula=formula_str,
                failure_reason=reason
            )

    if target_pixels.size < 16 or background_pixels.size < 16:
        return MetricResult(
            name="CNR",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="ratio",
            formula=formula_str,
            failure_reason="Target or background pixel count < 16"
        )

    mu_t = float(np.mean(target_pixels))
    mu_b = float(np.mean(background_pixels))
    sig_t = float(np.std(target_pixels))
    sig_b = float(np.std(background_pixels))

    denom = np.sqrt(sig_t ** 2 + sig_b ** 2)
    if denom <= 1e-7:
        return MetricResult(
            name="CNR",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="ratio",
            formula=formula_str,
            failure_reason="Denominator variance is zero"
        )

    cnr_val = float(abs(mu_t - mu_b) / denom)
    return MetricResult(
        name="CNR",
        value=round(cnr_val, 4),
        status=MetricStatus.VALID,
        unit="ratio",
        formula=formula_str,
        metadata={
            "mu_target": round(mu_t, 4),
            "mu_background": round(mu_b, 4),
            "sigma_target": round(sig_t, 4),
            "sigma_background": round(sig_b, 4)
        }
    )


def compute_epi(
    original: np.ndarray,
    enhanced: np.ndarray,
    roi_mask: Optional[np.ndarray] = None
) -> MetricResult:
    """
    Computes Edge Preservation Index (EPI).
    
    Formula (Normalized High-Pass Laplacian Energy Ratio):
        EPI = sum(|Laplacian(I_enhanced)|) / sum(|Laplacian(I_original)|)
        
    Identity Property:
        EPI(original, original) == 1.00000 (mathematically guaranteed).
        
    Interpretation:
        EPI ~ 1.0: Target boundaries preserved without blurring.
        EPI >> 1.0: High-frequency noise amplification or ringing artifacts.
        EPI << 1.0: Severe edge blurring / loss of acoustic shadow contours.
        
    Reference:
        Sattar, F., et al. (1997). Image enhancement based on a nonlinear multiscale method.
        IEEE Transactions on Image Processing.
    """
    formula_str = "EPI = sum(|Laplacian(I_enh)|) / sum(|Laplacian(I_orig)|)"

    if original.size == 0 or enhanced.size == 0:
        return MetricResult(
            name="EPI",
            value=None,
            status=MetricStatus.INVALID,
            unit="ratio",
            formula=formula_str,
            failure_reason="Original or enhanced image array is empty"
        )

    if original.shape != enhanced.shape:
        return MetricResult(
            name="EPI",
            value=None,
            status=MetricStatus.INVALID,
            unit="ratio",
            formula=formula_str,
            failure_reason=f"Shape mismatch: {original.shape} vs {enhanced.shape}"
        )

    # Compute standard 3x3 discrete 2D Laplacian operator
    orig_f = original.astype(np.float32)
    enh_f = enhanced.astype(np.float32)

    lap_kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)
    lap_orig = np.abs(cv2.filter2D(orig_f, -1, lap_kernel))
    lap_enh = np.abs(cv2.filter2D(enh_f, -1, lap_kernel))

    if roi_mask is not None and roi_mask.shape == original.shape:
        lap_orig = lap_orig[roi_mask]
        lap_enh = lap_enh[roi_mask]

    sum_orig = float(np.sum(lap_orig))
    sum_enh = float(np.sum(lap_enh))

    if sum_orig <= 1e-7:
        return MetricResult(
            name="EPI",
            value=None,
            status=MetricStatus.NOT_MEASURABLE,
            unit="ratio",
            formula=formula_str,
            failure_reason="Original image has zero Laplacian gradient energy (flat constant)"
        )

    epi_val = float(sum_enh / sum_orig)
    return MetricResult(
        name="EPI",
        value=round(epi_val, 4),
        status=MetricStatus.VALID,
        unit="ratio",
        formula=formula_str,
        metadata={"laplacian_sum_orig": round(sum_orig, 4), "laplacian_sum_enh": round(sum_enh, 4)}
    )
