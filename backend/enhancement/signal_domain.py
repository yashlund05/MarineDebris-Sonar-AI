"""
Mathematical signal-domain transformations for acoustic sonar imagery.

Implements Requirement R7:
- Explicit conversion functions (amplitude to dB, power to dB, dB to linear power)
- Mathematical invariants: epsilon guarding, bounded clipping, dynamic range estimation
- Double-logarithmic conversion prevention.
"""

from __future__ import annotations

import numpy as np
from typing import Tuple, Dict, Any, Optional

from backend.enhancement.pipeline_base import SignalRepresentation


def amplitude_to_db(
    image: np.ndarray,
    ref: float = 1.0,
    eps: float = 1e-7,
    clip_min_db: float = -60.0,
    clip_max_db: float = 0.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Converts linear acoustic amplitude array to decibels (dB):
    dB = 20 * log10(max(amplitude, eps) / ref)

    Returns:
        (db_image, audit_dict)
    """
    if not isinstance(image, np.ndarray):
        raise TypeError("Input must be a numpy ndarray")

    # Safety check: Detect if already in decibels (negative values with wide range)
    min_val = float(np.min(image)) if image.size > 0 else 0.0
    if min_val < -10.0:
        return image.astype(np.float32), {
            "warning": "Image appears to already be in dB scale; logarithmic conversion skipped to prevent distortion.",
            "skipped": True,
        }

    clamped = np.maximum(image.astype(np.float32), eps)
    db = 20.0 * np.log10(clamped / max(ref, eps))
    clipped = np.clip(db, clip_min_db, clip_max_db)

    # Normalize mapped dB range to canonical float32 [0.0, 1.0]
    mapped = (clipped - clip_min_db) / (clip_max_db - clip_min_db)

    audit = {
        "formula": "20 * log10(amp / ref)",
        "ref": ref,
        "eps": eps,
        "clip_min_db": clip_min_db,
        "clip_max_db": clip_max_db,
        "input_min": min_val,
        "output_range": [float(np.min(mapped)), float(np.max(mapped))],
    }
    return mapped.astype(np.float32), audit


def power_to_db(
    image: np.ndarray,
    ref: float = 1.0,
    eps: float = 1e-7,
    clip_min_db: float = -60.0,
    clip_max_db: float = 0.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Converts acoustic power / intensity array to decibels (dB):
    dB = 10 * log10(max(power, eps) / ref)
    """
    min_val = float(np.min(image)) if image.size > 0 else 0.0
    if min_val < -10.0:
        return image.astype(np.float32), {
            "warning": "Image appears to already be in dB scale; skipped.",
            "skipped": True,
        }

    clamped = np.maximum(image.astype(np.float32), eps)
    db = 10.0 * np.log10(clamped / max(ref, eps))
    clipped = np.clip(db, clip_min_db, clip_max_db)
    mapped = (clipped - clip_min_db) / (clip_max_db - clip_min_db)

    audit = {
        "formula": "10 * log10(power / ref)",
        "ref": ref,
        "eps": eps,
        "clip_min_db": clip_min_db,
        "clip_max_db": clip_max_db,
        "input_min": min_val,
        "output_range": [float(np.min(mapped)), float(np.max(mapped))],
    }
    return mapped.astype(np.float32), audit


def db_to_linear_power(
    db_image: np.ndarray,
    ref: float = 1.0,
    clip_min_db: float = -60.0,
    clip_max_db: float = 0.0,
) -> np.ndarray:
    """
    Inverts normalized dB representation back to linear power:
    power = ref * 10^(dB / 10)
    """
    # Denormalize [0, 1] back to [clip_min_db, clip_max_db]
    db_actual = db_image * (clip_max_db - clip_min_db) + clip_min_db
    power = ref * np.power(10.0, db_actual / 10.0)
    return power.astype(np.float32)


def safe_percentile_normalization(
    image: np.ndarray,
    p_low: float = 1.0,
    p_high: float = 99.0,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Robust percentile normalization avoiding outliers while preserving relative acoustic contrast.
    """
    if image.size == 0:
        return image.astype(np.float32), {"p_low": p_low, "p_high": p_high}

    finite_mask = np.isfinite(image)
    if not finite_mask.any():
        return np.zeros_like(image, dtype=np.float32), {"error": "no_finite_pixels"}

    clean_vals = image[finite_mask]
    v_low = float(np.percentile(clean_vals, p_low))
    v_high = float(np.percentile(clean_vals, p_high))

    if v_high <= v_low + 1e-7:
        normalized = np.zeros_like(image, dtype=np.float32)
    else:
        normalized = np.clip((image - v_low) / (v_high - v_low), 0.0, 1.0).astype(np.float32)

    return normalized, {
        "p_low": p_low,
        "p_high": p_high,
        "v_low": v_low,
        "v_high": v_high,
    }


def robust_dynamic_range_estimation(image: np.ndarray) -> float:
    """
    Estimates effective dynamic range in decibels (dB) via 1st and 99th percentiles.
    """
    finite_mask = np.isfinite(image)
    if not finite_mask.any():
        return 0.0
    vals = image[finite_mask]
    p01 = float(np.percentile(vals, 1))
    p99 = float(np.percentile(vals, 99))
    if p01 <= 0:
        p01 = max(float(np.min(vals[vals > 0])) if (vals > 0).any() else 1e-4, 1e-4)
    if p99 <= p01:
        return 0.0
    return float(20.0 * np.log10(p99 / p01))
