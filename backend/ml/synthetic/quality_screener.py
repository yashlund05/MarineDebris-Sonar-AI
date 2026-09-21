"""
MarineDebris-Sonar-AI: Synthetic Sonar Data Quality Screening Engine
Enforces rigorous acoustic physics gates, label integrity checks, and shadow plausibility
prior to admitting synthetic samples into experimental training manifests.
"""

from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import cv2
import numpy as np


class SyntheticScreeningStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EXPERIMENTAL_ONLY = "EXPERIMENTAL_ONLY"


@dataclass
class ScreeningResult:
    sample_path: str
    status: SyntheticScreeningStatus
    rejection_reasons: List[str]
    contrast_ratio: float
    shadow_contrast_ratio: float
    has_valid_shadow: bool
    label_valid: bool
    dimensions: Tuple[int, int]
    is_screened: bool = True


class SyntheticQualityScreener:
    """
    Automated gatekeeper for physics-based and generative synthetic sonar images.
    Blocks samples that violate acoustic backscatter bounds or shadow geometry.
    """

    def __init__(
        self,
        min_contrast: float = 1.15,
        min_shadow_depth: float = 0.85,
        required_dims: Tuple[int, int] = (640, 640),
    ):
        self.min_contrast = min_contrast
        self.min_shadow_depth = min_shadow_depth
        self.required_dims = required_dims

    def screen_sample(
        self,
        image_path: Path,
        label_path: Optional[Path] = None,
    ) -> ScreeningResult:
        """
        Executes multi-point acoustic screening on a synthetic sonar sample.
        """
        image_path = Path(image_path)
        reasons = []

        if not image_path.exists():
            return ScreeningResult(
                sample_path=str(image_path),
                status=SyntheticScreeningStatus.REJECTED,
                rejection_reasons=["File not found on disk"],
                contrast_ratio=0.0,
                shadow_contrast_ratio=0.0,
                has_valid_shadow=False,
                label_valid=False,
                dimensions=(0, 0),
            )

        img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            return ScreeningResult(
                sample_path=str(image_path),
                status=SyntheticScreeningStatus.REJECTED,
                rejection_reasons=["Corrupt or unreadable image file"],
                contrast_ratio=0.0,
                shadow_contrast_ratio=0.0,
                has_valid_shadow=False,
                label_valid=False,
                dimensions=(0, 0),
            )

        h, w = img.shape[:2]
        if (w, h) != self.required_dims:
            reasons.append(f"Invalid dimensions {w}x{h} (expected {self.required_dims[0]}x{self.required_dims[1]})")

        # Check for NaN / Inf / Flat image
        if np.isnan(img).any() or np.isinf(img).any():
            reasons.append("Image contains NaN or Inf values")

        if np.std(img) < 3.0:
            reasons.append("Image is degenerate / flat noise background")

        # Verify YOLO label
        label_valid = False
        boxes = []
        if label_path and Path(label_path).exists():
            with open(label_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) == 0:
                reasons.append("Synthetic positive sample has empty label file")
            else:
                label_valid = True
                for idx, line in enumerate(lines, 1):
                    parts = line.strip().split()
                    if len(parts) != 5:
                        reasons.append(f"Label line {idx} malformed: expected 5 tokens, got {len(parts)}")
                        label_valid = False
                        continue
                    try:
                        cid = int(parts[0])
                        xc, yc, bw, bh = map(float, parts[1:])
                        if not (0.0 <= xc <= 1.0 and 0.0 <= yc <= 1.0 and 0.0 < bw <= 1.0 and 0.0 < bh <= 1.0):
                            reasons.append(f"Box {idx} out of normalized bounds [0, 1]")
                            label_valid = False
                        else:
                            boxes.append((cid, xc, yc, bw, bh))
                    except ValueError:
                        reasons.append(f"Label line {idx} non-numeric tokens")
                        label_valid = False
        else:
            reasons.append("Missing label file for synthetic training candidate")

        # Acoustic shadow and target contrast check
        contrast_ratio = 1.0
        shadow_ratio = 1.0
        has_valid_shadow = False

        if label_valid and len(boxes) > 0:
            for _, xc, yc, bw, bh in boxes:
                # Target ROI
                tx1 = int(max(0, (xc - bw / 2.0) * w))
                tx2 = int(min(w, (xc + bw / 2.0) * w))
                ty1 = int(max(0, (yc - bh / 2.0) * h))
                ty2 = int(min(h, (yc + bh / 2.0) * h))

                if tx2 > tx1 and ty2 > ty1:
                    target_roi = img[ty1:ty2, tx1:tx2]
                    target_mean = float(np.mean(target_roi))

                    # Immediate downstream shadow zone (in FLS range axis, down from target)
                    sy1 = ty2
                    sy2 = int(min(h, ty2 + (ty2 - ty1) * 1.5))
                    if sy2 > sy1:
                        shadow_roi = img[sy1:sy2, tx1:tx2]
                        shadow_mean = float(np.mean(shadow_roi))
                        if shadow_mean > 0:
                            shadow_ratio = target_mean / max(1.0, shadow_mean)
                            if shadow_ratio >= 1.20:
                                has_valid_shadow = True

                    # Background comparison
                    bg_mean = float(np.mean(img))
                    if bg_mean > 0:
                        contrast_ratio = target_mean / bg_mean

        if contrast_ratio < self.min_contrast:
            reasons.append(f"Insufficient target-to-background contrast: {contrast_ratio:.2f} < {self.min_contrast}")

        if not has_valid_shadow:
            reasons.append("Missing or unverified acoustic shadow in downstream range")

        if len(reasons) == 0:
            status = SyntheticScreeningStatus.ACCEPTED
        elif len(reasons) == 1 and "shadow" in reasons[0].lower():
            status = SyntheticScreeningStatus.EXPERIMENTAL_ONLY
        else:
            status = SyntheticScreeningStatus.REJECTED

        return ScreeningResult(
            sample_path=str(image_path),
            status=status,
            rejection_reasons=reasons,
            contrast_ratio=round(contrast_ratio, 2),
            shadow_contrast_ratio=round(shadow_ratio, 2),
            has_valid_shadow=has_valid_shadow,
            label_valid=label_valid,
            dimensions=(w, h),
        )
