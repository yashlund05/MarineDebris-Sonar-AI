"""
Input validation, format detection, and acoustic representation analysis.
"""

import os
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np


SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
SUPPORTED_RAW_EXTENSIONS = {".xtf", ".jsf"}
ALL_SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_RAW_EXTENSIONS


class RepresentationType(str, Enum):
    RENDERED_GRAYSCALE = "rendered_grayscale"
    RAW_ACOUSTIC_LINEAR = "raw_acoustic_linear"
    NORMALIZED_FLOAT = "normalized_float"
    UNKNOWN = "unknown"


@dataclass
class InputRepresentation:
    representation_type: RepresentationType
    shape: Tuple[int, ...]
    dtype: str
    min_val: float
    max_val: float
    db_conversion_applicable: bool
    audit_note: str
    metadata_available: bool


def detect_file_format(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext in SUPPORTED_IMAGE_EXTENSIONS:
        return "rendered_image"
    elif ext == ".xtf":
        return "xtf"
    elif ext == ".jsf":
        return "jsf"
    return "unknown"


def analyze_input_representation(image: np.ndarray, file_type: str = "rendered_image") -> Dict[str, Any]:
    """
    Scientifically analyzes the acoustic input representation to determine whether
    dB conversion and physical gain corrections are physically meaningful.
    """
    rep = validate_input_representation(image, {"file_type": file_type})
    return {
        "representation": rep.representation_type.value,
        "is_rendered": rep.representation_type == RepresentationType.RENDERED_GRAYSCALE,
        "dtype": rep.dtype,
        "min_val": rep.min_val,
        "max_val": rep.max_val,
        "db_conversion_applicable": rep.db_conversion_applicable,
        "db_conversion_skip_reason": rep.audit_note if not rep.db_conversion_applicable else None,
        "metadata_available": rep.metadata_available,
    }


def validate_input_representation(
    image: np.ndarray,
    metadata: Optional[Dict[str, Any]] = None,
) -> InputRepresentation:
    """
    Evaluates matrix properties to determine physical acoustic representation.
    Guards against mathematically distorting double-dB conversion on already-log-compressed PNGs.
    """
    meta = metadata or {}
    filename = meta.get("filename", "")
    file_type = meta.get("file_type", detect_file_format(filename))

    dtype_str = str(image.dtype)
    val_min = float(np.nanmin(image)) if image.size > 0 else 0.0
    val_max = float(np.nanmax(image)) if image.size > 0 else 0.0

    # PNG / JPG rendered images are already log-compressed 8-bit visual representations
    if file_type == "rendered_image" or dtype_str == "uint8" or (val_max <= 255.0 and val_min >= 0.0 and (val_max - val_min) > 1.0 and dtype_str not in ("float32", "float64")):
        rep_type = RepresentationType.RENDERED_GRAYSCALE
        db_applicable = False
        audit_note = "Input is rendered/log-compressed imagery (0-255 range); additional dB conversion would distort dynamic range."
        meta_avail = False
    elif file_type in ("xtf", "jsf"):
        rep_type = RepresentationType.RAW_ACOUSTIC_LINEAR
        db_applicable = True
        audit_note = "Raw sonar telemetry (linear backscatter); dB conversion is mathematically valid."
        meta_avail = True
    elif dtype_str in ("float32", "float64") and val_max > 1.0:
        rep_type = RepresentationType.RAW_ACOUSTIC_LINEAR
        db_applicable = True
        audit_note = "Linear acoustic intensity float array; dB conversion is applicable."
        meta_avail = False
    elif dtype_str in ("float32", "float64") and val_max <= 1.0:
        rep_type = RepresentationType.NORMALIZED_FLOAT
        db_applicable = False
        audit_note = "Normalized [0, 1] float representation; applying 20*log10 without un-normalization is invalid."
        meta_avail = False
    else:
        rep_type = RepresentationType.RENDERED_GRAYSCALE
        db_applicable = False
        audit_note = "Input appears to be rendered grayscale imagery."
        meta_avail = False

    return InputRepresentation(
        representation_type=rep_type,
        shape=image.shape,
        dtype=dtype_str,
        min_val=val_min,
        max_val=val_max,
        db_conversion_applicable=db_applicable,
        audit_note=audit_note,
        metadata_available=meta_avail,
    )
