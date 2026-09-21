"""Unit tests for bounded async FrameBuffer and backpressure metrics.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

import asyncio
from datetime import datetime, timezone
import numpy as np
import pytest

from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    DropPolicy,
    LiveNavigationData,
    LiveSonarTelemetry,
    QualityFlags,
    SonarFrame,
)


def create_test_frame(seq: int = 0) -> SonarFrame:
    """Helper to generate a lightweight immutable SonarFrame for testing."""
    img = np.full((32, 32), fill_value=seq, dtype=np.uint8)
    return SonarFrame(
        frame_id=f"frame-{seq}",
        sequence_number=seq,
        timestamp_utc=datetime.now(timezone.utc),
        source_type="replay",
        source_uri="test://feed",
        image_data=img,
        sonar_metadata=LiveSonarTelemetry(frequency_hz=1200000.0, range_m=25.0),
        navigation=LiveNavigationData(latitude=38.8951, longitude=-77.0364),
        quality_flags=QualityFlags(is_dropout=False, motion_quality_score=1.0),
    )


def test_buffer_invalid_maxsize():
    with pytest.raises(ValueError, match="must be greater than 0"):
        FrameBuffer(maxsize=0)


def test_frame_immutability():
    frame = create_test_frame(1)
    assert not frame.image_data.flags.writeable
    with pytest.raises(ValueError, match="read-only"):
        frame.image_data[0, 0] = 255


@pytest.mark.asyncio
async def test_buffer_basic_put_get():
    buf = FrameBuffer(maxsize=5, policy=DropPolicy.DROP_OLDEST)
    assert buf.empty()
    assert not buf.full()
    assert buf.qsize() == 0

    frame = create_test_frame(10)
    await buf.put(frame)

    assert not buf.empty()
    assert buf.qsize() == 1
    assert buf.frames_received == 1

    out = await buf.get()
    assert out.frame_id == "frame-10"
    assert buf.frames_processed == 1
    assert buf.empty()


@pytest.mark.asyncio
async def test_buffer_policy_drop_oldest():
    buf = FrameBuffer(maxsize=3, policy=DropPolicy.DROP_OLDEST)

    for i in range(1, 6):
        await buf.put(create_test_frame(i))

    assert buf.qsize() == 3
    assert buf.frames_received == 5
    assert buf.frames_dropped == 2

    # Oldest frames 1 and 2 should have been dropped; 3, 4, 5 remain
    f3 = await buf.get()
    f4 = await buf.get()
    f5 = await buf.get()

    assert f3.sequence_number == 3
    assert f4.sequence_number == 4
    assert f5.sequence_number == 5


@pytest.mark.asyncio
async def test_buffer_policy_drop_newest():
    buf = FrameBuffer(maxsize=3, policy=DropPolicy.DROP_NEWEST)

    for i in range(1, 6):
        await buf.put(create_test_frame(i))

    assert buf.qsize() == 3
    assert buf.frames_received == 5
    assert buf.frames_dropped == 2

    # Newest frames 4 and 5 should have been discarded; 1, 2, 3 remain
    f1 = await buf.get()
    f2 = await buf.get()
    f3 = await buf.get()

    assert f1.sequence_number == 1
    assert f2.sequence_number == 2
    assert f3.sequence_number == 3


@pytest.mark.asyncio
async def test_buffer_policy_latest():
    # LATEST policy enforces capacity of 1
    buf = FrameBuffer(maxsize=5, policy=DropPolicy.LATEST)

    for i in range(1, 5):
        await buf.put(create_test_frame(i))

    assert buf.qsize() == 1
    assert buf.frames_received == 4
    assert buf.frames_dropped == 3

    latest = await buf.get()
    assert latest.sequence_number == 4
    assert buf.empty()


@pytest.mark.asyncio
async def test_buffer_policy_fifo_blocking():
    buf = FrameBuffer(maxsize=2, policy=DropPolicy.FIFO)

    await buf.put(create_test_frame(1))
    await buf.put(create_test_frame(2))

    # Synchronous put_nowait should fail when full
    with pytest.raises(asyncio.QueueFull):
        buf.put_nowait(create_test_frame(3))

    # Asynchronous put will wait until a consumer retrieves a frame
    async def delayed_consumer():
        await asyncio.sleep(0.05)
        return await buf.get()

    task = asyncio.create_task(delayed_consumer())
    await buf.put(create_test_frame(3))
    consumed = await task

    assert consumed.sequence_number == 1
    assert buf.qsize() == 2

    f2 = await buf.get()
    f3 = await buf.get()
    assert f2.sequence_number == 2
    assert f3.sequence_number == 3


@pytest.mark.asyncio
async def test_buffer_metrics_and_backpressure():
    buf = FrameBuffer(maxsize=10, policy=DropPolicy.DROP_OLDEST)

    for i in range(1, 15):
        await buf.put(create_test_frame(i))

    metrics = buf.get_metrics()
    assert metrics.frames_received == 14
    assert metrics.frames_dropped == 4
    assert metrics.queue_depth == 10
    assert metrics.drop_rate > 0.0

    # Consume frames and check processing metrics
    for _ in range(5):
        await buf.get()

    metrics_after = buf.get_metrics()
    assert metrics_after.frames_processed == 5
    assert metrics_after.queue_depth == 5
    assert metrics_after.latency_ms >= 0.0


@pytest.mark.asyncio
async def test_buffer_clear_and_close():
    buf = FrameBuffer(maxsize=5, policy=DropPolicy.DROP_OLDEST)
    await buf.put(create_test_frame(1))
    await buf.put(create_test_frame(2))

    buf.clear()
    assert buf.empty()
    assert buf.qsize() == 0

    await buf.close()
    with pytest.raises(RuntimeError, match="closed"):
        await buf.put(create_test_frame(3))

    with pytest.raises(asyncio.QueueEmpty):
        buf.get_nowait()
