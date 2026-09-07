"""
Classical Acoustic Enhancement Methods for Forward-Looking Sonar (FLS).

All methods:
- Input: 2D float32 [0, 1] single-channel sonar image
- Output: EnhancementResult containing canonical 2D float32 [0, 1] image, method name,
          parameters dictionary, and high-resolution execution time (ms).
- Reproducible, zero GPU dependency, and deterministic execution.
"""

import time
import numpy as np
import cv2
from typing import Dict, Any, Optional, Tuple
from backend.enhancement.types import EnhancementMethod, EnhancementResult


def _ensure_float32_range(image: np.ndarray) -> np.ndarray:
    """Helper to ensure image is 2D float32 in [0, 1]."""
    if image.size == 0:
        return image.astype(np.float32)
    if image.ndim == 3 and image.shape[2] == 1:
        image = image.squeeze(axis=2)
    img = np.nan_to_num(image, nan=0.0, posinf=1.0, neginf=0.0).astype(np.float32)
    return np.clip(img, 0.0, 1.0)


def identity(image: np.ndarray, **kwargs) -> EnhancementResult:
    """
    Control baseline: Returns the input array unchanged.
    """
    t0 = time.perf_counter()
    res = _ensure_float32_range(image).copy()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=res,
        method=EnhancementMethod.IDENTITY,
        parameters={},
        execution_time_ms=round(dt_ms, 3)
    )


def percentile_normalize(
    image: np.ndarray,
    p_low: float = 2.0,
    p_high: float = 98.0,
    **kwargs
) -> EnhancementResult:
    """
    Percentile-based dynamic range stretch to remove extreme acoustic saturation outliers.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.PERCENTILE_NORM, parameters={"p_low": p_low, "p_high": p_high}, execution_time_ms=0.0)

    v_min = float(np.percentile(img, p_low))
    v_max = float(np.percentile(img, p_high))

    if v_max <= v_min:
        out = np.zeros_like(img)
    else:
        out = np.clip((img - v_min) / (v_max - v_min), 0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out.astype(np.float32),
        method=EnhancementMethod.PERCENTILE_NORM,
        parameters={"p_low": p_low, "p_high": p_high},
        execution_time_ms=round(dt_ms, 3)
    )


def gamma_correct(
    image: np.ndarray,
    gamma: float = 0.7,
    **kwargs
) -> EnhancementResult:
    """
    Power-law gamma contrast transformation.
    gamma < 1.0 brightens weak acoustic returns (acoustic shadow visibility).
    gamma > 1.0 increases contrast in high-intensity target highlights.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0 or gamma <= 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.GAMMA_CORRECT, parameters={"gamma": gamma}, execution_time_ms=0.0)

    out = np.power(img, gamma)
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out.astype(np.float32),
        method=EnhancementMethod.GAMMA_CORRECT,
        parameters={"gamma": gamma},
        execution_time_ms=round(dt_ms, 3)
    )


def clahe_enhance(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    **kwargs
) -> EnhancementResult:
    """
    Contrast Limited Adaptive Histogram Equalization (CLAHE).
    Matches the baseline used in ARIS 3000 acoustic processing.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.CLAHE, parameters={"clip_limit": clip_limit, "tile_grid_size": list(tile_grid_size)}, execution_time_ms=0.0)

    img_u8 = (img * 255.0).clip(0, 255).astype(np.uint8)
    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl1 = clahe_obj.apply(img_u8)
    out = (cl1.astype(np.float32) / 255.0).clip(0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out,
        method=EnhancementMethod.CLAHE,
        parameters={"clip_limit": clip_limit, "tile_grid_size": list(tile_grid_size)},
        execution_time_ms=round(dt_ms, 3)
    )


def median_clahe(
    image: np.ndarray,
    kernel_size: int = 3,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    **kwargs
) -> EnhancementResult:
    """
    Median speckle filtering followed by localized CLAHE equalization.
    Suppresses impulsive acoustic noise before contrast expansion.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.MEDIAN_CLAHE, parameters={"kernel_size": kernel_size, "clip_limit": clip_limit}, execution_time_ms=0.0)

    # Median blur in uint8 domain
    img_u8 = (img * 255.0).clip(0, 255).astype(np.uint8)
    k = kernel_size if kernel_size % 2 == 1 else kernel_size + 1
    denoised_u8 = cv2.medianBlur(img_u8, k)

    # Followed by CLAHE
    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_u8 = clahe_obj.apply(denoised_u8)
    out = (enhanced_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out,
        method=EnhancementMethod.MEDIAN_CLAHE,
        parameters={"kernel_size": k, "clip_limit": clip_limit, "tile_grid_size": list(tile_grid_size)},
        execution_time_ms=round(dt_ms, 3)
    )


