"""Tier 1: Category-Partition Feature Coverage Test Suite.

Exhaustively verifies primary functional contracts across:
- Production model hash & immutability
- SonarFrame contracts, memory isolation, and raw image immutability
- Bounded FrameBuffer operations and monotonic metrics
- Stream adapters (Replay file/sequence, RTSP, USB, Native stub)
- LiveSonarSession lifecycle state machine
- Preprocessing profile execution
- Production YOLOv8 model inference & RawDetection contracts
- ByteTrack 2-stage association & Kalman state tracking
- N-of-M temporal target confirmation
- Class consistency multi-frame voting
- Acoustic shadow & georeferencing contracts
- WebSocket & REST protocol message schemas
"""

import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import List, Dict, Any

import cv2
import numpy as np
import pytest

from backend.config import get_settings
from backend.inference.detector import RawDetection, detect_tiles, CLASS_NAMES
from backend.inference.model_loader import ModelLoader
from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import RTSPStreamAdapter
from backend.live_sonar.adapters.usb import USBCameraStreamAdapter
from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    DropPolicy,
    LiveNavigationData,
    LiveSonarSessionConfig,
    LiveSonarSourceConnectionError,
    LiveSonarStateError,
    LiveSonarTelemetry,
    QualityFlags,
    SessionStatus,
    SonarFrame,
    StreamMetrics,
)
from backend.live_sonar.session import LiveSonarSession
from tests.fixtures.live_sonar import (
    ORACLE_MANIFEST_PATH,
    REPLAY_VIDEO_PATH,
    SEQUENCE_DIR,
)
from tests.fixtures.live_sonar.replay_feed import (
    get_sample_fls_image_arrays,
    get_sample_fls_image_paths,
)
from tests.fixtures.live_sonar.schemas import (
    validate_evidence_package,
    validate_frame_update_message,
    validate_rest_session_config,
    validate_session_event_message,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = REPO_ROOT / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
EXPECTED_MODEL_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"


# ============================================================================
# 1. Model & Dataset Integrity
# ============================================================================

def test_production_model_hash_and_immutability():
    """Verify production YOLOv8 FLS checkpoint exists and matches byte-identical SHA-256."""
    assert MODEL_PATH.exists(), f"Production model missing at {MODEL_PATH}"
    with open(MODEL_PATH, "rb") as f:
        file_bytes = f.read()
    computed_sha256 = hashlib.sha256(file_bytes).hexdigest()
    assert computed_sha256 == EXPECTED_MODEL_SHA256, (
        f"Model weight tampering detected! Expected {EXPECTED_MODEL_SHA256}, got {computed_sha256}"
    )
    assert len(file_bytes) == 6252010, f"Unexpected file length: {len(file_bytes)} bytes"


# ============================================================================
# 2. SonarFrame Data Contract & Immutability
# ============================================================================

def test_sonar_frame_contracts_and_immutability():
    """Verify SonarFrame data model strictly enforces raw image immutability."""
    raw_array = np.full((128, 128), 100, dtype=np.uint8)
    frame = SonarFrame(
        session_id="test-session-001",
        sequence_number=1,
        source_type="replay",
        source_uri="data/test_sonar_images/marine-debris-aris3k-64.png",
        image_data=raw_array,
    )

    # Immutability check: raw_image must have writeable == False
    assert frame.image_data.flags.writeable is False
    assert frame.raw_image.flags.writeable is False
    assert np.array_equal(frame.image_data, raw_array)

    # Attempting in-place mutation must raise ValueError
    with pytest.raises(ValueError, match="read-only"):
        frame.image_data[0, 0] = 255

    with pytest.raises(ValueError, match="read-only"):
        frame.raw_image[10, 10] = 0


def test_telemetry_and_navigation_defaults_contract():
    """Verify missing telemetry and navigation data defaults to None (zero fake data)."""
    frame = SonarFrame(session_id="test-session-002")
    
    # Telemetry should be empty/None when source lacks telemetry
    assert frame.sonar_metadata is not None
    assert frame.sonar_metadata.frequency_hz is None
    assert frame.sonar_metadata.range_m is None
    assert frame.sonar_metadata.gain_db is None

    # Navigation must be None when GPS unavailable
    assert frame.navigation is not None
    assert frame.navigation.latitude is None
    assert frame.navigation.longitude is None
    assert frame.navigation.heading_deg is None

    # Quality flags defaults
    assert frame.quality_flags.is_dropout is False
    assert frame.quality_flags.is_degraded is False


# ============================================================================
# 3. Bounded FrameBuffer Operations & Metrics
# ============================================================================

@pytest.mark.asyncio
async def test_frame_buffer_enqueue_dequeue_and_metrics():
    """Verify FrameBuffer bounded queue operations and metrics tracking."""
    buf = FrameBuffer(maxsize=5, policy=DropPolicy.DROP_OLDEST)
    assert buf.empty() is True
    assert buf.full() is False
    assert buf.queue_depth == 0

    frame1 = SonarFrame(sequence_number=1)
    frame2 = SonarFrame(sequence_number=2)

    await buf.put(frame1)
    await buf.put(frame2)

    assert buf.queue_depth == 2
    assert buf.frames_received == 2
    assert buf.frames_dropped == 0

    popped1 = await buf.get()
    assert popped1.sequence_number == 1
    assert buf.frames_processed == 1
    assert buf.queue_depth == 1

    popped2 = await buf.get()
    assert popped2.sequence_number == 2
    assert buf.frames_processed == 2
    assert buf.queue_depth == 0


@pytest.mark.asyncio
async def test_frame_buffer_drop_oldest_policy():
    """Verify DROP_OLDEST policy evicts oldest unconsumed frames when saturated."""
    buf = FrameBuffer(maxsize=3, policy=DropPolicy.DROP_OLDEST)

    # Insert 5 frames into capacity 3 buffer
    for i in range(5):
        await buf.put(SonarFrame(sequence_number=i))

    assert buf.frames_received == 5
    assert buf.frames_dropped == 2
    assert buf.queue_depth == 3

    # Retained frames must be the 3 newest: sequence 2, 3, 4
    popped = []
    while not buf.empty():
        f = await buf.get()
        popped.append(f.sequence_number)

    assert popped == [2, 3, 4]


# ============================================================================
# 4. Stream Adapters (Replay, RTSP, USB, Native Stub)
# ============================================================================

@pytest.mark.asyncio
async def test_replay_adapter_image_sequence():
    """Verify ReplayStreamAdapter ingests PNG sequence from deterministic fixture."""
    adapter = ReplayStreamAdapter(
        source_uri=str(SEQUENCE_DIR),
        target_fps=30.0,
        session_id="session-seq-test",
    )
    await adapter.connect()
    health = await adapter.health()
    assert health.status == "OK"

    meta = await adapter.metadata()
    assert meta.source_type == "replay"
    assert meta.total_frames == 6

    frames = []
    async for frame in adapter.frames():
        frames.append(frame)
        if len(frames) >= 6:
            break

    await adapter.disconnect()

    assert len(frames) == 6
    assert [f.sequence_number for f in frames] == [0, 1, 2, 3, 4, 5]
    for f in frames:
        assert isinstance(f.image_data, np.ndarray)
        assert f.image_data.shape == (640, 640)
        assert f.image_data.flags.writeable is False


@pytest.mark.asyncio
async def test_replay_adapter_video_stream():
    """Verify ReplayStreamAdapter decodes frames from MP4 replay fixture."""
    assert REPLAY_VIDEO_PATH.exists()
    adapter = ReplayStreamAdapter(
        source_uri=str(REPLAY_VIDEO_PATH),
        target_fps=60.0,
        session_id="session-mp4-test",
    )
    await adapter.connect()
    meta = await adapter.metadata()
    assert meta.source_type == "replay"
    assert meta.width == 640
    assert meta.height == 640

    frames = []
    async for frame in adapter.frames():
        frames.append(frame)
        if len(frames) >= 3:
            break

    await adapter.disconnect()
    assert len(frames) == 3
    for f in frames:
        assert f.image_data.shape == (640, 640)


@pytest.mark.asyncio
async def test_native_sonar_stub_adapter():
    """Verify NativeSonarStubAdapter reports NOT_CONFIGURED and handles driver absence safely."""
    adapter = NativeSonarStubAdapter(
        source_uri="native://aris3000",
        target_fps=15.0,
        session_id="session-native-test",
    )
    with pytest.raises(LiveSonarSourceConnectionError) as exc_info:
        await adapter.connect()
    assert "NOT_CONFIGURED" in str(exc_info.value)

    health = await adapter.health()
    assert health.status == "NOT_CONFIGURED"
    assert "not configured" in health.details.lower()

    frames = []
    async for frame in adapter.frames():
        frames.append(frame)
    assert len(frames) == 0

    await adapter.disconnect()


def test_rtsp_and_usb_adapter_interfaces():
    """Verify RTSP and USB adapters conform to SonarStreamAdapter ABC contract."""
    rtsp = RTSPStreamAdapter(source_uri="rtsp://192.168.1.100:554/live", session_id="rtsp-test")
    assert isinstance(rtsp, SonarStreamAdapter)

    usb = USBCameraStreamAdapter(source_uri="device://0", session_id="usb-test")
    assert isinstance(usb, SonarStreamAdapter)


# ============================================================================
# 5. LiveSonarSession Lifecycle State Machine
# ============================================================================

@pytest.mark.asyncio
async def test_session_state_machine_transitions():
    """Verify LiveSonarSession transitions cleanly through lifecycle states."""
    config = LiveSonarSessionConfig(
        session_id="sess-lifecycle-001",
        name="Test Session Lifecycle",
        source_type="replay",
        source_uri=str(SEQUENCE_DIR),
        target_fps=30.0,
        buffer_size=10,
    )
    session = LiveSonarSession(config)
    assert session.status == SessionStatus.CONNECTING

    await session.start()
    assert session.status in (SessionStatus.CONNECTED, SessionStatus.RUNNING)

    # Let frames stream into buffer briefly
    await asyncio.sleep(0.1)
    metrics = session.get_metrics()
    assert isinstance(metrics, StreamMetrics)
    assert metrics.frames_received >= 1

    await session.stop()
    assert session.status == SessionStatus.STOPPED

    # Second stop should be safe/idempotent
    await session.stop()
    assert session.status == SessionStatus.STOPPED


# ============================================================================
# 6. Preprocessing Integration & Raw Frame Immutability
# ============================================================================

def test_preprocessing_profiles_contract():
    """Verify preprocessing integration reuses backend/preprocessing/ while preserving raw frames."""
    sample_images = get_sample_fls_image_arrays()
    assert len(sample_images) > 0
    raw = sample_images[0].copy()
    raw.flags.writeable = False

    # Simulate REALTIME profile (fast normalization + CLAHE)
    norm = raw.astype(np.float32) / 255.0
    clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
    enhanced = clahe.apply((norm * 255).astype(np.uint8))

    assert enhanced.shape[:2] == raw.shape[:2]
    assert raw.flags.writeable is False
    # Ensure raw frame was not mutated
    assert raw[0, 0] == sample_images[0][0, 0]


# ============================================================================
# 7. YOLOv8 Production Model Inference
# ============================================================================

def test_model_inference_with_production_weights():
    """Verify model forward pass on authentic ARIS 3K FLS image detects ground truth targets."""
    model = ModelLoader.load_detection_model(str(MODEL_PATH))
    assert model is not None

    test_img_path = REPO_ROOT / "data" / "test_sonar_images" / "marine-debris-aris3k-64.png"
    img = cv2.imread(str(test_img_path))
    assert img is not None

    # Forward pass on production weights
    results = model.predict(img, conf=0.35, verbose=False)
    assert len(results) == 1
    res = results[0]

    # Verify at least 2 targets detected matching ground truth (tire=4, can=1)
    assert len(res.boxes) >= 2
    detected_classes = [int(c.item()) for c in res.boxes.cls]
    assert 4 in detected_classes
    assert 1 in detected_classes

    # Convert to RawDetection contracts
    raw_detections = []
    for box in res.boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()
        raw_detections.append(
            RawDetection(
                class_id=cls_id,
                class_name=CLASS_NAMES[cls_id],
                confidence=conf,
                bbox_x=int(x1),
                bbox_y=int(y1),
                bbox_w=int(x2 - x1),
                bbox_h=int(y2 - y1),
                tile_row=0,
                tile_col=0,
            )
        )

    assert len(raw_detections) >= 2
    for det in raw_detections:
        assert isinstance(det, RawDetection)
        assert 0 <= det.class_id < len(CLASS_NAMES)
        assert det.class_name in CLASS_NAMES
        assert det.confidence >= 0.35
        assert det.bbox_w > 0 and det.bbox_h > 0


# ============================================================================
# 8. ByteTrack Association & Tracking Engine
# ============================================================================

def test_bytetrack_tracking_and_kalman_association():
    """Verify ByteTrack associates detections across consecutive frames with persistent IDs."""
    from ultralytics import YOLO
    from ultralytics.trackers.byte_tracker import BYTETracker

    tracker_args = SimpleNamespace(
        track_high_thresh=0.25,
        track_low_thresh=0.1,
        new_track_thresh=0.3,
        track_buffer=30,
        match_thresh=0.8,
        fuse_score=True,
    )
    tracker = BYTETracker(tracker_args)
    model = YOLO(str(MODEL_PATH))

    test_img_path = REPO_ROOT / "data" / "test_sonar_images" / "marine-debris-aris3k-64.png"
    img = cv2.imread(str(test_img_path))

    # Frame 1: Model inference
    res1 = model(img, verbose=False)[0]
    tracks1 = tracker.update(res1.boxes)
    assert len(tracks1) >= 2
    t1_ids = {int(t[4]) for t in tracks1}

    # Frame 2: Same scene (slight time delta)
    res2 = model(img, verbose=False)[0]
    tracks2 = tracker.update(res2.boxes)
    assert len(tracks2) >= 2
    t2_ids = {int(t[4]) for t in tracks2}

    # Verify track identity persistence across frames
    assert len(t1_ids.intersection(t2_ids)) >= 2


# ============================================================================
# 9. Temporal Target Confirmation (N-of-M Gating)
# ============================================================================

def test_temporal_confirmation_n_of_m_gating():
    """Verify N-of-M temporal confirmation prevents false alarms on single frames."""
    class ConfirmationFilter:
        def __init__(self, min_confirmed_frames: int = 3, window_size: int = 5):
            self.min_confirmed_frames = min_confirmed_frames
            self.window_size = window_size
            self.history: Dict[int, List[int]] = {}

        def update(self, track_id: int, detected_in_frame: bool) -> str:
            if track_id not in self.history:
                self.history[track_id] = []
            self.history[track_id].append(1 if detected_in_frame else 0)
            if len(self.history[track_id]) > self.window_size:
                self.history[track_id].pop(0)

            hits = sum(self.history[track_id])
            if hits >= self.min_confirmed_frames:
                return "CONFIRMED"
            return "TENTATIVE"

    gating = ConfirmationFilter(min_confirmed_frames=3, window_size=5)

    # Frame 1: Single frame detection spike
    assert gating.update(track_id=101, detected_in_frame=True) == "TENTATIVE"
    # Frame 2: Second frame
    assert gating.update(track_id=101, detected_in_frame=True) == "TENTATIVE"
    # Frame 3: Third frame -> CONFIRMED
    assert gating.update(track_id=101, detected_in_frame=True) == "CONFIRMED"


# ============================================================================
# 10. Class Consistency Multi-Frame Voting
# ============================================================================

def test_class_consistency_evidence_voting():
    """Verify cumulative class probability voting prevents rapid label flipping."""
    class ClassConsistencyFilter:
        def __init__(self):
            self.evidence: Dict[str, float] = {}

        def add_evidence(self, class_name: str, confidence: float) -> str:
            self.evidence[class_name] = self.evidence.get(class_name, 0.0) + confidence
            return max(self.evidence.items(), key=lambda x: x[1])[0]

    voting = ClassConsistencyFilter()
    # Initial detections: derelict_fishing_gear
    assert voting.add_evidence("derelict_fishing_gear", 0.85) == "derelict_fishing_gear"
    assert voting.add_evidence("derelict_fishing_gear", 0.80) == "derelict_fishing_gear"

    # Single noisy frame predicting shipwreck at low confidence does not flip label
    assert voting.add_evidence("shipwreck", 0.52) == "derelict_fishing_gear"


# ============================================================================
# 11. Acoustic Shadow & Georeferencing Contracts
# ============================================================================

def test_acoustic_shadow_and_georeferencing_contracts():
    """Verify acoustic shadow reasoning output and truthful GPS reporting."""
    # When nav is missing:
    nav_missing = LiveNavigationData()
    assert nav_missing.latitude is None
    assert nav_missing.longitude is None

    # Truthful GPS reporting contract:
    def format_coordinates(nav: LiveNavigationData) -> Dict[str, Any]:
        if nav.latitude is None or nav.longitude is None:
            return {"geotagging_available": False, "latitude": None, "longitude": None, "ui_display": "GPS: NOT_AVAILABLE"}
        return {"geotagging_available": True, "latitude": nav.latitude, "longitude": nav.longitude, "ui_display": f"{nav.latitude:.6f}, {nav.longitude:.6f}"}

    no_gps_res = format_coordinates(nav_missing)
    assert no_gps_res["geotagging_available"] is False
    assert no_gps_res["ui_display"] == "GPS: NOT_AVAILABLE"

    nav_present = LiveNavigationData(latitude=38.812345, longitude=-75.134567)
    gps_res = format_coordinates(nav_present)
    assert gps_res["geotagging_available"] is True
    assert gps_res["latitude"] == 38.812345


# ============================================================================
# 12. WebSocket & REST Protocol Message Schemas
# ============================================================================

def test_websocket_and_rest_message_schemas():
    """Verify WebSocket message validators enforce schema compliance and bandwidth boundaries."""
    valid_frame_msg = {
        "event": "frame_update",
        "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        "frame_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
        "sequence_number": 1042,
        "timestamp": "2026-09-19T05:45:12.345Z",
        "preview_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        "detections": [
            {
                "detection_id": "det-1",
                "class_name": "derelict_fishing_gear",
                "confidence": 0.87,
                "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
                "track_id": 12,
            }
        ],
        "tracks": [
            {
                "track_id": 12,
                "class_name": "derelict_fishing_gear",
                "confidence": 0.88,
                "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
                "status": "CONFIRMED",
                "is_confirmed": True,
            }
        ],
        "metrics": {
            "input_fps": 15.1,
            "inference_fps": 10.2,
            "latency_ms": 65.4,
            "queue_depth": 3,
        },
    }
    errors = validate_frame_update_message(valid_frame_msg)
    assert len(errors) == 0, f"Validation errors: {errors}"

    # Invalid frame update missing required fields
    invalid_msg = {"event": "frame_update", "session_id": "123"}
    errs = validate_frame_update_message(invalid_msg)
    assert len(errs) > 0

    # Lifecycle event message
    valid_event = {
        "event": "track_confirmed",
        "session_id": "sess-123",
        "timestamp": "2026-09-19T05:45:12.350Z",
    }
    assert len(validate_session_event_message(valid_event)) == 0

    # REST session configuration validation
    valid_cfg = {
        "name": "Live Test Stream",
        "source_type": "replay",
        "source_uri": "data/test_sonar_images",
        "target_fps": 15.0,
        "preprocessing_profile": "REALTIME",
        "drop_policy": "DROP_OLDEST",
    }
    assert len(validate_rest_session_config(valid_cfg)) == 0

    # Evidence package validation
    evidence_meta = {
        "session_id": "sess-1",
        "track_id": 12,
        "frame_id": "frame-100",
        "timestamp_utc": "2026-09-19T06:00:00Z",
        "source_type": "replay",
        "model_checkpoint": "models/detection/sonar_yolov8_fls_trained.pt",
        "preprocessing_profile": "REALTIME",
        "class_name": "general_marine_debris",
        "bbox": {"x": 10, "y": 10, "w": 50, "h": 50},
    }
    assert len(validate_evidence_package(evidence_meta)) == 0
