"""Session Recording Engine for Live Sonar Streams.

Records incoming acoustic frames, telemetry, and live detection events
to local storage using structured video/JSONL conventions.
Conforms to Requirement R5 §36 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import cv2
import numpy as np

from backend.config import get_settings
from backend.live_sonar.models import SonarFrame

logger = logging.getLogger(__name__)


class SessionRecorder:
    """Records an active live sonar session to persistent disk storage."""

    def __init__(self, session_id: str, output_base_dir: Optional[str] = None) -> None:
        self.session_id = session_id
        settings = get_settings()
        base_dir = Path(output_base_dir or getattr(settings, "STORAGE_LOCAL_PATH", "data/storage"))
        self.record_dir = base_dir / "recordings" / f"session_{session_id}"
        self.record_dir.mkdir(parents=True, exist_ok=True)

        self._is_recording = False
        self._frames_written = 0
        self._log_file = None
        self._video_writer = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def start(self, width: int = 640, height: int = 480, fps: float = 15.0) -> None:
        """Initialize video container and metadata JSONL log."""
        if self._is_recording:
            return

        video_path = self.record_dir / "stream_raw.mp4"
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self._video_writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height), isColor=False)

        log_path = self.record_dir / "telemetry_events.jsonl"
        self._log_file = open(log_path, "a", encoding="utf-8")
        self._is_recording = True
        self._frames_written = 0
        logger.info(f"SessionRecorder started for session {self.session_id} at {self.record_dir}")

    def write_frame(
        self,
        frame: SonarFrame,
        detections: Optional[list] = None,
        tracks: Optional[list] = None,
    ) -> None:
        """Append a frame to the video stream and write its telemetry event record."""
        if not self._is_recording:
            return

        try:
            # Write to video if writer is open and image matches
            if self._video_writer is not None and frame.image_data.size > 0:
                img = frame.image_data
                if img.ndim == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                self._video_writer.write(img)
                self._frames_written += 1

            # Append telemetry & detection JSONL record
            if self._log_file is not None:
                record = {
                    "sequence_number": frame.sequence_number,
                    "frame_id": frame.frame_id,
                    "timestamp_utc": frame.timestamp_utc.isoformat(),
                    "telemetry": {
                        "frequency_hz": frame.sonar_metadata.frequency_hz if frame.sonar_metadata else None,
                        "range_m": frame.sonar_metadata.range_m if frame.sonar_metadata else None,
                        "gain_db": frame.sonar_metadata.gain_db if frame.sonar_metadata else None,
                    },
                    "navigation": {
                        "latitude": frame.navigation.latitude if frame.navigation else None,
                        "longitude": frame.navigation.longitude if frame.navigation else None,
                        "depth_m": frame.navigation.depth_m if frame.navigation else None,
                    },
                    "detections_count": len(detections or []),
                    "active_tracks_count": len(tracks or []),
                }
                self._log_file.write(json.dumps(record) + "\n")
                self._log_file.flush()

        except Exception as e:
            logger.error(f"Error recording frame {frame.sequence_number}: {e}")

    def stop(self) -> Dict[str, Any]:
        """Finalize video writer and close log file."""
        if not self._is_recording:
            return {"status": "NOT_RECORDING", "frames_written": 0}

        self._is_recording = False
        if self._video_writer is not None:
            self._video_writer.release()
            self._video_writer = None

        if self._log_file is not None:
            self._log_file.close()
            self._log_file = None

        logger.info(f"SessionRecorder stopped. Recorded {self._frames_written} frames.")
        return {
            "status": "STOPPED",
            "session_id": self.session_id,
            "recording_dir": str(self.record_dir).replace("\\", "/"),
            "frames_written": self._frames_written,
        }
