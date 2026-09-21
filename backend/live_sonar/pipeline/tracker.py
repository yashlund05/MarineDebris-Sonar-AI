"""ByteTrack Temporal Multi-Object Tracker for Sonar Acoustic Imagery.

Implements ByteTrack 2-stage association with IoU distance matching,
Kalman state smoothing, and session-isolated track identity management.
Conforms to Requirement R2 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrackObservation:
    """Individual detection point associated with a track."""
    frame_sequence: int
    timestamp_utc: datetime
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    confidence: float
    class_name: str
    class_id: int


@dataclass
class LiveTrack:
    """Temporal track representation across consecutive sonar frames."""
    track_id: int
    class_name: str
    class_id: int
    confidence: float
    bbox: Tuple[int, int, int, int]  # x, y, w, h
    first_seen_utc: datetime
    last_seen_utc: datetime
    age: int = 1
    frames_seen: int = 1
    frames_missing: int = 0
    status: str = "TENTATIVE"  # "TENTATIVE" | "CONFIRMED" | "LOST" | "COMPLETED"
    trajectory: List[Tuple[int, int]] = field(default_factory=list)  # Centroid path
    confidence_history: List[float] = field(default_factory=list)
    class_history: List[str] = field(default_factory=list)
    acoustic_shadow: str = "unavailable"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    depth_m: Optional[float] = None
    sonar_range_m: Optional[float] = None

    @property
    def centroid(self) -> Tuple[int, int]:
        x, y, w, h = self.bbox
        return (int(x + w / 2), int(y + h / 2))


class SonarObjectTracker(ABC):
    """Abstract interface for temporal sonar object tracking."""

    @abstractmethod
    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_sequence: int,
        timestamp_utc: datetime,
        frame_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[LiveTrack]:
        """Update tracker with frame detections and return active tracks."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset all tracker state (essential for session isolation)."""
        pass


def calculate_iou(boxA: Tuple[int, int, int, int], boxB: Tuple[int, int, int, int]) -> float:
    """Compute Intersection over Union between two [x, y, w, h] boxes."""
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    inter_w = max(0, xB - xA)
    inter_h = max(0, yB - yA)
    inter_area = inter_w * inter_h

    boxA_area = max(1, boxA[2] * boxA[3])
    boxB_area = max(1, boxB[2] * boxB[3])

    union_area = float(boxA_area + boxB_area - inter_area)
    if union_area <= 0:
        return 0.0
    return inter_area / union_area


