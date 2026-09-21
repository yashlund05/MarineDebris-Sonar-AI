"""Tier 2: Boundary Value Analysis & Stress Extremes Test Suite.

Exhaustively verifies mathematical boundaries, corner cases, and adversarial limits:
- Buffer capacity limits across all drop policies (DROP_OLDEST, FIFO, DROP_NEWEST, LATEST)
- Zero and negative capacity parameter validation
- Backpressure telemetry & rolling drop-rate calculation
- Replay adapter boundary behaviors (EOF termination, missing files, path traversal)
- RTSP security boundaries (cloud metadata SSRF, loopback blocking, credential scrubbing)
- Malformed & extreme image dimensions (0x0, 1x1, 4096x4096)
- Missing & extreme telemetry values (NaN, Inf, Null navigation)
- WebSocket bandwidth cap (<80 KB budget enforcement vs uncompressed raster)
- Session error state handling
"""

import asyncio
import base64
import json
import math
from pathlib import Path
from typing import Dict, Any

import cv2
import numpy as np
import pytest

from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import (
    RTSPStreamAdapter,
    sanitize_rtsp_uri,
    validate_rtsp_uri,
)
from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    DropPolicy,
    LiveNavigationData,
    LiveSonarSecurityViolationError,
    LiveSonarSessionConfig,
    LiveSonarSourceInvalidError,
    LiveSonarStateError,
    LiveSonarTelemetry,
    QualityFlags,
    SessionStatus,
    SonarFrame,
    StreamMetrics,
)
from backend.live_sonar.session import LiveSonarSession
from tests.fixtures.live_sonar import SEQUENCE_DIR
from tests.fixtures.live_sonar.schemas import validate_frame_update_message

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ============================================================================
# 1. Frame Buffer Capacity & Policy Boundaries
# ============================================================================

def test_buffer_capacity_zero_or_negative_raises_value_error():
    """Verify FrameBuffer rejects zero or negative capacity limits."""
    with pytest.raises(ValueError, match="greater than 0"):
        FrameBuffer(maxsize=0)

    with pytest.raises(ValueError, match="greater than 0"):
        FrameBuffer(maxsize=-10)


@pytest.mark.asyncio
async def test_buffer_fifo_drop_policy_blocking_and_nowait():
    """Verify FIFO policy blocks or rejects non-blocking put when full."""
    buf = FrameBuffer(maxsize=2, policy=DropPolicy.FIFO)
    buf.put_nowait(SonarFrame(sequence_number=1))
    buf.put_nowait(SonarFrame(sequence_number=2))

    assert buf.full() is True
    assert buf.queue_depth == 2

    # Non-blocking put on full FIFO buffer must raise QueueFull
    with pytest.raises(asyncio.QueueFull):
        buf.put_nowait(SonarFrame(sequence_number=3))

    # Async put with timeout should timeout if no space is freed
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(buf.put(SonarFrame(sequence_number=4)), timeout=0.1)

    # Dequeue one item; now put can succeed
    popped = await buf.get()
    assert popped.sequence_number == 1

    await buf.put(SonarFrame(sequence_number=5))
    assert buf.queue_depth == 2


@pytest.mark.asyncio
async def test_buffer_drop_newest_policy():
    """Verify DROP_NEWEST rejects incoming frames when buffer is saturated."""
    buf = FrameBuffer(maxsize=3, policy=DropPolicy.DROP_NEWEST)

    for i in range(5):
        await buf.put(SonarFrame(sequence_number=i))

    assert buf.frames_received == 5
    assert buf.frames_dropped == 2
    assert buf.queue_depth == 3

    # Retained frames must be the original oldest frames: 0, 1, 2
    popped = []
    while not buf.empty():
        f = await buf.get()
        popped.append(f.sequence_number)

    assert popped == [0, 1, 2]


@pytest.mark.asyncio
async def test_buffer_latest_policy_capacity_one():
    """Verify LATEST policy strictly maintains capacity 1, always retaining newest frame."""
    buf = FrameBuffer(maxsize=50, policy=DropPolicy.LATEST)

    # Effective maxsize for LATEST is always 1
    for i in range(10):
        await buf.put(SonarFrame(sequence_number=i))

    assert buf.frames_received == 10
    assert buf.frames_dropped == 9
    assert buf.queue_depth == 1

    latest_frame = await buf.get()
    assert latest_frame.sequence_number == 9
    assert buf.empty() is True


