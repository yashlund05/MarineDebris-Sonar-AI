"""Unit tests for SonarStreamAdapter implementations (Replay, RTSP, USB, Native Stub).

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from pathlib import Path
import pytest

from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import (
    RTSPStreamAdapter,
    sanitize_rtsp_uri,
    validate_rtsp_uri,
)
from backend.live_sonar.adapters.usb import USBCameraStreamAdapter
from backend.live_sonar.models import (
    LiveSonarSecurityViolationError,
    LiveSonarSourceConnectionError,
    LiveSonarSourceInvalidError,
)


@pytest.mark.asyncio
async def test_replay_adapter_real_image_sequence():
    test_dir = Path("data/test_sonar_images")
    if not test_dir.exists():
        pytest.skip("data/test_sonar_images not found")

    adapter = ReplayStreamAdapter(
        source_uri=str(test_dir),
        target_fps=60.0,  # Fast for test
        loop=False,
    )

    assert not adapter.is_connected
    await adapter.connect()
    assert adapter.is_connected

    meta = await adapter.metadata()
    assert meta.source_type == "replay"
    assert meta.total_frames is not None and meta.total_frames >= 6
    assert meta.width is not None and meta.height is not None

    health = await adapter.health()
    assert health.status == "OK"

    # Consume first 3 frames
    frames_collected = []
    async for frame in adapter.frames():
        frames_collected.append(frame)
        if len(frames_collected) >= 3:
            break

    assert len(frames_collected) == 3
    for idx, f in enumerate(frames_collected):
        assert f.sequence_number == idx
        assert f.source_type == "replay"
        assert f.image_data.ndim == 2
        assert not f.image_data.flags.writeable  # Immutability verified

    await adapter.disconnect()
    assert not adapter.is_connected


@pytest.mark.asyncio
async def test_replay_adapter_synthetic_feed():
    adapter = ReplayStreamAdapter(
        source_uri="synthetic://fls",
        target_fps=100.0,
        loop=False,
    )

    await adapter.connect()
    assert adapter.is_connected

    frames_collected = []
    async for frame in adapter.frames():
        frames_collected.append(frame)
        if len(frames_collected) >= 2:
            break

    assert len(frames_collected) == 2
    f0 = frames_collected[0]
    assert f0.image_data.shape == (512, 640)
    assert f0.sonar_metadata.frequency_hz == 1200000.0
    assert f0.sonar_metadata.range_m == 30.0

    await adapter.disconnect()


@pytest.mark.asyncio
async def test_replay_adapter_controls():
    test_dir = Path("data/test_sonar_images")
    if not test_dir.exists():
        pytest.skip("data/test_sonar_images not found")

    adapter = ReplayStreamAdapter(
        source_uri=str(test_dir),
        target_fps=30.0,
        loop=True,
    )
    await adapter.connect()

    # Seek
    adapter.seek(2)
    assert adapter._current_index == 2

    # Speed
    adapter.set_speed(2.0)
    assert adapter.speed_multiplier == 2.0

    # Pause & Resume
    adapter.pause()
    assert adapter.is_paused
    adapter.resume()
    assert not adapter.is_paused

    await adapter.disconnect()


@pytest.mark.asyncio
async def test_replay_adapter_invalid_path():
    adapter = ReplayStreamAdapter(source_uri="data/nonexistent_dir_12345")
    with pytest.raises(LiveSonarSourceInvalidError, match="does not exist"):
        await adapter.connect()


@pytest.mark.asyncio
async def test_replay_adapter_path_traversal():
    adapter = ReplayStreamAdapter(source_uri="../../windows/system32")
    with pytest.raises(LiveSonarSourceInvalidError, match="Path traversal"):
        await adapter.connect()


def test_rtsp_uri_sanitization():
    raw_uri = "rtsp://admin:hunter2@192.168.1.100:554/sonar/live"
    sanitized = sanitize_rtsp_uri(raw_uri)
    assert "hunter2" not in sanitized
    assert "admin" not in sanitized
    assert "rtsp://***:***@192.168.1.100:554/sonar/live" == sanitized

    clean_uri = "rtsp://192.168.1.100:554/sonar/live"
    assert sanitize_rtsp_uri(clean_uri) == clean_uri


def test_rtsp_uri_validation_ssrf():
    # Cloud metadata link-local address
    with pytest.raises(LiveSonarSecurityViolationError, match="169.254.169.254"):
        validate_rtsp_uri("rtsp://169.254.169.254/feed")

    # Invalid scheme
    with pytest.raises(LiveSonarSecurityViolationError, match="Invalid RTSP protocol scheme"):
        validate_rtsp_uri("http://192.168.1.100:8080/stream")

    # Missing host
    with pytest.raises(LiveSonarSourceInvalidError, match="valid hostname"):
        validate_rtsp_uri("rtsp:///path")

    # Loopback disallowed
    with pytest.raises(LiveSonarSecurityViolationError, match="loopback"):
        validate_rtsp_uri("rtsp://127.0.0.1:8554/live", allow_local=False)


@pytest.mark.asyncio
async def test_rtsp_adapter_connection_failure():
    adapter = RTSPStreamAdapter(
        source_uri="rtsp://admin:pass@192.0.2.1:554/unreachable",
        max_reconnect_attempts=1,
    )
    with pytest.raises(LiveSonarSourceConnectionError):
        await adapter.connect()

    health = await adapter.health()
    assert health.status == "ERROR"
    assert "pass" not in health.source_uri
    assert "pass" not in health.details


def test_usb_camera_adapter_device_index():
    adapter1 = USBCameraStreamAdapter(source_uri="device://0")
    assert adapter1.device_index == 0

    adapter2 = USBCameraStreamAdapter(source_uri="usb://2")
    assert adapter2.device_index == 2

    adapter3 = USBCameraStreamAdapter(source_uri="1")
    assert adapter3.device_index == 1

    with pytest.raises(LiveSonarSourceInvalidError, match="Invalid USB device URI"):
        USBCameraStreamAdapter(source_uri="device://invalid")


@pytest.mark.asyncio
async def test_native_sonar_stub_adapter():
    adapter = NativeSonarStubAdapter(source_uri="native://aris3000")

    assert not adapter.is_connected

    # connect() must raise LiveSonarSourceConnectionError reporting NOT_CONFIGURED
    with pytest.raises(LiveSonarSourceConnectionError) as exc_info:
        await adapter.connect()
    assert "NOT_CONFIGURED" in str(exc_info.value)
    assert exc_info.value.error_code == "NATIVE_SONAR_UNAVAILABLE"

    # health() returns NOT_CONFIGURED
    health = await adapter.health()
    assert health.status == "NOT_CONFIGURED"
    assert "not configured" in health.details

    # metadata() returns NOT_CONFIGURED
    meta = await adapter.metadata()
    assert meta.source_type == "native_stub"
    assert meta.extra.get("status") == "NOT_CONFIGURED"

    # frames() yields zero frames without crashing
    frames = []
    async for f in adapter.frames():
        frames.append(f)
    assert len(frames) == 0
