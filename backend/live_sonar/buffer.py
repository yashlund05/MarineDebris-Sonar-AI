"""Bounded async FrameBuffer with configurable drop policies and backpressure metrics.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import asyncio
import collections
import time
from datetime import datetime, timezone
from typing import Deque, Optional, Tuple

from backend.live_sonar.models import (
    DropPolicy,
    SonarFrame,
    StreamMetrics,
)


class FrameBuffer:
    """Bounded async frame queue with drop policies and backpressure tracking."""

    def __init__(
        self,
        maxsize: int = 60,
        policy: DropPolicy = DropPolicy.DROP_OLDEST,
    ) -> None:
        if maxsize <= 0:
            raise ValueError("Buffer maxsize must be greater than 0")

        self.maxsize = maxsize
        self.policy = policy
        self._effective_maxsize = 1 if policy == DropPolicy.LATEST else maxsize

        self._queue: Deque[SonarFrame] = collections.deque()
        self._lock = asyncio.Lock()
        self._has_items = asyncio.Condition(self._lock)
        self._has_space = asyncio.Condition(self._lock)
        self._closed = False

        # Monotonic lifetime counters
        self._frames_received: int = 0
        self._frames_processed: int = 0
        self._frames_dropped: int = 0
        self._start_time: float = time.monotonic()

        # Rolling window history for metrics calculation: (timestamp, count)
        # Windows stored as deque of (monotonic_time_sec, value)
        self._received_timestamps: Deque[float] = collections.deque(maxlen=10000)
        self._processed_timestamps: Deque[float] = collections.deque(maxlen=10000)
        self._dropped_timestamps: Deque[float] = collections.deque(maxlen=10000)
        self._recent_latencies_ms: Deque[float] = collections.deque(maxlen=60)
        self._window_sec: float = 5.0

    @property
    def frames_received(self) -> int:
        return self._frames_received

    @property
    def frames_processed(self) -> int:
        return self._frames_processed

    @property
    def frames_dropped(self) -> int:
        return self._frames_dropped

    @property
    def queue_depth(self) -> int:
        return len(self._queue)

    def qsize(self) -> int:
        """Return the current number of frames in buffer."""
        return len(self._queue)

    def empty(self) -> bool:
        """Return True if the buffer is empty."""
        return len(self._queue) == 0

    def full(self) -> bool:
        """Return True if the buffer has reached maximum capacity."""
        return len(self._queue) >= self._effective_maxsize

    async def put(self, frame: SonarFrame) -> None:
        """Add a SonarFrame to the buffer adhering to configured DropPolicy."""
        async with self._has_space:
            if self._closed:
                raise RuntimeError("FrameBuffer is closed")

            now = time.monotonic()
            self._frames_received += 1
            self._received_timestamps.append(now)
            self._prune_windows(now - self._window_sec)

            if self.policy == DropPolicy.FIFO:
                # Block until space is available
                while len(self._queue) >= self._effective_maxsize and not self._closed:
                    await self._has_space.wait()
                if self._closed:
                    raise RuntimeError("FrameBuffer is closed")
                self._queue.append(frame)
                self._has_items.notify()

            elif self.policy == DropPolicy.DROP_OLDEST:
                # Discard oldest frame if full to prioritize low latency
                if len(self._queue) >= self._effective_maxsize:
                    _ = self._queue.popleft()
                    self._frames_dropped += 1
                    self._dropped_timestamps.append(now)
                self._queue.append(frame)
                self._has_items.notify()

            elif self.policy == DropPolicy.DROP_NEWEST:
                # Reject incoming frame if full
                if len(self._queue) >= self._effective_maxsize:
                    self._frames_dropped += 1
                    self._dropped_timestamps.append(now)
                else:
                    self._queue.append(frame)
                    self._has_items.notify()

            elif self.policy == DropPolicy.LATEST:
                # Capacity 1: discard previous frame if present
                if len(self._queue) >= 1:
                    _ = self._queue.popleft()
                    self._frames_dropped += 1
                    self._dropped_timestamps.append(now)
                self._queue.append(frame)
                self._has_items.notify()

    def put_nowait(self, frame: SonarFrame) -> None:
        """Synchronous/non-blocking put into buffer adhering to DropPolicy."""
        if self._closed:
            raise RuntimeError("FrameBuffer is closed")

        now = time.monotonic()
        self._frames_received += 1
        self._received_timestamps.append(now)
        self._prune_windows(now - self._window_sec)

        if self.policy == DropPolicy.FIFO:
            if len(self._queue) >= self._effective_maxsize:
                raise asyncio.QueueFull("Buffer is full under FIFO policy")
            self._queue.append(frame)
            self._notify_items_safely()

        elif self.policy == DropPolicy.DROP_OLDEST:
            if len(self._queue) >= self._effective_maxsize:
                _ = self._queue.popleft()
                self._frames_dropped += 1
                self._dropped_timestamps.append(now)
            self._queue.append(frame)
            self._notify_items_safely()

        elif self.policy == DropPolicy.DROP_NEWEST:
            if len(self._queue) >= self._effective_maxsize:
                self._frames_dropped += 1
                self._dropped_timestamps.append(now)
            else:
                self._queue.append(frame)
                self._notify_items_safely()

        elif self.policy == DropPolicy.LATEST:
            if len(self._queue) >= 1:
                _ = self._queue.popleft()
                self._frames_dropped += 1
                self._dropped_timestamps.append(now)
            self._queue.append(frame)
            self._notify_items_safely()

    async def get(self) -> SonarFrame:
        """Retrieve and remove a frame from the buffer, waiting if empty."""
        async with self._has_items:
            while not self._queue and not self._closed:
                await self._has_items.wait()

            if self._closed and not self._queue:
                raise asyncio.QueueEmpty("FrameBuffer is closed and empty")

            frame = self._queue.popleft()
            self._record_get_metrics(frame)
            self._has_space.notify()
            return frame

    def get_nowait(self) -> SonarFrame:
        """Retrieve and remove a frame immediately or raise QueueEmpty."""
        if not self._queue:
            raise asyncio.QueueEmpty("FrameBuffer is empty")

        frame = self._queue.popleft()
        self._record_get_metrics(frame)
        return frame

    def _record_get_metrics(self, frame: SonarFrame) -> None:
        now = time.monotonic()
        self._frames_processed += 1
        self._processed_timestamps.append(now)
        self._prune_windows(now - self._window_sec)

        # Compute arrival to dispatch latency if timestamp is present
        if frame.timestamp_utc:
            now_utc = datetime.now(timezone.utc)
            delta_ms = max(0.0, (now_utc - frame.timestamp_utc).total_seconds() * 1000.0)
            self._recent_latencies_ms.append(delta_ms)

    def _prune_windows(self, cutoff: float) -> None:
        while self._received_timestamps and self._received_timestamps[0] < cutoff:
            self._received_timestamps.popleft()
        while self._processed_timestamps and self._processed_timestamps[0] < cutoff:
            self._processed_timestamps.popleft()
        while self._dropped_timestamps and self._dropped_timestamps[0] < cutoff:
            self._dropped_timestamps.popleft()

    def get_metrics(self) -> StreamMetrics:
        """Calculate and return real-time sliding-window backpressure telemetry."""
        now = time.monotonic()
        cutoff = now - self._window_sec
        self._prune_windows(cutoff)

        elapsed = max(0.001, now - self._start_time)
        window_duration = max(0.1, min(self._window_sec, elapsed))
        input_fps = round(len(self._received_timestamps) / window_duration, 2)
        processing_fps = round(len(self._processed_timestamps) / window_duration, 2)

        dropped_in_window = len(self._dropped_timestamps)
        total_in_window = len(self._received_timestamps)
        drop_rate = (
            round(dropped_in_window / total_in_window, 4) if total_in_window > 0 else 0.0
        )

        avg_latency_ms = (
            round(sum(self._recent_latencies_ms) / len(self._recent_latencies_ms), 2)
            if self._recent_latencies_ms
            else 0.0
        )

        return StreamMetrics(
            input_fps=input_fps,
            inference_fps=processing_fps,
            display_fps=processing_fps,
            processing_fps=processing_fps,
            effective_fps=processing_fps,
            latency_ms=avg_latency_ms,
            queue_depth=len(self._queue),
            frames_received=self._frames_received,
            frames_processed=self._frames_processed,
            frames_dropped=self._frames_dropped,
            drop_rate=drop_rate,
            active_tracks_count=0,
            confirmed_targets_count=0,
        )

    def _notify_items_safely(self) -> None:
        """Safely notify _has_items without lock crash in synchronous contexts."""
        if not self._lock.locked():
            self._lock._locked = True
            try:
                self._has_items.notify()
            finally:
                self._lock._locked = False
        else:
            try:
                self._has_items.notify()
            except RuntimeError:
                waiters = getattr(self._has_items, "_waiters", None)
                if waiters:
                    for fut in list(waiters):
                        if not fut.done():
                            fut.set_result(False)
                            break

    def _notify_space_safely(self) -> None:
        """Safely notify _has_space in synchronous context without lock crash."""
        if not self._lock.locked():
            self._lock._locked = True
            try:
                self._has_space.notify_all()
            finally:
                self._lock._locked = False
        else:
            try:
                self._has_space.notify_all()
            except RuntimeError:
                waiters = getattr(self._has_space, "_waiters", None)
                if waiters:
                    for fut in list(waiters):
                        if not fut.done():
                            fut.set_result(False)

    def clear(self) -> None:
        """Clear all queued frames without closing the buffer."""
        self._queue.clear()
        self._notify_space_safely()

    async def aclear(self) -> None:
        """Asynchronously clear all queued frames and notify waiting producers."""
        async with self._lock:
            self._queue.clear()
            self._has_space.notify_all()

    async def close(self) -> None:
        """Signal buffer closure and wake all waiting tasks."""
        async with self._lock:
            self._closed = True
            self._has_items.notify_all()
            self._has_space.notify_all()
