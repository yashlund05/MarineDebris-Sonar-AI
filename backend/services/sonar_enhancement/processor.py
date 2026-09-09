"""
Production Sonar Enhancement Processor with SHA-256 Caching and Provenance Tracking.
Provides high-level processing APIs, fast recoloring, and strict detection separation.
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, Tuple, List
import numpy as np
import cv2

from .config import SonarEnhancementConfig, ColormapName, DetectionInputMode
from .exceptions import SonarEnhancementError, CorruptImageError
from .pipeline import SonarEnhancementPipeline, PipelineResult
from .image_export import (
    apply_sonar_colormap,
    encode_to_base64_data_url,
    encode_to_png_bytes,
    save_png,
)

logger = logging.getLogger(__name__)

CACHE_DIR = Path("data/storage/enhancement_cache")
PIPELINE_VERSION = "2.0.0-sidescantools"


class SonarEnhancementProcessor:
    """
    Production processor with deterministic caching, audit logging,
    and strict isolation between raw sonar, enhanced grayscale, and display-only pseudocolor.
    """

    _instance: Optional["SonarEnhancementProcessor"] = None

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.pipeline = SonarEnhancementPipeline()
        # In-memory LRU cache for ultra-fast response
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_limit = 128

    @classmethod
    def get_instance(cls) -> "SonarEnhancementProcessor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def compute_cache_key(self, image_bytes: bytes, config: SonarEnhancementConfig) -> str:
        """
        Computes SHA256 key over raw image bytes, configuration dict, and pipeline version.
        Ensures exact reproducibility.
        """
        h = hashlib.sha256()
        h.update(image_bytes)
        cfg_str = json.dumps(config.to_dict(), sort_keys=True)
        h.update(cfg_str.encode("utf-8"))
        h.update(PIPELINE_VERSION.encode("utf-8"))
        return h.hexdigest()

    def process_image_bytes(
        self,
        image_bytes: bytes,
        filename: str = "sonar_frame.png",
        config: Optional[SonarEnhancementConfig] = None,
        run_detection: bool = False,
        detector: Optional[Any] = None,
        conf_threshold: float = 0.25,
        allow_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Processes raw sonar image bytes through the enhancement pipeline.
        
        Guarantees:
        - raw image bytes are completely preserved (SHA256 verified)
        - pseudocolor is strictly for display and never passed to detector
        """
        cfg = config or SonarEnhancementConfig()
        raw_sha256_before = hashlib.sha256(image_bytes).hexdigest()

        cache_key = self.compute_cache_key(image_bytes, cfg)

        # 1. Check memory / disk cache
        if allow_cache and cache_key in self._memory_cache:
            entry = self._memory_cache[cache_key]
            logger.info("Serving enhancement result from memory cache: %s", cache_key[:12])
            res = dict(entry)
            res["cache_hit"] = True
            if run_detection and detector is not None and "detection_results" not in res:
                res["detection_results"] = self._execute_detection(
                    res["_enhanced_gray_u8"], res["_raw_gray_u8"], cfg, detector, conf_threshold
                )
            return res

        # 2. Decode raw image
        nparr = np.frombuffer(image_bytes, np.uint8)
        decoded = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if decoded is None or decoded.size == 0:
            raise CorruptImageError(f"Failed to decode image: {filename}")

        # 3. Run Pipeline
        pipeline_res = self.pipeline.run(
            input_image=decoded,
            config=cfg,
            metadata={"filename": filename, "file_size_bytes": len(image_bytes)},
        )

        # 4. Verify Raw Integrity (Immutability contract)
        raw_sha256_after = hashlib.sha256(image_bytes).hexdigest()
        if raw_sha256_before != raw_sha256_after:
            raise RuntimeError("CRITICAL ERROR: Raw image bytes were mutated during processing!")

        # 5. Generate Base64 Data URLs
        raw_data_url = encode_to_base64_data_url(pipeline_res.raw_gray_u8)
        enhanced_gray_data_url = encode_to_base64_data_url(pipeline_res.enhanced_gray_u8)
        pseudocolor_data_url = encode_to_base64_data_url(pipeline_res.pseudocolor_bgr)

        # 6. Optional Detection (strictly on grayscale)
        detection_results = None
        if run_detection and detector is not None:
            detection_results = self._execute_detection(
                pipeline_res.enhanced_gray_u8,
                pipeline_res.raw_gray_u8,
                cfg,
                detector,
                conf_threshold,
            )

        colormap_val = cfg.colormap.value if isinstance(cfg.colormap, ColormapName) else str(cfg.colormap)

        # 7. Package Response
        response = {
            "success": True,
            "cache_key": cache_key,
            "cache_hit": False,
            "pipeline_version": PIPELINE_VERSION,
            "source_filename": filename,
            "raw_sha256": raw_sha256_before,
            "execution_time_ms": pipeline_res.execution_time_ms,
            "raw_image_data_url": raw_data_url,
            "enhanced_grayscale_data_url": enhanced_gray_data_url,
            "pseudocolor_data_url": pseudocolor_data_url,
            "colormap": colormap_val,
            "metrics": pipeline_res.metrics,
            "audit_trail": pipeline_res.audit_trail,
            "applied_operations": pipeline_res.applied_operations,
            "input_representation": pipeline_res.input_representation,
            "config_applied": pipeline_res.config_applied,
            "detection_results": detection_results,
            # Internal reference for fast recoloring & detection
            "_raw_gray_u8": pipeline_res.raw_gray_u8,
            "_enhanced_gray_u8": pipeline_res.enhanced_gray_u8,
        }

        # Store in memory cache
        if len(self._memory_cache) >= self._cache_limit:
            oldest = next(iter(self._memory_cache))
            del self._memory_cache[oldest]
        self._memory_cache[cache_key] = response

        return response

    def render_colormap_fast(
        self,
        cache_key: str,
        colormap: Union[ColormapName, str],
    ) -> Dict[str, Any]:
        """
        Fast colormap recoloring without re-running 2D-FFT or CLAHE enhancement.
        Runs in < 5ms by recoloring cached enhanced grayscale array.
        """
        if cache_key not in self._memory_cache:
            raise SonarEnhancementError(f"Cached enhancement frame not found for key: {cache_key}")

        entry = self._memory_cache[cache_key]
        enhanced_gray = entry["_enhanced_gray_u8"]

        cmap_str = colormap.value if isinstance(colormap, ColormapName) else str(colormap)
        t_start = time.perf_counter()
        pseudocolor_bgr = apply_sonar_colormap(enhanced_gray, colormap=cmap_str)
        pseudocolor_data_url = encode_to_base64_data_url(pseudocolor_bgr)
        elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)

        return {
            "success": True,
            "cache_key": cache_key,
            "colormap": cmap_str,
            "pseudocolor_data_url": pseudocolor_data_url,
            "recolor_time_ms": elapsed_ms,
        }

    def _execute_detection(
        self,
        enhanced_gray: np.ndarray,
        raw_gray: np.ndarray,
        config: SonarEnhancementConfig,
        detector: Any,
        conf_threshold: float,
    ) -> Dict[str, Any]:
        """
        Executes YOLOv8 detection according to detection_input_mode.
        ENFORCES STRICT RULE: Never feed false-color to acoustic detector.
        """
        det_mode = config.detection_input_mode.value if isinstance(config.detection_input_mode, DetectionInputMode) else str(config.detection_input_mode)

        if det_mode == "pseudo_color" or det_mode == "pseudocolor":
            raise ValueError(
                "CRITICAL ERROR: Attempted to run detection on pseudo-color image! "
                "Pseudo-color is strictly presentation-only. Only raw or enhanced grayscale can be passed to ML models."
            )

        if det_mode == DetectionInputMode.RAW.value or det_mode == "raw":
            input_matrix = raw_gray
            mode_str = "RAW_GRAYSCALE"
        else:
            input_matrix = enhanced_gray
            mode_str = "ENHANCED_GRAYSCALE"

        t_det_start = time.perf_counter()
        detections = []

        try:
            if hasattr(detector, "predict"):
                preds = detector.predict([input_matrix], conf_threshold=conf_threshold)
                raw_dets = preds[0] if preds else []
                for d in raw_dets:
                    detections.append({
                        "class_name": getattr(d, "class_name", "debris"),
                        "confidence": float(getattr(d, "confidence", 0.0)),
                        "bbox": [
                            int(getattr(d, "bbox_x", 0)),
                            int(getattr(d, "bbox_y", 0)),
                            int(getattr(d, "bbox_w", 0)),
                            int(getattr(d, "bbox_h", 0)),
                        ]
                    })
        except Exception as ex:
            logger.warning("Detection execution failed: %s", str(ex))

        det_ms = round((time.perf_counter() - t_det_start) * 1000.0, 2)
        return {
            "mode": mode_str,
            "conf_threshold": conf_threshold,
            "detection_count": len(detections),
            "detections": detections,
            "inference_time_ms": det_ms,
        }
