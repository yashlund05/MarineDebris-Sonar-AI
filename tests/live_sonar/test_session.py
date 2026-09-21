"""Unit tests for LiveSonarSession lifecycle manager and adapter factory.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

import asyncio
from pathlib import Path
import pytest

from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import RTSPStreamAdapter
from backend.live_sonar.adapters.usb import USBCameraStreamAdapter
from backend.live_sonar.models import (
    DropPolicy,
    LiveSonarSessionConfig,
    LiveSonarSourceInvalidError,
    LiveSonarStateError,
    SessionStatus,
)
from backend.live_sonar.session import LiveSonarSession, create_adapter


def test_create_adapter_factory():
    cfg_replay = LiveSonarSessionConfig(
        session_id="s1",
        source_type="replay",
        source_uri="synthetic://test",
    )
    assert isinstance(create_adapter(cfg_replay), ReplayStreamAdapter)

    cfg_rtsp = LiveSonarSessionConfig(
        session_id="s2",
        source_type="rtsp",
        source_uri="rtsp://localhost:8554/live",
    )
    assert isinstance(create_adapter(cfg_rtsp), RTSPStreamAdapter)

    cfg_usb = LiveSonarSessionConfig(
        session_id="s3",
        source_type="usb",
        source_uri="device://0",
    )
    assert isinstance(create_adapter(cfg_usb), USBCameraStreamAdapter)

    cfg_native = LiveSonarSessionConfig(
        session_id="s4",
        source_type="native_stub",
        source_uri="native://aris",
    )
    assert isinstance(create_adapter(cfg_native), NativeSonarStubAdapter)

    cfg_invalid = LiveSonarSessionConfig(
        session_id="s5",
        source_type="unsupported_type",
        source_uri="foo://bar",
    )
    with pytest.raises(LiveSonarSourceInvalidError, match="Unsupported sonar source type"):
        create_adapter(cfg_invalid)


@pytest.mark.asyncio
async def test_session_lifecycle_with_replay():
    test_dir = Path("data/test_sonar_images")
    if not test_dir.exists():
        pytest.skip("data/test_sonar_images not found")

    config = LiveSonarSessionConfig(
        session_id="test-session-123",
        name="Test Replay Session",
        source_type="replay",
        source_uri=str(test_dir),
        target_fps=50.0,
        buffer_size=10,
        drop_policy=DropPolicy.DROP_OLDEST,
    )

    session = LiveSonarSession(config)
    assert session.status == SessionStatus.CONNECTING
    assert session.started_at is None
    assert session.stopped_at is None

    # Start session
    await session.start()
    assert session.status == SessionStatus.RUNNING
    assert session.started_at is not None

    # Retrieve at least 2 frames from session buffer
    frame1 = await asyncio.wait_for(session.buffer.get(), timeout=2.0)
    frame2 = await asyncio.wait_for(session.buffer.get(), timeout=2.0)

    assert frame1.session_id == "test-session-123"
    assert frame2.session_id == "test-session-123"

    metrics = session.get_metrics()
    assert metrics.frames_received >= 2
    assert metrics.frames_processed >= 2

    # Pause and resume
    await session.pause()
    await session.resume()

    # Stop session
    await session.stop()
    assert session.status == SessionStatus.STOPPED
    assert session.stopped_at is not None


@pytest.mark.asyncio
async def test_session_double_start_error():
    config = LiveSonarSessionConfig(
        session_id="test-session-double",
        source_type="replay",
        source_uri="synthetic://test",
        target_fps=100.0,
    )
    session = LiveSonarSession(config)
    await session.start()
    assert session.status == SessionStatus.RUNNING

    with pytest.raises(LiveSonarStateError, match="already active"):
        await session.start()

    await session.stop()


@pytest.mark.asyncio
async def test_session_invalid_source_error_state():
    config = LiveSonarSessionConfig(
        session_id="test-session-err",
        source_type="replay",
        source_uri="data/nonexistent_folder_xyz",
    )
    session = LiveSonarSession(config)

    with pytest.raises(LiveSonarSourceInvalidError):
        await session.start()

    assert session.status == SessionStatus.ERROR
    assert session.error_message is not None
