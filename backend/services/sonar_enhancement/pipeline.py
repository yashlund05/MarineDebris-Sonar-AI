"""
Core SidescanTools Sonar Image Enhancement Pipeline.
Orchestrates representation analysis, 2D-FFT stripe suppression, CLAHE,
homomorphic sharpening, quality metrics, and false-color generation.
"""

import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import cv2

from .config import SonarEnhancementConfig, ColormapName
from .validators import validate_input_representation, InputRepresentation
from .sidescan_adapter import SidescanToolsAdapter
from .quality_metrics import compute_comparative_quality_metrics
from .image_export import apply_sonar_colormap

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Complete result from executing the Sonar Enhancement Pipeline."""
    raw_gray_u8: np.ndarray
    enhanced_gray_u8: np.ndarray
    pseudocolor_bgr: np.ndarray
    metrics: Dict[str, Any]
    audit_trail: List[str]
    applied_operations: List[str]
    execution_time_ms: float
    input_representation: Dict[str, Any]
    config_applied: Dict[str, Any]


class SonarEnhancementPipeline:
    """
    Deterministic domain-aware Sonar Enhancement Pipeline adapting sonoware/sidescantools.
    Guarantees raw image immutability and strict separation between acoustic intensity and pseudocolor.
    """

    def __init__(self, config: Optional[SonarEnhancementConfig] = None):
        self.config = config or SonarEnhancementConfig()
        self.adapter = SidescanToolsAdapter()

    def run(
        self,
        input_image: np.ndarray,
        config: Optional[SonarEnhancementConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Executes the enhancement pipeline on a sonar image.
        """
        t_start = time.perf_counter()
        cfg = config or self.config
        audit: List[str] = []
        applied_ops: List[str] = []

        # 1. Input Representation Validation
        rep = validate_input_representation(input_image, metadata)
        audit.append(
            f"Input analyzed: shape={rep.shape}, dtype={rep.dtype}, "
            f"dynamic_range=[{rep.min_val:.1f}, {rep.max_val:.1f}], "
            f"representation={rep.representation_type.value}"
        )

        # 2. Extract 2D single-channel grayscale
        if input_image.ndim == 3:
            if input_image.shape[2] == 1:
                raw_2d = input_image.squeeze(2)
            elif input_image.shape[2] == 3:
                raw_2d = cv2.cvtColor(input_image, cv2.COLOR_BGR2GRAY)
                audit.append("Collapsed 3-channel input to 1-channel acoustic backscatter")
            elif input_image.shape[2] == 4:
                raw_2d = cv2.cvtColor(input_image, cv2.COLOR_BGRA2GRAY)
                audit.append("Collapsed 4-channel BGRA to 1-channel acoustic backscatter")
            else:
                raw_2d = input_image[:, :, 0]
                audit.append("Extracted first channel from multi-channel input")
        else:
            raw_2d = input_image.copy()

        # Ensure raw uint8 version for reference and immutability check
        if raw_2d.dtype == np.uint8:
            raw_gray_u8 = raw_2d.copy()
        elif raw_2d.dtype == np.uint16:
            raw_gray_u8 = (raw_2d / 256.0).clip(0, 255).astype(np.uint8)
        else:
            if raw_2d.max() <= 1.0:
                raw_gray_u8 = (raw_2d * 255.0).clip(0, 255).astype(np.uint8)
            else:
                raw_gray_u8 = raw_2d.clip(0, 255).astype(np.uint8)

        # Work on float32 array for signal processing
        cur_arr = raw_2d.astype(np.float32)

        # 3. Logarithmic dB conversion (Conditional & Safe)
        if cfg.convert_to_db:
            if rep.db_conversion_applicable:
                cur_arr = self.adapter.convert_to_dB(cur_arr)
                applied_ops.append("dB_conversion")
                audit.append("Applied 20*log10 dB conversion to linear acoustic intensity")
            else:
                audit.append(f"dB conversion skipped: {rep.audit_note}")
        else:
            audit.append("dB conversion disabled by configuration")

        # 4. 2D-FFT Directional Pie-Slice Stripe Noise Suppression
        if cfg.stripe_noise_filter:
            cur_arr, applied = self.adapter.apply_pie_slice_filter(cur_arr)
            if applied:
                applied_ops.append("stripe_noise_filter_fft")
                audit.append("Applied 2D-FFT directional pie-slice filter for stripe noise suppression")
            else:
                audit.append("Stripe filter evaluated: no periodic stripe peaks exceeded threshold")
        else:
            audit.append("Stripe noise suppression disabled by configuration")

        # 5. Acoustic CLAHE (Contrast-Limited Adaptive Histogram Equalization)
        if cfg.clahe:
            cur_arr = self.adapter.hist_equalization(
                cur_arr,
                clip_limit=cfg.clahe_clip_limit,
            )
            applied_ops.append("clahe")
            audit.append(
                f"Applied CLAHE contrast equalization (clip_limit={cfg.clahe_clip_limit})"
            )
        else:
            audit.append("CLAHE disabled by configuration")

        # 6. Experimental Homomorphic Sharpening (Defaults to False)
        if cfg.sharpening:
            cur_arr, _ = self.adapter.apply_sharpening_filter(
                cur_arr,
                gamma_h=cfg.sharpening_gamma_h,
                gamma_l=cfg.sharpening_gamma_l,
                const_c=cfg.sharpening_c,
            )
            applied_ops.append("homomorphic_sharpening")
            audit.append(
                f"Applied homomorphic sharpening (gamma_h={cfg.sharpening_gamma_h}, gamma_l={cfg.sharpening_gamma_l})"
            )
        else:
            audit.append("Homomorphic sharpening disabled (experimental feature)")

        # 7. Physical Gain Normalization (BAC / EGN)
        if cfg.gain_normalization:
            if metadata and ("altitude" in metadata or "beam_angles" in metadata):
                cur_arr = self.adapter.apply_gain_normalization(cur_arr, metadata)
                applied_ops.append("gain_normalization")
                audit.append("Applied acoustic beam and grazing angle gain compensation (BAC/EGN)")
            else:
                audit.append("Gain normalization skipped: physical geometry metadata unavailable for PNG input")
        else:
            audit.append("Gain normalization disabled by configuration")

        # 8. Normalization to uint8 (0 - 255)
        enhanced_gray_u8 = self.adapter.normalize_to_uint8(cur_arr)
        applied_ops.append("uint8_normalization")

        # 9. Compute Non-Reference and Comparative Acoustic Quality Metrics
        metrics = compute_comparative_quality_metrics(raw_gray_u8, enhanced_gray_u8)

        # 10. Display-only False-Color Rendering
        pseudocolor_bgr = apply_sonar_colormap(enhanced_gray_u8, colormap=cfg.colormap)

        elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return PipelineResult(
            raw_gray_u8=raw_gray_u8,
            enhanced_gray_u8=enhanced_gray_u8,
            pseudocolor_bgr=pseudocolor_bgr,
            metrics=metrics,
            audit_trail=audit,
            applied_operations=applied_ops,
            execution_time_ms=elapsed_ms,
            input_representation={
                "type": rep.representation_type.value,
                "shape": list(rep.shape),
                "dtype": str(rep.dtype),
                "min_val": rep.min_val,
                "max_val": rep.max_val,
                "db_applicable": rep.db_conversion_applicable,
            },
            config_applied=cfg.to_dict(),
        )
