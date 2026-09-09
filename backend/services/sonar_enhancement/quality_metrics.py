"""
Acoustic Image Quality Metrics (Non-Reference and Comparative Diagnostics).
Calculates scientifically meaningful statistics across raw and enhanced representations.
"""

from typing import Dict, Any, Optional
import numpy as np
import cv2


def compute_brenner_gradient(image_f: np.ndarray) -> float:
    """Computes Brenner's gradient focus/sharpness metric (sum of squared differences of 2nd pixel distance)."""
    h, w = image_f.shape
    if h < 3 or w < 3:
        return 0.0
    diff = (image_f[:, 2:] - image_f[:, :-2]) ** 2
    return float(np.mean(diff))


def compute_tenengrad(image_f: np.ndarray) -> float:
    """Computes Tenengrad gradient metric using Sobel operators."""
    gx = cv2.Sobel(image_f, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(image_f, cv2.CV_32F, 0, 1, ksize=3)
    mag_sq = gx ** 2 + gy ** 2
    return float(np.mean(mag_sq))


def compute_acoustic_quality_metrics(image: np.ndarray, is_raw: bool = False) -> Dict[str, Any]:
    """
    Computes non-reference statistical quality metrics on a 2D grayscale array [0, 1] or uint8 [0, 255].
    """
    if image is None or image.size == 0:
        return {
            "mean_intensity": 0.0,
            "std_intensity": 0.0,
            "dynamic_range": 0.0,
            "rms_contrast": 0.0,
            "entropy": 0.0,
            "edge_density": 0.0,
            "brenner_gradient": 0.0,
            "tenengrad": 0.0,
            "enl_diagnostic": None,
        }

    # Ensure 2D float in [0, 1]
    if image.ndim == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    img_f = image.astype(np.float32)
    if img_f.max() > 1.0:
        img_f = img_f / 255.0
    img_f = np.clip(img_f, 0.0, 1.0)

    # 1. Intensity statistics
    mean_val = float(np.mean(img_f))
    std_val = float(np.std(img_f))

    # 2. Dynamic range (1st to 99th percentile to exclude dead pixels/outliers)
    p1 = float(np.percentile(img_f, 1))
    p99 = float(np.percentile(img_f, 99))
    dynamic_range = round(p99 - p1, 4)

    # 3. RMS Contrast
    rms_contrast = round(std_val, 4)

    # 4. Shannon Entropy (bits per pixel on 256 bins)
    img_u8 = (img_f * 255.0).astype(np.uint8)
    hist, _ = np.histogram(img_u8, bins=256, range=(0, 256), density=True)
    hist = hist[hist > 0]
    entropy = float(-np.sum(hist * np.log2(hist))) if len(hist) > 0 else 0.0

    # 5. Edge Density via Sobel gradients
    sobelx = cv2.Sobel(img_f, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(img_f, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = np.sqrt(sobelx ** 2 + sobely ** 2)
    edge_thresh = 0.15
    edge_density = float(np.mean(magnitude > edge_thresh))

    # 6. Sharpness metrics
    brenner = compute_brenner_gradient(img_f)
    tenengrad = compute_tenengrad(img_f)

    # 7. ENL Diagnostic (Equivalent Number of Looks)
    enl = None
    h, w = img_f.shape
    if h >= 32 and w >= 32:
        step = 16
        enls = []
        for y in range(0, h - 32, step):
            for x in range(0, w - 32, step):
                win = img_f[y:y+32, x:x+32]
                m = float(np.mean(win))
                s = float(np.std(win))
                if m > 0.1 and s > 0.01:
                    cov = s / m
                    if cov < 0.35:
                        enls.append((m ** 2) / (s ** 2))
        if enls:
            enl = round(float(np.median(enls)), 2)

    return {
        "mean_intensity": round(mean_val, 4),
        "std_intensity": round(std_val, 4),
        "dynamic_range": dynamic_range,
        "rms_contrast": rms_contrast,
        "entropy": round(entropy, 4),
        "edge_density": round(edge_density, 4),
        "brenner_gradient": round(brenner, 6),
        "tenengrad": round(tenengrad, 6),
        "enl_diagnostic": enl,
    }


def compute_comparative_quality_metrics(raw_image: np.ndarray, enhanced_image: np.ndarray) -> Dict[str, Any]:
    """Computes individual and delta comparative quality metrics across raw and enhanced frames."""
    raw_m = compute_acoustic_quality_metrics(raw_image, is_raw=True)
    enh_m = compute_acoustic_quality_metrics(enhanced_image, is_raw=False)

    contrast_gain = round(enh_m["rms_contrast"] - raw_m["rms_contrast"], 4)
    entropy_delta = round(enh_m["entropy"] - raw_m["entropy"], 4)
    dynamic_range_gain = round(enh_m["dynamic_range"] - raw_m["dynamic_range"], 4)

    raw_tenengrad = max(raw_m["tenengrad"], 1e-6)
    sharpness_ratio = round(enh_m["tenengrad"] / raw_tenengrad, 2)

    return {
        "raw": raw_m,
        "enhanced": enh_m,
        "delta": {
            "contrast_gain": contrast_gain,
            "entropy_delta": entropy_delta,
            "dynamic_range_gain": dynamic_range_gain,
            "sharpness_ratio": sharpness_ratio,
        },
    }
