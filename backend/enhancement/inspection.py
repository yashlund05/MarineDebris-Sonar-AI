"""
Robust input inspection and modality detection for sonar imagery.

Implements Requirement R6:
- FLS vs SSS detection
- Signal representation validation (amplitude, intensity, dB, normalized float, display)
- Saturation, dead pixel, dropout, and dynamic range auditing
- Explicit forensic reporting; avoids silent guessing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import numpy as np

from backend.enhancement.pipeline_base import Modality, SignalRepresentation


@dataclass
class SonarInspectionReport:
    """Comprehensive inspection diagnosis of raw sonar input."""
    shape: List[int]
    dtype: str
    channels: int
    modality: Modality
    detected_representation: SignalRepresentation
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    dynamic_range_db: float
    nan_count: int
    inf_count: int
    zero_pixel_ratio: float
    saturated_pixel_ratio: float
    dead_column_count: int
    is_normalized: bool
    is_valid_float32: bool
    metadata_available: bool
    sonar_frequency_hz: Optional[float] = None
    range_resolution_m: Optional[float] = None
    gain_db: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    risk_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "shape": self.shape,
            "dtype": self.dtype,
            "channels": self.channels,
            "modality": self.modality.value,
            "detected_representation": self.detected_representation.value,
            "min_value": round(self.min_value, 4),
            "max_value": round(self.max_value, 4),
            "mean_value": round(self.mean_value, 4),
            "std_value": round(self.std_value, 4),
            "dynamic_range_db": round(self.dynamic_range_db, 2),
            "nan_count": self.nan_count,
            "inf_count": self.inf_count,
            "zero_pixel_ratio": round(self.zero_pixel_ratio, 4),
            "saturated_pixel_ratio": round(self.saturated_pixel_ratio, 4),
            "dead_column_count": self.dead_column_count,
            "is_normalized": self.is_normalized,
            "is_valid_float32": self.is_valid_float32,
            "metadata_available": self.metadata_available,
            "sonar_frequency_hz": self.sonar_frequency_hz,
            "range_resolution_m": self.range_resolution_m,
            "gain_db": self.gain_db,
            "warnings": self.warnings,
            "risk_flags": self.risk_flags,
        }


def inspect_sonar_input(
    data: np.ndarray, metadata: Optional[Dict[str, Any]] = None
) -> SonarInspectionReport:
    """
    Inspects input numpy array and metadata.
    Avoids silent assumptions and records forensic warnings.
    """
    warnings: List[str] = []
    risk_flags: List[str] = []
    meta = metadata or {}

    if not isinstance(data, np.ndarray):
        raise TypeError(f"Expected numpy.ndarray, got {type(data)}")

    shape = list(data.shape)
    channels = 1
    if data.ndim == 3:
        channels = shape[2]
        if channels == 3:
            warnings.append("Input array has 3 channels; sonar data is canonically single-channel.")
        elif channels != 1:
            risk_flags.append(f"Unexpected channel count: {channels}")

    # Check finite numbers
    nan_count = int(np.isnan(data).sum())
    inf_count = int(np.isinf(data).sum())
    if nan_count > 0:
        warnings.append(f"Detected {nan_count} NaN values in raw input.")
        risk_flags.append("NAN_VALUES_PRESENT")
    if inf_count > 0:
        warnings.append(f"Detected {inf_count} infinite values in raw input.")
        risk_flags.append("INF_VALUES_PRESENT")

    finite_mask = np.isfinite(data)
    if finite_mask.any():
        valid_vals = data[finite_mask]
        min_val = float(np.min(valid_vals))
        max_val = float(np.max(valid_vals))
        mean_val = float(np.mean(valid_vals))
        std_val = float(np.std(valid_vals))
    else:
        min_val, max_val, mean_val, std_val = 0.0, 0.0, 0.0, 0.0
        risk_flags.append("NO_FINITE_PIXELS")

    total_pixels = max(1, data.size)
    zero_count = int((data == 0).sum())
    zero_ratio = float(zero_count / total_pixels)

    # Detect representation
    is_norm = False
    is_float32 = (data.dtype == np.float32)
    rep = SignalRepresentation.UNKNOWN

    if np.issubdtype(data.dtype, np.floating):
        if min_val >= -1e-4 and max_val <= 1.0 + 1e-4:
            is_norm = True
            rep = SignalRepresentation.NORMALIZED_FLOAT
        elif min_val < 0:
            rep = SignalRepresentation.DECIBEL
            warnings.append("Negative minimum detected: Input appears to be in logarithmic/dB scale.")
        else:
            rep = SignalRepresentation.LINEAR_AMPLITUDE
    elif np.issubdtype(data.dtype, np.integer):
        if data.dtype == np.uint8:
            rep = SignalRepresentation.DISPLAY_GRAYSCALE
        else:
            rep = SignalRepresentation.LINEAR_AMPLITUDE

    # Saturation estimation
    if rep == SignalRepresentation.DISPLAY_GRAYSCALE:
        sat_count = int((data >= 254).sum())
    elif is_norm:
        sat_count = int((data >= 0.999).sum())
    else:
        sat_count = int((data >= (max_val - 1e-5)).sum()) if max_val > min_val else 0
    sat_ratio = float(sat_count / total_pixels)

    if sat_ratio > 0.05:
        warnings.append(f"High acoustic saturation: {sat_ratio*100:.1f}% of pixels are at maximum dynamic limit.")
        risk_flags.append("ACOUSTIC_CLIPPING")

    # Dead column detection (common in sensor dropouts)
    dead_cols = 0
    if data.ndim >= 2:
        img_2d = data if data.ndim == 2 else data[:, :, 0]
        col_stds = np.std(img_2d, axis=0)
        dead_cols = int(np.sum(col_stds < 1e-7))
        if dead_cols > 2:
            warnings.append(f"Detected {dead_cols} dead or constant sensor columns.")
            risk_flags.append("SENSOR_DROPOUT")

    # Dynamic range estimate (in dB proxy)
    if min_val > 0 and max_val > min_val:
        dr_db = float(20.0 * np.log10(max_val / max(min_val, 1e-6)))
    elif is_norm and max_val > 0:
        p99 = float(np.percentile(valid_vals, 99)) if finite_mask.any() else 1.0
        p01 = float(np.percentile(valid_vals, 1)) if finite_mask.any() else 0.01
        dr_db = float(20.0 * np.log10(max(p99, 1e-4) / max(p01, 1e-4)))
    else:
        dr_db = 0.0

    # Modality detection
    modality = Modality.UNKNOWN
    if "modality" in meta:
        m_str = str(meta["modality"]).upper()
        if "FLS" in m_str or "FORWARD" in m_str or "ARIS" in m_str:
            modality = Modality.FLS
        elif "SSS" in m_str or "SIDE" in m_str or "EDGETECH" in m_str:
            modality = Modality.SSS

    if modality == Modality.UNKNOWN:
        # Heuristic from geometry
        h, w = shape[0], shape[1]
        aspect = w / max(h, 1)
        if 0.7 <= aspect <= 1.4:
            # FLS cameras typically capture square or 4:3 fan views
            modality = Modality.FLS
        elif aspect > 2.5 or aspect < 0.4:
            # SSS surveys typically form long across-track or along-track waterfall ribbons
            modality = Modality.SSS
        else:
            modality = Modality.UNKNOWN
            warnings.append("Modality ambiguous from geometry alone; tagged as UNKNOWN.")

    meta_avail = bool(meta.get("frequency_hz") or meta.get("range_m") or meta.get("gain_db"))

    return SonarInspectionReport(
        shape=shape,
        dtype=str(data.dtype),
        channels=channels,
        modality=modality,
        detected_representation=rep,
        min_value=min_val,
        max_value=max_val,
        mean_value=mean_val,
        std_value=std_val,
        dynamic_range_db=dr_db,
        nan_count=nan_count,
        inf_count=inf_count,
        zero_pixel_ratio=zero_ratio,
        saturated_pixel_ratio=sat_ratio,
        dead_column_count=dead_cols,
        is_normalized=is_norm,
        is_valid_float32=is_float32,
        metadata_available=meta_avail,
        sonar_frequency_hz=meta.get("frequency_hz"),
        range_resolution_m=meta.get("range_resolution_m"),
        gain_db=meta.get("gain_db"),
        warnings=warnings,
        risk_flags=risk_flags,
    )