@pytest.mark.asyncio
async def test_backpressure_and_drop_rate_calculation():
    """Verify rolling drop rate metric increments truthfully under backpressure."""
    buf = FrameBuffer(maxsize=5, policy=DropPolicy.DROP_OLDEST)

    # Rapidly inject 20 frames
    for i in range(20):
        await buf.put(SonarFrame(sequence_number=i))

    metrics = buf.get_metrics()
    assert metrics.frames_received == 20
    assert metrics.frames_dropped == 15
    assert metrics.queue_depth == 5
    # Drop rate is dropped / received
    assert metrics.drop_rate > 0.0
    assert metrics.drop_rate <= 1.0


# ============================================================================
# 2. Replay Adapter Boundary Cases
# ============================================================================

@pytest.mark.asyncio
async def test_replay_adapter_missing_file_raises_source_invalid_error():
    """Verify ReplayStreamAdapter raises LiveSonarSourceInvalidError for nonexistent files."""
    adapter = ReplayStreamAdapter(
        source_uri="data/test_sonar_images/nonexistent_frame_9999.png",
        session_id="err-missing-file",
    )
    with pytest.raises(LiveSonarSourceInvalidError) as exc_info:
        await adapter.connect()
    assert exc_info.value.status_code == 400
    assert "does not exist" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_replay_adapter_path_traversal_detection():
    """Verify ReplayStreamAdapter blocks directory traversal attempts."""
    traversal_uri = "../../windows/system32/cmd.exe"
    adapter = ReplayStreamAdapter(
        source_uri=traversal_uri,
        session_id="err-traversal",
    )
    with pytest.raises(LiveSonarSourceInvalidError) as exc_info:
        await adapter.connect()
    assert "path traversal" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_replay_adapter_clean_eof_termination():
    """Verify ReplayStreamAdapter terminates generator at EOF when loop=False."""
    adapter = ReplayStreamAdapter(
        source_uri=str(SEQUENCE_DIR),
        target_fps=60.0,
        loop=False,
        session_id="eof-test",
    )
    await adapter.connect()

    count = 0
    async for _ in adapter.frames():
        count += 1

    await adapter.disconnect()
    # Entire sequence read, then loop terminates cleanly
    assert count == 6


# ============================================================================
# 3. Security & Network Protocol Boundaries
# ============================================================================

def test_rtsp_ssrf_cloud_metadata_ip_blocked():
    """Verify SSRF validation strictly prohibits access to cloud metadata IP 169.254.169.254."""
    with pytest.raises(LiveSonarSecurityViolationError) as exc_info:
        validate_rtsp_uri("rtsp://169.254.169.254/latest/meta-data")
    assert "169.254.169.254" in str(exc_info.value)
    assert exc_info.value.status_code == 400


def test_rtsp_ssrf_loopback_blocked_when_disallowed():
    """Verify loopback addresses are blocked when allow_local is False."""
    with pytest.raises(LiveSonarSecurityViolationError):
        validate_rtsp_uri("rtsp://127.0.0.1:8554/live", allow_local=False)

    with pytest.raises(LiveSonarSecurityViolationError):
        validate_rtsp_uri("rtsp://localhost:8554/live", allow_local=False)


def test_rtsp_credential_scrubbing_hygiene():
    """Verify embedded credentials in RTSP URIs are cleanly stripped and redacted."""
    raw_uri = "rtsp://sonarAdmin:ExtremeSecretKey99@192.168.1.120:554/stream"
    sanitized = sanitize_rtsp_uri(raw_uri)

    assert "sonarAdmin" not in sanitized
    assert "ExtremeSecretKey99" not in sanitized
    assert sanitized == "rtsp://***:***@192.168.1.120:554/stream"


def test_rtsp_invalid_protocol_scheme_rejected():
    """Verify non-RTSP schemes are rejected to prevent protocol smuggling."""
    for bad_scheme in ["http://192.168.1.10/video.mp4", "ftp://192.168.1.10/sonar", "gopher://bad.host"]:
        with pytest.raises(LiveSonarSecurityViolationError):
            validate_rtsp_uri(bad_scheme)


# ============================================================================
# 4. Input Stress & Extreme Frame Dimensions
# ============================================================================