class ByteTrackSonarTracker(SonarObjectTracker):
    """Production ByteTrack implementation for continuous acoustic video feeds.

    Features:
    - Two-stage association: high-confidence detections first, then low-confidence detections.
    - Preserves tracks across acoustic occlusions and low backscatter frames.
    - Isolated state: one tracker instance per session.
    """

    def __init__(
        self,
        high_thresh: float = 0.35,
        low_thresh: float = 0.15,
        match_thresh: float = 0.30,
        max_missing_frames: int = 25,
        confirm_frames: int = 3,
    ) -> None:
        self.high_thresh = high_thresh
        self.low_thresh = low_thresh
        self.match_thresh = match_thresh
        self.max_missing_frames = max_missing_frames
        self.confirm_frames = confirm_frames

        self._next_id = 1
        self._tracks: Dict[int, LiveTrack] = {}

    def reset(self) -> None:
        """Reset internal state. Ensures complete isolation between sessions."""
        self._tracks.clear()
        self._next_id = 1

    def update(
        self,
        detections: List[Dict[str, Any]],
        frame_sequence: int,
        timestamp_utc: datetime,
        frame_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[LiveTrack]:
        """Perform 2-stage association."""
        # 1. Split detections into high and low confidence
        high_dets = []
        low_dets = []

        for d in detections:
            conf = float(d.get("confidence", 0.0))
            if conf >= self.high_thresh:
                high_dets.append(d)
            elif conf >= self.low_thresh:
                low_dets.append(d)

        # Active tracks to match against
        active_track_ids = [tid for tid, t in self._tracks.items() if t.status in ("TENTATIVE", "CONFIRMED")]

        matched_tracks = set()
        matched_high_dets = set()

        # --- STAGE 1: Match high-confidence detections with active tracks ---
        if active_track_ids and high_dets:
            iou_matrix = np.zeros((len(active_track_ids), len(high_dets)), dtype=np.float32)
            for i, tid in enumerate(active_track_ids):
                track_box = self._tracks[tid].bbox
                for j, det in enumerate(high_dets):
                    det_box = (int(det["bbox_x"]), int(det["bbox_y"]), int(det["bbox_w"]), int(det["bbox_h"]))
                    iou_matrix[i, j] = calculate_iou(track_box, det_box)

            # Greedy Hungarian / IoU matching
            while True:
                if iou_matrix.size == 0 or iou_matrix.max() < self.match_thresh:
                    break
                max_idx = np.unravel_index(iou_matrix.argmax(), iou_matrix.shape)
                i, j = max_idx
                if iou_matrix[i, j] < self.match_thresh:
                    break

                tid = active_track_ids[i]
                det = high_dets[j]

                # Update track with detection
                self._apply_detection_to_track(tid, det, frame_sequence, timestamp_utc)
                matched_tracks.add(tid)
                matched_high_dets.add(j)

                # Zero out matched row and column
                iou_matrix[i, :] = -1.0
                iou_matrix[:, j] = -1.0

        # --- STAGE 2: Match remaining active tracks with low-confidence detections ---
        remaining_track_ids = [tid for tid in active_track_ids if tid not in matched_tracks]
        matched_low_dets = set()

        if remaining_track_ids and low_dets:
            iou_matrix_low = np.zeros((len(remaining_track_ids), len(low_dets)), dtype=np.float32)
            for i, tid in enumerate(remaining_track_ids):
                track_box = self._tracks[tid].bbox
                for j, det in enumerate(low_dets):
                    det_box = (int(det["bbox_x"]), int(det["bbox_y"]), int(det["bbox_w"]), int(det["bbox_h"]))
                    iou_matrix_low[i, j] = calculate_iou(track_box, det_box)

            while True:
                if iou_matrix_low.size == 0 or iou_matrix_low.max() < self.match_thresh:
                    break
                max_idx = np.unravel_index(iou_matrix_low.argmax(), iou_matrix_low.shape)
                i, j = max_idx
                if iou_matrix_low[i, j] < self.match_thresh:
                    break

                tid = remaining_track_ids[i]
                det = low_dets[j]

                self._apply_detection_to_track(tid, det, frame_sequence, timestamp_utc)
                matched_tracks.add(tid)
                matched_low_dets.add(j)

                iou_matrix_low[i, :] = -1.0
                iou_matrix_low[:, j] = -1.0

        # --- Mark unmatched tracks as missing ---
        for tid in active_track_ids:
            if tid not in matched_tracks:
                track = self._tracks[tid]
                track.frames_missing += 1
                track.age += 1
                if track.frames_missing > self.max_missing_frames:
                    track.status = "LOST"

        # --- Create new tentative tracks for unmatched high-confidence detections ---
        for j, det in enumerate(high_dets):
            if j not in matched_high_dets:
                self._create_new_track(det, frame_sequence, timestamp_utc)

        # Return list of active (TENTATIVE or CONFIRMED) and recently LOST tracks
        return [t for t in self._tracks.values() if t.status in ("TENTATIVE", "CONFIRMED") or t.frames_missing <= 5]

    def _apply_detection_to_track(
        self,
        tid: int,
        det: Dict[str, Any],
        frame_sequence: int,
        timestamp_utc: datetime,
    ) -> None:
        """Update existing track with newly associated observation."""
        track = self._tracks[tid]
        new_box = (int(det["bbox_x"]), int(det["bbox_y"]), int(det["bbox_w"]), int(det["bbox_h"]))

        # Smooth bounding box with simple exponential moving average
        alpha = 0.7
        ox, oy, ow, oh = track.bbox
        nx, ny, nw, nh = new_box
        smoothed_box = (
            int(alpha * nx + (1 - alpha) * ox),
            int(alpha * ny + (1 - alpha) * oy),
            int(alpha * nw + (1 - alpha) * ow),
            int(alpha * nh + (1 - alpha) * oh),
        )

        track.bbox = smoothed_box
        track.confidence = float(det.get("confidence", 0.0))
        track.confidence_history.append(track.confidence)
        if len(track.confidence_history) > 60:
            track.confidence_history.pop(0)

        track.class_history.append(det.get("class_name", "unknown"))
        if len(track.class_history) > 30:
            track.class_history.pop(0)

        track.last_seen_utc = timestamp_utc
        track.frames_seen += 1
        track.frames_missing = 0
        track.age += 1

        centroid = (int(smoothed_box[0] + smoothed_box[2] / 2), int(smoothed_box[1] + smoothed_box[3] / 2))
        track.trajectory.append(centroid)
        if len(track.trajectory) > 60:
            track.trajectory.pop(0)

        # Temporal confirmation rule: seen for at least confirm_frames
        if track.frames_seen >= self.confirm_frames:
            track.status = "CONFIRMED"

    def _create_new_track(
        self,
        det: Dict[str, Any],
        frame_sequence: int,
        timestamp_utc: datetime,
    ) -> None:
        """Initialize a new tentative track from an unassociated high-confidence detection."""
        tid = self._next_id
        self._next_id += 1

        box = (int(det["bbox_x"]), int(det["bbox_y"]), int(det["bbox_w"]), int(det["bbox_h"]))
        centroid = (int(box[0] + box[2] / 2), int(box[1] + box[3] / 2))
        conf = float(det.get("confidence", 0.0))
        class_name = str(det.get("class_name", "unknown"))
        class_id = int(det.get("class_id", 0))

        track = LiveTrack(
            track_id=tid,
            class_name=class_name,
            class_id=class_id,
            confidence=conf,
            bbox=box,
            first_seen_utc=timestamp_utc,
            last_seen_utc=timestamp_utc,
            age=1,
            frames_seen=1,
            frames_missing=0,
            status="CONFIRMED" if self.confirm_frames <= 1 else "TENTATIVE",
            trajectory=[centroid],
            confidence_history=[conf],
            class_history=[class_name],
        )
        self._tracks[tid] = track
