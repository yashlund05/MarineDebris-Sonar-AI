"""ReplayStreamAdapter: High-fidelity replay of sonar images, sequences, video files, and synthetic feeds.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

import cv2
import numpy as np

from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.models import (
    LiveNavigationData,
    LiveSonarSourceInvalidError,
    LiveSonarTelemetry,
    QualityFlags,
    SonarFrame,
    SonarStreamMetadata,
    StreamHealth,
)


class ReplayStreamAdapter(SonarStreamAdapter):
    """Replays video files (.mp4/.avi/.mkv), image sequences (.png/.jpg), or synthetic sonar streams."""

    VALID_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
    VALID_VIDEO_EXTS = {".mp4", ".avi", ".mkv", ".mov"}

    def __init__(
        self,
        source_uri: str,
        target_fps: float = 15.0,
        loop: bool = False,
        speed_multiplier: float = 1.0,
        session_id: str = "",
    ) -> None:
        self.source_uri = source_uri
        self.target_fps = max(0.1, target_fps)
        self.loop = loop
        self.speed_multiplier = max(0.1, speed_multiplier)
        self.session_id = session_id

        self._connected: bool = False
        self._is_paused: bool = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()

        self._current_index: int = 0
        self._total_frames: int = 0
        self._mode: str = "none"  # "image_sequence" | "video" | "synthetic"
        self._image_files: List[Path] = []
        self._video_cap: Optional[cv2.VideoCapture] = None
        self._manifest_metadata: Dict[str, Any] = {}
        self._resolved_path: Optional[Path] = None

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def is_paused(self) -> bool:
        return self._is_paused

    def pause(self) -> None:
        """Pause playback."""
        self._is_paused = True
        self._pause_event.clear()

    def resume(self) -> None:
        """Resume playback."""
        self._is_paused = False
        self._pause_event.set()

    def seek(self, frame_index: int) -> None:
        """Seek to a target frame index."""
        if frame_index < 0:
            frame_index = 0
        if self._total_frames > 0 and frame_index >= self._total_frames:
            frame_index = self._total_frames - 1

        self._current_index = frame_index
        if self._mode == "video" and self._video_cap is not None:
            self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

    def set_speed(self, multiplier: float) -> None:
        """Set speed playback multiplier (e.g. 0.25, 0.5, 1.0, 2.0, 4.0)."""
        self.speed_multiplier = max(0.1, multiplier)

    async def connect(self) -> None:
        """Connect to the replay source and validate availability."""
        if not self.source_uri or not self.source_uri.strip():
            raise LiveSonarSourceInvalidError("Source URI cannot be empty or whitespace.")

        # Check for demo video shortcuts
        clean_uri = self.source_uri.strip().lower()
        if clean_uri in ("demo", "demo://", "default", "aris3k", "demo_video"):
            candidate = Path.cwd() / "tests" / "fixtures" / "live_sonar" / "aris3k_replay_stream.mp4"
            if not candidate.exists():
                from tests.fixtures.live_sonar.replay_feed import build_replay_video
                candidate = build_replay_video()
            self.source_uri = str(candidate)
            self.loop = True

        # Check for synthetic stream mode
        if self.source_uri.startswith("synthetic://") or self.source_uri == "synthetic":
            self._mode = "synthetic"
            self._total_frames = 1000
            self._connected = True
            return

        # Path traversal guard: block illegal sequences
        if ".." in self.source_uri and not os.path.isabs(self.source_uri):
            # Check normalized path
            norm = os.path.normpath(self.source_uri)
            if norm.startswith(".."):
                raise LiveSonarSourceInvalidError(
                    f"Path traversal detected in source URI: '{self.source_uri}'"
                )

        raw_path = Path(self.source_uri)
        # Check relative to cwd or absolute
        if not raw_path.is_absolute():
            resolved = Path.cwd() / raw_path
        else:
            resolved = raw_path

        if not resolved.exists():
            raise LiveSonarSourceInvalidError(
                f"Replay source path does not exist: '{self.source_uri}'"
            )

        self._resolved_path = resolved

        if resolved.is_dir():
            # Collect images
            images = [
                p for p in resolved.iterdir()
                if p.is_file() and p.suffix.lower() in self.VALID_IMAGE_EXTS
            ]
            images.sort(key=lambda p: p.name)
            if not images:
                raise LiveSonarSourceInvalidError(
                    f"Directory '{self.source_uri}' contains no supported sonar image files"
                )
            self._image_files = images
            self._total_frames = len(images)
            self._mode = "image_sequence"

            # Check for manifest sidecar
            manifest_file = resolved / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        self._manifest_metadata = json.load(f)
                except Exception:
                    self._manifest_metadata = {}

        elif resolved.is_file():
            suffix = resolved.suffix.lower()
            if suffix in self.VALID_VIDEO_EXTS:
                self._mode = "video"
                cap = cv2.VideoCapture(str(resolved))
                if not cap.isOpened():
                    raise LiveSonarSourceInvalidError(
                        f"Failed to open video file '{self.source_uri}'"
                    )
                self._video_cap = cap
                self._total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            elif suffix in self.VALID_IMAGE_EXTS:
                self._mode = "image_sequence"
                self._image_files = [resolved]
                self._total_frames = 1
            else:
                raise LiveSonarSourceInvalidError(
                    f"Unsupported replay file format '{suffix}' for source '{self.source_uri}'"
                )
        else:
            raise LiveSonarSourceInvalidError(
                f"Source path '{self.source_uri}' is neither a file nor a directory"
            )

        self._connected = True

    async def disconnect(self) -> None:
        """Cleanly release open file handles and video captures."""
        self._connected = False
        if self._video_cap is not None:
            self._video_cap.release()
            self._video_cap = None
        self._pause_event.set()

    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield paced SonarFrame instances from the replay source."""
        if not self._connected:
            raise RuntimeError("Adapter is not connected. Call connect() first.")

        seq_num = 0
        while self._connected:
            # Handle pause
            await self._pause_event.wait()
            if not self._connected:
                break

            loop_start = time.monotonic()
            frame_array: Optional[np.ndarray] = None
            metadata_telemetry = LiveSonarTelemetry()
            navigation_data = LiveNavigationData()
            source_meta: Dict[str, Any] = {
                "source_type": "replay",
                "source_uri": self.source_uri,
                "frame_index": self._current_index,
            }

            if self._mode == "image_sequence":
                if self._current_index >= len(self._image_files):
                    if self.loop:
                        self._current_index = 0
                    else:
                        break

                img_path = self._image_files[self._current_index]
                source_meta["filename"] = img_path.name

                # Guard against 0-byte or missing corrupt image files before cv2.imread
                try:
                    if not img_path.exists() or img_path.stat().st_size == 0:
                        self._current_index += 1
                        continue
                except OSError:
                    self._current_index += 1
                    continue

                # Read image
                img = cv2.imread(str(img_path), cv2.IMREAD_UNCHANGED)
                if img is None:
                    # Skip corrupt frame
                    self._current_index += 1
                    continue

                if len(img.shape) == 3 and img.shape[2] >= 3:
                    frame_array = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                else:
                    frame_array = img

                # Check if manifest metadata has sidecar entry for this image
                if self._manifest_metadata:
                    target_entry = None
                    if isinstance(self._manifest_metadata, list):
                        for entry in self._manifest_metadata:
                            if entry.get("filename") == img_path.name or entry.get("image") == img_path.name:
                                target_entry = entry
                                break
                    elif isinstance(self._manifest_metadata, dict):
                        target_entry = self._manifest_metadata.get(img_path.name)

                    if target_entry:
                        source_meta["manifest"] = target_entry

                self._current_index += 1

            elif self._mode == "video":
                if self._video_cap is None or not self._video_cap.isOpened():
                    break

                ret, bgr_frame = self._video_cap.read()
                if not ret:
                    if self.loop:
                        self._video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        self._current_index = 0
                        continue
                    else:
                        break

                frame_array = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
                self._current_index += 1

            elif self._mode == "synthetic":
                if self._current_index >= self._total_frames:
                    if self.loop:
                        self._current_index = 0
                    else:
                        break

                # Generate synthetic acoustic sector with reverberation noise
                h, w = 512, 640
                t = self._current_index * 0.1
                base_noise = np.random.rayleigh(scale=20.0, size=(h, w)).astype(np.float32)
                # Inject a synthetic moving acoustic highlight
                cx = int((w / 2) + 150 * np.sin(t))
                cy = int((h / 2) + 80 * np.cos(t))
                cv2.circle(base_noise, (cx, cy), 18, 220, -1)
                # Add acoustic shadow behind the highlight (down-range)
                cv2.rectangle(base_noise, (cx - 16, cy + 18), (cx + 16, cy + 65), 15, -1)
                frame_array = np.clip(base_noise, 0, 255).astype(np.uint8)

                metadata_telemetry = LiveSonarTelemetry(
                    frequency_hz=1200000.0,
                    range_m=30.0,
                    gain_db=18.0,
                    beam_angle_deg=28.0,
                    heading_deg=180.0,
                    depth_m=12.5,
                    sound_speed_mps=1500.0,
                )
                self._current_index += 1

            if frame_array is None:
                continue

            frame = SonarFrame(
                session_id=self.session_id,
                sequence_number=seq_num,
                timestamp_utc=datetime.now(timezone.utc),
                source_type="replay",
                source_uri=self.source_uri,
                source_metadata=source_meta,
                image_data=frame_array,
                sonar_metadata=metadata_telemetry,
                navigation=navigation_data,
                quality_flags=QualityFlags(
                    is_dropout=False,
                    motion_quality_score=0.95,
                    is_degraded=False,
                ),
            )
            seq_num += 1
            yield frame

            # Frame pacing
            effective_fps = self.target_fps * self.speed_multiplier
            delay = (1.0 / effective_fps) - (time.monotonic() - loop_start)
            if delay > 0:
                await asyncio.sleep(delay)

    async def health(self) -> StreamHealth:
        """Return real-time health telemetry."""
        if not self._connected:
            return StreamHealth(
                status="DISCONNECTED",
                details="Replay adapter is not connected",
                source_uri=self.source_uri,
            )
        return StreamHealth(
            status="OK",
            details=f"Playing {self._mode} ({self._current_index}/{self._total_frames} frames)",
            source_uri=self.source_uri,
        )

    async def metadata(self) -> SonarStreamMetadata:
        """Return stream metadata."""
        w, h = None, None
        if self._mode == "image_sequence" and self._image_files:
            try:
                sample = cv2.imread(str(self._image_files[0]), cv2.IMREAD_UNCHANGED)
                if sample is not None:
                    h, w = sample.shape[:2]
            except Exception:
                pass
        elif self._mode == "video" and self._video_cap is not None:
            w = int(self._video_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._video_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        elif self._mode == "synthetic":
            w, h = 640, 512

        return SonarStreamMetadata(
            source_type="replay",
            source_uri=self.source_uri,
            width=w,
            height=h,
            fps=self.target_fps,
            total_frames=self._total_frames,
            is_live=False,
            extra={
                "loop": self.loop,
                "mode": self._mode,
                "speed_multiplier": self.speed_multiplier,
            },
        )