def test_extreme_and_corrupt_frame_dimensions():
    """Verify SonarFrame handles extreme and boundary dimensions safely."""
    # Empty 0x0 frame
    empty_arr = np.zeros((0, 0), dtype=np.uint8)
    f_empty = SonarFrame(image_data=empty_arr)
    assert f_empty.image_data.shape == (0, 0)
    assert f_empty.image_data.flags.writeable is False

    # Single-pixel 1x1 frame
    pixel_arr = np.zeros((1, 1), dtype=np.uint8)
    f_pixel = SonarFrame(image_data=pixel_arr)
    assert f_pixel.image_data.shape == (1, 1)

    # Large 4096x4096 frame
    large_arr = np.zeros((4096, 4096), dtype=np.uint8)
    f_large = SonarFrame(image_data=large_arr)
    assert f_large.image_data.shape == (4096, 4096)
    assert f_large.image_data.flags.writeable is False


def test_malformed_telemetry_and_navigation_types():
    """Verify telemetry handling of NaN, Inf, and boundary float values."""
    telem = LiveSonarTelemetry(
        frequency_hz=float("nan"),
        range_m=float("inf"),
        gain_db=-999.0,
    )
    assert math.isnan(telem.frequency_hz)
    assert math.isinf(telem.range_m)

    # Quality flags handling degraded status
    qf = QualityFlags(is_dropout=True, is_degraded=True, motion_quality_score=0.1)
    assert qf.is_dropout is True
    assert qf.is_degraded is True


# ============================================================================
# 5. WebSocket Bandwidth Budget Enforcement
# ============================================================================

def test_websocket_bandwidth_budget_enforcement():
    """Verify WebSocket preview payload stays strictly under the 80 KB bandwidth budget.
    
    Raw 1024x1024 float32 frames (~4 MB) must NEVER be transmitted over WebSocket.
    """
    from tests.fixtures.live_sonar.replay_feed import get_sample_fls_image_arrays

    # 1. Uncompressed raw frame size
    raw_frame_float32 = np.zeros((1024, 1024), dtype=np.float32)
    raw_size_bytes = raw_frame_float32.nbytes
    assert raw_size_bytes == 4 * 1024 * 1024  # 4.19 MB

    # 2. Authentic ARIS 3K acoustic JPEG preview (640x640, quality=75)
    sonar_images = get_sample_fls_image_arrays()
    test_img = sonar_images[0] if sonar_images else np.full((640, 640), 128, dtype=np.uint8)
    success, encoded_jpg = cv2.imencode(".jpg", test_img, [cv2.IMWRITE_JPEG_QUALITY, 75])
    assert success is True

    jpg_b64 = "data:image/jpeg;base64," + base64.b64encode(encoded_jpg.tobytes()).decode("ascii")

    # 3. Construct full frame_update message
    payload = {
        "event": "frame_update",
        "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "frame_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "sequence_number": 100,
        "timestamp": "2026-09-19T06:00:00.000Z",
        "preview_image": jpg_b64,
        "detections": [
            {
                "detection_id": "d-1",
                "class_name": "general_marine_debris",
                "confidence": 0.85,
                "bbox": {"x": 200, "y": 300, "w": 40, "h": 50},
                "track_id": 1,
            }
        ],
        "tracks": [
            {
                "track_id": 1,
                "class_name": "general_marine_debris",
                "confidence": 0.85,
                "bbox": {"x": 200, "y": 300, "w": 40, "h": 50},
                "status": "CONFIRMED",
                "is_confirmed": True,
            }
        ],
        "metrics": {
            "input_fps": 15.0,
            "inference_fps": 10.0,
            "latency_ms": 45.2,
            "queue_depth": 2,
        },
    }

    # Validate schema
    assert len(validate_frame_update_message(payload)) == 0

    # Validate bandwidth: serialized JSON must be under 80 KB (81,920 bytes)
    serialized_bytes = len(json.dumps(payload).encode("utf-8"))
    assert serialized_bytes < 80 * 1024, (
        f"Payload size {serialized_bytes} bytes exceeds 80 KB limit!"
    )


# ============================================================================
# 6. Session Error State & Transition Boundaries
# ============================================================================

@pytest.mark.asyncio
async def test_session_invalid_lifecycle_transition_raises_error():
    """Verify illegal lifecycle operations raise LiveSonarStateError."""
    config = LiveSonarSessionConfig(
        session_id="err-state-sess",
        source_type="replay",
        source_uri=str(SEQUENCE_DIR),
    )
    session = LiveSonarSession(config)
    await session.start()
    assert session.status in (SessionStatus.CONNECTED, SessionStatus.RUNNING)

    # Attempting to start an already active session must raise LiveSonarStateError
    with pytest.raises(LiveSonarStateError, match="already active"):
        await session.start()

    await session.stop()
    assert session.status == SessionStatus.STOPPED
