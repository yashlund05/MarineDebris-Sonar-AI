"""Temporal Confirmation and Class Consistency Engine.

Enforces N-of-M temporal confirmation gating and multi-frame class evidence voting
to suppress acoustic false alarms and flickering class predictions.
Conforms to Requirements R2 §21, §22, §23 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

from collections import Counter
from typing import List, Optional, Tuple
from backend.live_sonar.pipeline.tracker import LiveTrack


class TemporalConfirmationFilter:
    """Manages temporal confirmation and class consistency for live sonar tracks."""

    def __init__(
        self,
        min_confirmed_frames: int = 3,
        window_size: int = 5,
        min_track_age: int = 3,
        confidence_threshold: float = 0.35,
    ) -> None:
        self.min_confirmed_frames = min_confirmed_frames
        self.window_size = window_size
        self.min_track_age = min_track_age
        self.confidence_threshold = confidence_threshold

    def evaluate_track(self, track: LiveTrack) -> str:
        """Evaluate if track meets temporal confirmation gating.

        Returns status: "CONFIRMED" or "TENTATIVE".
        """
        # Rule: Must have been seen for at least min_confirmed_frames
        # and age >= min_track_age
        if (
            track.frames_seen >= self.min_confirmed_frames
            and track.age >= self.min_track_age
            and track.confidence >= self.confidence_threshold
        ):
            return "CONFIRMED"
        return "TENTATIVE"

    def smooth_class(self, track: LiveTrack) -> str:
        """Compute most consistent class name using majority vote over history."""
        if not track.class_history:
            return track.class_name

        # Consider recent observations (up to window_size * 2)
        recent = track.class_history[-10:]
        counts = Counter(recent)
        most_common, _ = counts.most_common(1)[0]
        return most_common

    def smooth_confidence(self, track: LiveTrack, alpha: float = 0.6) -> float:
        """Compute exponentially smoothed confidence score."""
        if not track.confidence_history:
            return track.confidence

        ema = track.confidence_history[0]
        for c in track.confidence_history[1:]:
            ema = alpha * c + (1 - alpha) * ema
        return round(float(ema), 4)

    def apply(self, tracks: List[LiveTrack]) -> List[LiveTrack]:
        """Apply confirmation gating, class smoothing, and confidence smoothing to all tracks."""
        for t in tracks:
            t.status = self.evaluate_track(t)
            t.class_name = self.smooth_class(t)
            t.confidence = self.smooth_confidence(t)
        return tracks
