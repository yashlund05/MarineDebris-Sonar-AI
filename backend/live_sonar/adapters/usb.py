"""USBCameraStreamAdapter: Local capture card and USB sonar interface.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import asyncio
import platform
import time
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

import cv2
import numpy as np

from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.models import (
    LiveNavigationData,
    LiveSonarSourceConnectionError,
    LiveSonarSourceInvalidError,
    LiveSonarTelemetry,
    QualityFlags,
    SonarFrame,
    SonarStreamMetadata,
    StreamHealth,
)


class USBCameraStreamAdapter(SonarStreamAdapter):
    """Captures frames from USB capture cards or local video devices."""

    def __init__(
        self,
        source_uri: str,
        target_fps: float = 15.0,
        session_id: str = "",
    ) -> None:
        self.source_uri = source_uri
        self.target_fps = max(0.1, target_fps)
        self.session_id = session_id

        self.device_index: int = self._parse_device_index(source_uri)
        self._connected: bool = False
        self._cap: Optional[cv2.VideoCapture] = None
        self._health_status: str = "DISCONNECTED"
        self._health_details: str = "Adapter initialized"

    def _parse_device_index(self, uri: str) -> int:
        """Extract device integer index from device://<idx> or raw int string."""
        clean = uri.strip()
        if clean.startswith("device://"):
            idx_str = clean[len("device://"):]
        elif clean.startswith("usb://"):
            idx_str = clean[len("usb://"):]
        else:
            idx_str = clean

        try:
            idx = int(idx_str)
            if idx < 0:
                raise ValueError()
            return idx
        except Exception:
            raise LiveSonarSourceInvalidError(
                f"Invalid USB device URI '{uri}'. Expected format 'device://0' or integer."
            )

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Connect to the camera device."""
        self._health_status = "CONNECTING"
        self._health_details = f"Opening device index {self.device_index}"

        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_V4L2
        cap = await asyncio.to_thread(cv2.VideoCapture, self.device_index, backend)

        if not cap.isOpened():
            cap.release()
            self._health_status = "ERROR"
            self._health_details = f"Device index {self.device_index} not found or occupied"
            raise LiveSonarSourceConnectionError(
                f"Failed to open USB capture device at index {self.device_index} (device not found or busy)"
            )

        self._cap = cap
        self._connected = True
        self._health_status = "OK"
        self._health_details = f"Connected to USB device {self.device_index}"

    async def disconnect(self) -> None:
        """Release device handle."""
        self._connected = False
        self._health_status = "DISCONNECTED"
        self._health_details = "Disconnected by user"

        if self._cap is not None:
            await asyncio.to_thread(self._cap.release)
            self._cap = None

    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield frames captured from the USB device."""
        if not self._connected:
            raise RuntimeError("Adapter is not connected. Call connect() first.")

        seq_num = 0
        frame_interval = 1.0 / self.target_fps

        while self._connected:
            loop_start = time.monotonic()

            ret, bgr_frame = await asyncio.to_thread(self._read_frame)
            if not ret or bgr_frame is None:
                self._connected = False
                self._health_status = "ERROR"
                self._health_details = f"Device index {self.device_index} disconnected during active capture"
                break

            if len(bgr_frame.shape) == 3 and bgr_frame.shape[2] >= 3:
                frame_gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            else:
                frame_gray = bgr_frame

            frame = SonarFrame(
                session_id=self.session_id,
                sequence_number=seq_num,
                timestamp_utc=datetime.now(timezone.utc),
                source_type="usb",
                source_uri=self.source_uri,
                source_metadata={"device_index": self.device_index},
                image_data=frame_gray,
                sonar_metadata=LiveSonarTelemetry(),
                navigation=LiveNavigationData(),
                quality_flags=QualityFlags(
                    is_dropout=False,
                    motion_quality_score=0.9,
                    is_degraded=False,
                ),
            )
            seq_num += 1
            yield frame

            delay = frame_interval - (time.monotonic() - loop_start)
            if delay > 0:
                await asyncio.sleep(delay)

    def _read_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        if self._cap is None or not self._cap.isOpened():
            return False, None
        try:
            return self._cap.read()
        except Exception:
            return False, None

    async def health(self) -> StreamHealth:
        return StreamHealth(
            status=self._health_status,
            details=self._health_details,
            source_uri=self.source_uri,
            reconnect_attempts=0,
        )

    async def metadata(self) -> SonarStreamMetadata:
        w, h = None, None
        if self._cap is not None and self._cap.isOpened():
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return SonarStreamMetadata(
            source_type="usb",
            source_uri=self.source_uri,
            width=w,
            height=h,
            fps=self.target_fps,
            total_frames=None,
            is_live=True,
            extra={"device_index": self.device_index},
        )