def bilateral_clahe(
    image: np.ndarray,
    d: int = 5,
    sigma_color: float = 0.1,
    sigma_space: float = 3.0,
    clip_limit: float = 1.8,
    tile_grid_size: Tuple[int, int] = (8, 8),
    **kwargs
) -> EnhancementResult:
    """
    Bilateral edge-preserving smoothing followed by CLAHE.
    Smooths homogeneous acoustic reverberation while strictly retaining target boundary steps.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.BILATERAL_CLAHE, parameters={"d": d, "sigma_color": sigma_color, "clip_limit": clip_limit}, execution_time_ms=0.0)

    img_u8 = (img * 255.0).clip(0, 255).astype(np.uint8)
    # Scale sigma_color to uint8 range [0, 255]
    sig_c_u8 = sigma_color * 255.0
    denoised_u8 = cv2.bilateralFilter(img_u8, d=d, sigmaColor=sig_c_u8, sigmaSpace=sigma_space)

    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_u8 = clahe_obj.apply(denoised_u8)
    out = (enhanced_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out,
        method=EnhancementMethod.BILATERAL_CLAHE,
        parameters={
            "d": d,
            "sigma_color": sigma_color,
            "sigma_space": sigma_space,
            "clip_limit": clip_limit,
            "tile_grid_size": list(tile_grid_size)
        },
        execution_time_ms=round(dt_ms, 3)
    )


def unsharp_clahe(
    image: np.ndarray,
    sigma: float = 1.0,
    amount: float = 0.6,
    clip_limit: float = 2.0,
    tile_grid_size: Tuple[int, int] = (8, 8),
    **kwargs
) -> EnhancementResult:
    """
    High-boost Unsharp Masking combined with CLAHE.
    Sharpens acoustic highlight/shadow boundary transitions.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.UNSHARP_CLAHE, parameters={"amount": amount, "clip_limit": clip_limit}, execution_time_ms=0.0)

    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma, sigmaY=sigma)
    sharpened = np.clip(img + amount * (img - blurred), 0.0, 1.0)

    # Follow with CLAHE
    sharp_u8 = (sharpened * 255.0).clip(0, 255).astype(np.uint8)
    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_u8 = clahe_obj.apply(sharp_u8)
    out = (enhanced_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out,
        method=EnhancementMethod.UNSHARP_CLAHE,
        parameters={"sigma": sigma, "amount": amount, "clip_limit": clip_limit, "tile_grid_size": list(tile_grid_size)},
        execution_time_ms=round(dt_ms, 3)
    )


def log_bilateral_clahe(
    image: np.ndarray,
    d: int = 5,
    sigma_color: float = 0.15,
    sigma_space: float = 3.0,
    clip_limit: float = 1.6,
    tile_grid_size: Tuple[int, int] = (8, 8),
    **kwargs
) -> EnhancementResult:
    """
    Homomorphic Log-Bilateral Filtering followed by CLAHE.
    Transforms multiplicative acoustic speckle noise into additive Gaussian noise in the log domain,
    applies bilateral denoising, returns to linear intensity, and balances contrast with CLAHE.
    """
    t0 = time.perf_counter()
    img = _ensure_float32_range(image)
    if img.size == 0:
        return EnhancementResult(canonical_image=img, method=EnhancementMethod.LOG_BILATERAL_CLAHE, parameters={}, execution_time_ms=0.0)

    # 1. Homomorphic log transform (convert multiplicative noise to additive)
    eps = 1e-4
    log_img = np.log(img + eps)
    # Normalize log image to [0, 1]
    log_min, log_max = float(np.min(log_img)), float(np.max(log_img))
    if log_max > log_min:
        log_norm = (log_img - log_min) / (log_max - log_min)
    else:
        log_norm = np.zeros_like(img)

    # 2. Bilateral filter in log domain
    log_u8 = (log_norm * 255.0).clip(0, 255).astype(np.uint8)
    denoised_u8 = cv2.bilateralFilter(log_u8, d=d, sigmaColor=sigma_color * 255.0, sigmaSpace=sigma_space)

    # 3. Invert log normalization
    denoised_log = (denoised_u8.astype(np.float32) / 255.0) * (log_max - log_min) + log_min
    linear_img = np.clip(np.exp(denoised_log) - eps, 0.0, 1.0)

    # 4. CLAHE balancing
    linear_u8 = (linear_img * 255.0).clip(0, 255).astype(np.uint8)
    clahe_obj = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced_u8 = clahe_obj.apply(linear_u8)
    out = (enhanced_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)

    dt_ms = (time.perf_counter() - t0) * 1000.0
    return EnhancementResult(
        canonical_image=out,
        method=EnhancementMethod.LOG_BILATERAL_CLAHE,
        parameters={
            "d": d,
            "sigma_color": sigma_color,
            "sigma_space": sigma_space,
            "clip_limit": clip_limit,
            "tile_grid_size": list(tile_grid_size)
        },
        execution_time_ms=round(dt_ms, 3)
    )


# Registry of callable methods
ENHANCEMENT_METHODS = {
    EnhancementMethod.IDENTITY: identity,
    EnhancementMethod.PERCENTILE_NORM: percentile_normalize,
    EnhancementMethod.GAMMA_CORRECT: gamma_correct,
    EnhancementMethod.CLAHE: clahe_enhance,
    EnhancementMethod.MEDIAN_CLAHE: median_clahe,
    EnhancementMethod.BILATERAL_CLAHE: bilateral_clahe,
    EnhancementMethod.UNSHARP_CLAHE: unsharp_clahe,
    EnhancementMethod.LOG_BILATERAL_CLAHE: log_bilateral_clahe,
}


def apply_enhancement_method(
    method_name: str,
    image: np.ndarray,
    **kwargs
) -> EnhancementResult:
    """Dispatches to the requested enhancement method with parameter passing."""
    try:
        method_enum = EnhancementMethod(method_name)
    except ValueError:
        raise ValueError(f"Unknown enhancement method '{method_name}'. Valid options: {[m.value for m in EnhancementMethod]}")

    func = ENHANCEMENT_METHODS[method_enum]
    return func(image, **kwargs)
