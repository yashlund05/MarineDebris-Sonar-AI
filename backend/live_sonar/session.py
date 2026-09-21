"""LiveSonarSession: Lifecycle manager for live sonar streaming sessions.

Manages state transitions (CONNECTING, CONNECTED, RUNNING, DEGRADED, STOPPING, STOPPED, ERROR),
asynchronous frame ingestion, frame buffer management, and backpressure degradation detection.
Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import RTSPStreamAdapter
from backend.live_sonar.adapters.usb import USBCameraStreamAdapter
from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    LiveSonarSessionConfig,
    LiveSonarSourceInvalidError,
    LiveSonarStateError,
    SessionStatus,
    StreamMetrics,
)

logger = logging.getLogger(__name__)


def create_adapter(config: LiveSonarSessionConfig) -> SonarStreamAdapter:
    """Instantiate appropriate SonarStreamAdapter for the specified source type."""
    st = config.source_type.lower().strip()
    if st in ("replay", "demo"):
        return ReplayStreamAdapter(
            source_uri=config.source_uri or "demo",
            target_fps=config.target_fps,
            loop=getattr(config, "loop", True),
            session_id=config.session_id,
        )
    elif st in ("rtsp", "rtsps"):
        return RTSPStreamAdapter(
            source_uri=config.source_uri,
            target_fps=config.target_fps,
            session_id=config.session_id,
        )
    elif st in ("usb", "camera", "device"):
        return USBCameraStreamAdapter(
            source_uri=config.source_uri,
            target_fps=config.target_fps,
            session_id=config.session_id,
        )
    elif st in ("native_stub", "native", "aris"):
        return NativeSonarStubAdapter(
            source_uri=config.source_uri or "native://aris3000",
            target_fps=config.target_fps,
            session_id=config.session_id,
        )
    else:
        raise LiveSonarSourceInvalidError(
            f"Unsupported sonar source type '{config.source_type}'. "
            "Must be one of: 'replay', 'rtsp', 'usb', 'native_stub'."
        )


class LiveSonarSession:
    """Manages the lifecycle of a single live acoustic acquisition session."""

    def __init__(
        self,
        config: LiveSonarSessionConfig,
        adapter: Optional[SonarStreamAdapter] = None,
        buffer: Optional[FrameBuffer] = None,
    ) -> None:
        self.config = config
        self.session_id = config.session_id
        self.adapter = adapter if adapter is not None else create_adapter(config)
        self.buffer = (
            buffer
            if buffer is not None
            else FrameBuffer(
                maxsize=config.buffer_size,
                policy=config.drop_policy,
            )
        )

        self._status: SessionStatus = SessionStatus.CONNECTING
        self._error_message: Optional[str] = None
        self._started_at: Optional[datetime] = None
        self._stopped_at: Optional[datetime] = None

        self._ingestion_task: Optional[asyncio.Task] = None
        self._status_lock = asyncio.Lock()

    @property
    def status(self) -> SessionStatus:
        return self._status

    @property
    def error_message(self) -> Optional[str]:
        return self._error_message

    @property
    def started_at(self) -> Optional[datetime]:
        return self._started_at

    @property
    def stopped_at(self) -> Optional[datetime]:
        return self._stopped_at

    async def start(self) -> None:
        """Start acquisition: transition CONNECTING -> CONNECTED -> RUNNING."""
        async with self._status_lock:
            if self._status in (SessionStatus.RUNNING, SessionStatus.DEGRADED):
                raise LiveSonarStateError(f"Session {self.session_id} is already active")
            if self._status == SessionStatus.STOPPING:
                raise LiveSonarStateError(f"Session {self.session_id} is stopping")

            self._status = SessionStatus.CONNECTING
            self._error_message = None

        try:
            await self.adapter.connect()
            async with self._status_lock:
                self._status = SessionStatus.CONNECTED

            # Launch background frame ingestion task
            self._ingestion_task = asyncio.create_task(
                self._ingestion_loop(),
                name=f"live-sonar-ingest-{self.session_id}",
            )
            async with self._status_lock:
                self._status = SessionStatus.RUNNING
                self._started_at = datetime.now(timezone.utc)
            logger.info(f"LiveSonarSession {self.session_id} started successfully.")

        except Exception as exc:
            async with self._status_lock:
                self._status = SessionStatus.ERROR
                self._error_message = str(exc)
            logger.error(f"LiveSonarSession {self.session_id} failed to start: {exc}")
            raise

    async def _ingestion_loop(self) -> None:
        """Continuously consume from source adapter and feed bounded buffer."""
        try:
            async for frame in self.adapter.frames():
                if self._status in (SessionStatus.STOPPING, SessionStatus.STOPPED):
                    break

                # Enqueue frame
                await self.buffer.put(frame)

                # Check for backpressure degradation
                metrics = self.buffer.get_metrics()
                capacity = self.buffer.maxsize
                q_depth = metrics.queue_depth

                if q_depth >= int(0.8 * capacity) and metrics.input_fps > metrics.processing_fps:
                    if self._status == SessionStatus.RUNNING:
                        async with self._status_lock:
                            self._status = SessionStatus.DEGRADED
                elif self._status == SessionStatus.DEGRADED and q_depth <= int(0.4 * capacity):
                    async with self._status_lock:
                        self._status = SessionStatus.RUNNING

            # Stream finished naturally (e.g. EOF in replay without loop)
            if self._status not in (SessionStatus.STOPPING, SessionStatus.STOPPED):
                async with self._status_lock:
                    self._status = SessionStatus.STOPPED
                    self._stopped_at = datetime.now(timezone.utc)
                await self.adapter.disconnect()
                await self.buffer.close()

        except asyncio.CancelledError:
            # Clean task cancellation
            pass
        except Exception as exc:
            logger.error(f"Error in ingestion loop for session {self.session_id}: {exc}")
            async with self._status_lock:
                self._status = SessionStatus.ERROR
                self._error_message = str(exc)

    async def stop(self) -> None:
        """Stop ingestion cleanly: transition STOPPING -> STOPPED."""
        async with self._status_lock:
            if self._status == SessionStatus.STOPPED:
                return
            self._status = SessionStatus.STOPPING

        # Cancel ingestion task
        if self._ingestion_task is not None and not self._ingestion_task.done():
            self._ingestion_task.cancel()
            try:
                await self._ingestion_task
            except asyncio.CancelledError:
                pass
            self._ingestion_task = None

        # Disconnect source adapter
        try:
            await self.adapter.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting adapter for session {self.session_id}: {e}")

        # Close buffer
        try:
            await self.buffer.close()
        except Exception as e:
            logger.warning(f"Error closing buffer for session {self.session_id}: {e}")

        async with self._status_lock:
            self._status = SessionStatus.STOPPED
            self._stopped_at = datetime.now(timezone.utc)
        logger.info(f"LiveSonarSession {self.session_id} stopped cleanly.")

    async def pause(self) -> None:
        """Pause replay playback if supported by adapter."""
        if hasattr(self.adapter, "pause"):
            self.adapter.pause()

    async def resume(self) -> None:
        """Resume replay playback if supported by adapter."""
        if hasattr(self.adapter, "resume"):
            self.adapter.resume()

    def get_metrics(self) -> StreamMetrics:
        """Return real-time stream throughput and backpressure metrics."""
        return self.buffer.get_metrics()
