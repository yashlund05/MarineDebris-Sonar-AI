"""Evidence Capture Engine for Live Sonar Targets.

Captures multi-representation evidence crops (raw, enhanced, annotated)
and structured metadata JSON for confirmed acoustic targets and manual snapshots.
Conforms to Requirement R5 §37 & §64 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from backend.config import get_settings

logger = logging.getLogger(__name__)


def capture_evidence(
    session_id: str,
    track_id: int,
    frame_id: str,
    raw_image: np.ndarray,
    processed_image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    class_name: str,
    confidence: float,
    metadata: Optional[Dict[str, Any]] = None,
    output_base_dir: Optional[str] = None,
) -> Dict[str, str]:
    """Capture raw, enhanced, and annotated evidence crops plus metadata JSON.

    Guarantees raw image immutability by operating only on sliced views/copies.
    Returns dictionary with relative or absolute paths to the saved artifacts.
    """
    settings = get_settings()
    base_dir = Path(output_base_dir or getattr(settings, "STORAGE_LOCAL_PATH", "data/storage"))
    evidence_dir = base_dir / "evidence" / f"session_{session_id}" / f"track_{track_id}"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_%f")
    prefix = f"frame_{frame_id[:8]}_{timestamp_str}"

    h_img, w_img = raw_image.shape[:2]
    x, y, w, h = bbox

    # Expand box slightly for acoustic context (20% padding)
    pad_x = int(w * 0.2)
    pad_y = int(h * 0.2)
    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w_img, x + w + pad_x)
    y2 = min(h_img, y + h + pad_y)

    # 1. Raw Crop
    raw_crop = raw_image[y1:y2, x1:x2].copy()
    raw_path = evidence_dir / f"{prefix}_raw.png"
    cv2.imwrite(str(raw_path), raw_crop)

    # 2. Enhanced Crop
    enh_crop = processed_image[y1:y2, x1:x2].copy()
    enh_path = evidence_dir / f"{prefix}_enhanced.png"
    cv2.imwrite(str(enh_path), enh_crop)

    # 3. Annotated Crop
    annotated_crop = enh_crop.copy()
    if annotated_crop.ndim == 2:
        annotated_crop = cv2.cvtColor(annotated_crop, cv2.COLOR_GRAY2BGR)

    # Draw box relative to crop coordinates
    rel_x = x - x1
    rel_y = y - y1
    cv2.rectangle(annotated_crop, (rel_x, rel_y), (rel_x + w, rel_y + h), (59, 82, 200), 2)  # Terracotta BGR
    label = f"T-{track_id} {class_name} {int(confidence * 100)}%"
    cv2.putText(
        annotated_crop,
        label,
        (rel_x, max(12, rel_y - 6)),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.4,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    annot_path = evidence_dir / f"{prefix}_annotated.png"
    cv2.imwrite(str(annot_path), annotated_crop)

    # 4. Metadata JSON
    meta_payload = {
        "evidence_id": str(uuid.uuid4()),
        "session_id": session_id,
        "track_id": track_id,
        "frame_id": frame_id,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "class_name": class_name,
        "confidence": float(confidence),
        "bbox": {"x": int(x), "y": int(y), "w": int(w), "h": int(h)},
        "crop_bounds": {"x1": int(x1), "y1": int(y1), "x2": int(x2), "y2": int(y2)},
        "model_version": getattr(settings, "DEFAULT_DETECTION_MODEL_VERSION", "1.0.0"),
        "extra_metadata": metadata or {},
    }
    meta_path = evidence_dir / f"{prefix}_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)

    return {
        "raw_crop_path": str(raw_path).replace("\\", "/"),
        "enhanced_crop_path": str(enh_path).replace("\\", "/"),
        "annotated_crop_path": str(annot_path).replace("\\", "/"),
        "metadata_json_path": str(meta_path).replace("\\", "/"),
    }
