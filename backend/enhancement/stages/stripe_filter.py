"""
Modular 2D FFT stripe-noise and periodic-artifact reduction stage.

Implements Requirement R10:
- Frequency-domain periodic stripe detection via 2D FFT
- Directional notch filtering
- Confidence gating: Automatically skips when confidence < threshold (0.40)
  to prevent erasing real linear debris (pipes, cables, chains, moorings).
"""

from __future__ import annotations

from typing import Tuple, Dict, Any
import numpy as np
import cv2

from backend.enhancement.pipeline_base import (
    SonarEnhancementStage,
    SonarEnhancementContext,
    Modality,
    SignalRepresentation,
)


class StripeNoiseNotchStage(SonarEnhancementStage):
    """
    Directional frequency-domain notch filter for horizontal/vertical scanning stripes.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.40,
        notch_width: int = 3,
        attenuation: float = 0.85,
        name: str = "StripeNoiseNotchFilter",
    ):
        super().__init__(name=name, is_ai_safe_default=True)
        self.confidence_threshold = confidence_threshold
        self.notch_width = notch_width
        self.attenuation = attenuation

    def validate_input(self, image: np.ndarray, context: SonarEnhancementContext) -> bool:
        return image is not None and image.ndim == 2 and image.shape[0] >= 32 and image.shape[1] >= 32

    def process(
        self, image: np.ndarray, context: SonarEnhancementContext
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        h, w = image.shape
        # 1. 2D Fast Fourier Transform
        f_transform = np.fft.fft2(image)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)

        # 2. Analyze directional energy along principal vertical/horizontal axes
        center_y, center_x = h // 2, w // 2
        # Exclude DC component center window
        dc_radius = 5
        col_energy = np.sum(magnitude_spectrum[:, center_x - 1 : center_x + 2], axis=1)
        row_energy = np.sum(magnitude_spectrum[center_y - 1 : center_y + 2, :], axis=0)

        total_mag = np.sum(magnitude_spectrum) + 1e-7
        # Energy concentrated in narrow horizontal/vertical bands
        horiz_stripe_energy = float(np.sum(col_energy[dc_radius:-dc_radius]) / total_mag)
        vert_stripe_energy = float(np.sum(row_energy[dc_radius:-dc_radius]) / total_mag)

        max_stripe_energy = max(horiz_stripe_energy, vert_stripe_energy)
        # Empirical confidence: periodic stripe pattern has high directional spectral energy ratio
        confidence = float(np.clip(max_stripe_energy * 25.0, 0.0, 1.0))

        metrics: Dict[str, Any] = {
            "detected_horiz_energy": round(horiz_stripe_energy, 4),
            "detected_vert_energy": round(vert_stripe_energy, 4),
            "stripe_confidence": round(confidence, 3),
            "confidence_threshold": self.confidence_threshold,
            "stage_applied": False,
        }

        # Safe gating: If stripe energy is below confidence threshold, SKIP to protect genuine linear targets
        if confidence < self.confidence_threshold:
            metrics["skip_reason"] = "Confidence below threshold; skipped to protect potential linear debris structures."
            return image, metrics

        # 3. Create directional notch mask
        mask = np.ones((h, w), dtype=np.float32)
        nw = self.notch_width

        if horiz_stripe_energy >= vert_stripe_energy:
            # Vertical frequency line corresponding to horizontal stripes
            mask[:, center_x - nw : center_x + nw + 1] = 1.0 - self.attenuation
        else:
            # Horizontal frequency line corresponding to vertical stripes
            mask[center_y - nw : center_y + nw + 1, :] = 1.0 - self.attenuation

        # Preserve DC center component
        cv2.circle(mask, (center_x, center_y), dc_radius, 1.0, -1)

        # 4. Apply filter and Inverse FFT
        f_shift_filtered = f_shift * mask
        f_ishift = np.fft.ifftshift(f_shift_filtered)
        img_back = np.fft.ifft2(f_ishift)
        filtered = np.real(img_back)

        # Clip back to canonical float32 [0.0, 1.0]
        out_image = np.clip(filtered, 0.0, 1.0).astype(np.float32)

        # Compute delta metrics
        diff = np.abs(out_image - image)
        metrics.update({
            "stage_applied": True,
            "mean_pixel_shift": float(np.mean(diff)),
            "max_pixel_shift": float(np.max(diff)),
            "altered_pixel_ratio": float(np.sum(diff > 0.01) / image.size),
        })

        return out_image, metrics
