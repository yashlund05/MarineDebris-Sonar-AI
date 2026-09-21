"""Live Sonar AI Inference Worker.

Orchestrates preprocessing, production YOLOv8 model inference, ByteTrack temporal tracking,
acoustic shadow evaluation, and geospatial association for continuous acoustic video streams.
Conforms to Requirements R2 §15–§26 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from backend.config import get_settings
from backend.inference.detector import CLASS_NAMES, RawDetection, detect_tiles
from backend.inference.model_loader import ModelLoader
from backend.live_sonar.models import (
    LiveNavigationData,
    LiveSonarTelemetry,
    SonarFrame,
)
from backend.live_sonar.pipeline.confirmation import TemporalConfirmationFilter
from backend.live_sonar.pipeline.georeference import associate_geolocation
from backend.live_sonar.pipeline.preprocess import PreprocessingProfile, preprocess_live_image
from backend.live_sonar.pipeline.shadow import evaluate_acoustic_shadow
from backend.live_sonar.pipeline.tracker import ByteTrackSonarTracker, LiveTrack

logger = logging.getLogger(__name__)


@dataclass
class LiveDetectionResult:
    """Consolidated AI detection and tracking result for an incoming frame."""
    frame_id: str
    session_id: str
    sequence_number: int
    timestamp_utc: datetime
    raw_image: np.ndarray
    processed_image: np.ndarray
    detections: List[Dict[str, Any]]
    active_tracks: List[LiveTrack]
    confirmed_targets_count: int
    latency_breakdown_ms: Dict[str, float]
    effective_fps: float
    sonar_telemetry: Optional[LiveSonarTelemetry]
    navigation: Optional[LiveNavigationData]
    preview_jpeg: Optional[bytes] = None  # Lightweight preview frame for WebSocket


class LiveInferenceWorker:
    """Dedicated inference worker isolated from HTTP request lifecycle.

    Maintains session-specific ByteTrack tracker and temporal confirmation state.
    Reuses the singleton production YOLOv8 model loaded once per worker.
    """

    def __init__(
        self,
        session_id: str,
        conf_threshold: float = 0.35,
        target_inference_fps: float = 10.0,
        preprocessing_profile: str = "REALTIME",
        min_confirmed_frames: int = 3,
    ) -> None:
        self.session_id = session_id
        self.conf_threshold = conf_threshold
        self.target_inference_fps = target_inference_fps
        self.preprocessing_profile = preprocessing_profile

        # Ensure model is loaded once through singleton loader
        self._model = ModelLoader.get_detection_model()
        self._device = ModelLoader.get_device()

        # Session-isolated tracker & confirmation filter
        self.tracker = ByteTrackSonarTracker(
            high_thresh=conf_threshold,
            low_thresh=max(0.10, conf_threshold * 0.4),
            confirm_frames=min_confirmed_frames,
        )
        self.confirmation_filter = TemporalConfirmationFilter(
            min_confirmed_frames=min_confirmed_frames,
            confidence_threshold=conf_threshold,
        )

        # Performance tracking
        self._last_process_time: Optional[float] = None
        self._processed_count = 0
        self._fps_history: List[float] = []

    def reset(self) -> None:
        """Reset state when session restarts or switches streams."""
        self.tracker.reset()
        self._processed_count = 0
        self._last_process_time = None

    def process_frame(
        self,
        frame: SonarFrame,
        generate_preview: bool = True,
    ) -> LiveDetectionResult:
        """Execute full preprocessing -> detection -> tracking -> reasoning pipeline on a single frame."""
        t_start = time.perf_counter()

        # 1. Preprocess frame (preserving raw immutability)
        t_prep_start = time.perf_counter()
        processed_image = preprocess_live_image(
            frame.image_data,
            profile=self.preprocessing_profile,
        )
        t_prep_end = time.perf_counter()
        preprocess_ms = (t_prep_end - t_prep_start) * 1000.0

        # 2. AI Model Inference
        t_infer_start = time.perf_counter()
        raw_detections = self._run_model_inference(processed_image)
        t_infer_end = time.perf_counter()
        inference_ms = (t_infer_end - t_infer_start) * 1000.0

        # Convert detections to standardized dicts
        detection_dicts = []
        for det in raw_detections:
            # Physical acoustic shadow reasoning
            shadow_status = evaluate_acoustic_shadow(
                processed_image,
                (det.bbox_x, det.bbox_y, det.bbox_w, det.bbox_h),
            )
            # Geolocation association
            lat, lon, depth = associate_geolocation(
                (det.bbox_x, det.bbox_y, det.bbox_w, det.bbox_h),
                processed_image.shape[:2],
                frame.navigation,
                range_m=frame.sonar_metadata.range_m if frame.sonar_metadata else None,
            )

            det_dict = {
                "class_id": det.class_id,
                "class_name": det.class_name,
                "confidence": round(det.confidence, 4),
                "bbox_x": det.bbox_x,
                "bbox_y": det.bbox_y,
                "bbox_w": det.bbox_w,
                "bbox_h": det.bbox_h,
                "acoustic_shadow": shadow_status,
                "latitude": lat,
                "longitude": lon,
                "depth_m": depth,
            }
            detection_dicts.append(det_dict)

        # 3. ByteTrack Temporal Tracking
        t_track_start = time.perf_counter()
        tracks = self.tracker.update(
            detection_dicts,
            frame_sequence=frame.sequence_number,
            timestamp_utc=frame.timestamp_utc,
            frame_metadata=frame.source_metadata,
        )

        # 4. Temporal Confirmation & Class Consistency Filtering
        confirmed_tracks = self.confirmation_filter.apply(tracks)

        # Update tracks with shadow and geolocation
        for trk in confirmed_tracks:
            trk.acoustic_shadow = evaluate_acoustic_shadow(processed_image, trk.bbox)
            lat, lon, depth = associate_geolocation(
                trk.bbox,
                processed_image.shape[:2],
                frame.navigation,
                range_m=frame.sonar_metadata.range_m if frame.sonar_metadata else None,
            )
            trk.latitude = lat
            trk.longitude = lon
            trk.depth_m = depth

        t_track_end = time.perf_counter()
        tracking_ms = (t_track_end - t_track_start) * 1000.0

        t_total_end = time.perf_counter()
        total_ms = (t_total_end - t_start) * 1000.0

        # Calculate effective FPS
        now = time.perf_counter()
        if self._last_process_time is not None:
            dt = now - self._last_process_time
            if dt > 0:
                current_fps = 1.0 / dt
                self._fps_history.append(current_fps)
                if len(self._fps_history) > 30:
                    self._fps_history.pop(0)
        self._last_process_time = now
        effective_fps = round(float(np.mean(self._fps_history)), 1) if self._fps_history else 0.0
        self._processed_count += 1

        # 5. Generate lightweight preview JPEG if requested (keeping bandwidth bounded)
        preview_jpeg = None
        if generate_preview and processed_image.size > 0:
            # Scale down if large for WebSocket transmission
            preview_img = processed_image
            h, w = preview_img.shape[:2]
            if w > 800:
                scale = 800.0 / w
                preview_img = cv2.resize(preview_img, (800, int(h * scale)), interpolation=cv2.INTER_AREA)

            success, encoded = cv2.imencode(".jpg", preview_img, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if success:
                preview_jpeg = encoded.tobytes()

        confirmed_count = sum(1 for t in confirmed_tracks if t.status == "CONFIRMED")

        return LiveDetectionResult(
            frame_id=frame.frame_id,
            session_id=frame.session_id or self.session_id,
            sequence_number=frame.sequence_number,
            timestamp_utc=frame.timestamp_utc,
            raw_image=frame.image_data,
            processed_image=processed_image,
            detections=detection_dicts,
            active_tracks=confirmed_tracks,
            confirmed_targets_count=confirmed_count,
            latency_breakdown_ms={
                "preprocess_ms": round(preprocess_ms, 2),
                "inference_ms": round(inference_ms, 2),
                "tracking_ms": round(tracking_ms, 2),
                "total_ms": round(total_ms, 2),
            },
            effective_fps=effective_fps,
            sonar_telemetry=frame.sonar_metadata,
            navigation=frame.navigation,
            preview_jpeg=preview_jpeg,
        )

    def _run_model_inference(self, image: np.ndarray) -> List[RawDetection]:
        """Run production YOLOv8 model inference via detect_tiles or direct predict."""
        if self._model is None:
            # Try reloading once
            self._model = ModelLoader.get_detection_model()
            if self._model is None:
                logger.warning("Production detection model not available. Returning 0 detections.")
                return []

        try:
            # Format image for YOLOv8
            img_bgr = image
            if img_bgr.ndim == 2:
                img_bgr = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

            # Use detect_tiles with a single full-resolution tile
            tile_results = detect_tiles(
                [img_bgr],
                model=self._model,
                conf_threshold=self.conf_threshold,
                device=self._device,
            )
            if tile_results and len(tile_results) > 0:
                return tile_results[0]
            return []
        except Exception as e:
            logger.error(f"Inference error on live frame: {e}")
            return []
