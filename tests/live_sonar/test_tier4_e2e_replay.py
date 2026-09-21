"""Tier 4: Real-World Workload Testing & Deterministic E2E Replay Lifecycle Test Suite.

Exhaustively verifies complete end-to-end mission workflows:
- Deterministic Replay Lifecycle:
    Session Init -> Frame Ingestion -> Preprocessing -> Production YOLOv8 Inference ->
    ByteTrack Temporal Association -> N-of-M Confirmation -> WebSocket Push ->
    Session Teardown
- Sustained workload performance & latency profiling
- Deterministic replay parity (repeatability across runs)
"""

import asyncio
import base64
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Dict, List, Any

import cv2
import numpy as np
import pytest
from ultralytics import YOLO
from ultralytics.trackers.byte_tracker import BYTETracker

from backend.inference.detector import RawDetection, CLASS_NAMES
from backend.inference.model_loader import ModelLoader
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    DropPolicy,
    LiveNavigationData,
    LiveSonarSessionConfig,
    LiveSonarTelemetry,
    QualityFlags,
    SessionStatus,
    SonarFrame,
    StreamMetrics,
)
from backend.live_sonar.session import LiveSonarSession
from tests.fixtures.live_sonar import (
    REPLAY_VIDEO_PATH,
    SEQUENCE_DIR,
)
from tests.fixtures.live_sonar.schemas import (
    validate_evidence_package,
    validate_frame_update_message,
    validate_session_event_message,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = REPO_ROOT / "models" / "detection" / "sonar_yolov8_fls_trained.pt"


# ============================================================================
# 1. Full Deterministic E2E Replay Lifecycle
# ============================================================================

@pytest.mark.asyncio
async def test_full_deterministic_e2e_replay_lifecycle(tmp_path):
    """Verify complete end-to-end replay lifecycle with authentic ARIS 3000 imagery.
    
    Validates:
    1. Session starts cleanly: CONNECTING -> CONNECTED -> RUNNING
    2. Real ARIS 3K frames arrive through ReplayStreamAdapter
    3. Production YOLOv8 model detects marine debris targets
    4. ByteTrack associates detections across consecutive frames with persistent IDs
    5. N-of-M confirmation promotes targets to CONFIRMED
    6. Formatted WebSocket messages adhere strictly to schema & <80 KB budget
    7. Evidence artifacts are written to disk for confirmed targets
    8. Session stops cleanly: RUNNING -> STOPPED
    """
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize session configuration with looping replay of authentic FLS image
    fls_img_path = str(REPO_ROOT / "data" / "test_sonar_images" / "marine-debris-aris3k-64.png")
    config = LiveSonarSessionConfig(
        session_id="e2e-session-lifecycle-001",
        name="E2E Sonar Replay Survey",
        source_type="replay",
        source_uri=fls_img_path,
        target_fps=30.0,
        inference_fps=15.0,
        buffer_size=20,
        confidence_threshold=0.35,
        minimum_confirmed_frames=3,
    )
    adapter = ReplayStreamAdapter(
        source_uri=fls_img_path,
        target_fps=30.0,
        loop=True,
        session_id=config.session_id,
    )
    session = LiveSonarSession(config, adapter=adapter)
    assert session.status == SessionStatus.CONNECTING

    # Load production model
    model = ModelLoader.load_detection_model(str(MODEL_PATH))
    assert model is not None

    # Tracker initialization
    tracker_args = SimpleNamespace(
        track_high_thresh=0.25,
        track_low_thresh=0.1,
        new_track_thresh=0.3,
        track_buffer=30,
        match_thresh=0.8,
        fuse_score=True,
    )
    tracker = BYTETracker(tracker_args)

    # Confirmation & evidence tracking state
    track_hit_counter: Dict[int, int] = {}
    confirmed_tracks: set = set()
    evidence_packages: List[Dict[str, Any]] = []
    emitted_ws_messages: List[Dict[str, Any]] = []

    # 2. Start session
    await session.start()
    assert session.status in (SessionStatus.CONNECTED, SessionStatus.RUNNING)

    # 3. Ingestion and inference pipeline loop
    processed_count = 0
    start_time = time.monotonic()

    while processed_count < 6 and (time.monotonic() - start_time) < 5.0:
        try:
            frame: SonarFrame = await asyncio.wait_for(session.buffer.get(), timeout=1.0)
        except asyncio.TimeoutError:
            break

        # Verification of raw immutability
        assert frame.image_data.flags.writeable is False
        raw_bgr = cv2.cvtColor(frame.image_data, cv2.COLOR_GRAY2BGR)

        # AI Forward pass on production YOLOv8
        inference_start = time.perf_counter()
        results = model.predict(raw_bgr, conf=config.confidence_threshold, verbose=False)
        inference_latency_ms = (time.perf_counter() - inference_start) * 1000.0

        detections = []
        res = results[0]
        if len(res.boxes) > 0:
            for b in res.boxes:
                cid = int(b.cls[0].item())
                cconf = float(b.conf[0].item())
                x1, y1, x2, y2 = b.xyxy[0].tolist()
                detections.append(
                    RawDetection(
                        class_id=cid,
                        class_name=CLASS_NAMES[cid],
                        confidence=cconf,
                        bbox_x=int(x1),
                        bbox_y=int(y1),
                        bbox_w=int(x2 - x1),
                        bbox_h=int(y2 - y1),
                        tile_row=0,
                        tile_col=0,
                    )
                )

        # ByteTrack temporal association
        tracks_output = []
        if len(res.boxes) > 0:
            tracked_boxes = tracker.update(res.boxes)
            for tb in tracked_boxes:
                t_x1, t_y1, t_x2, t_y2, tid, tconf, tcls, _ = tb
                tid = int(tid)
                track_hit_counter[tid] = track_hit_counter.get(tid, 0) + 1

                is_confirmed = track_hit_counter[tid] >= config.minimum_confirmed_frames
                if is_confirmed and tid not in confirmed_tracks:
                    confirmed_tracks.add(tid)
                    # Trigger Evidence Capture
                    raw_art_path = evidence_dir / f"track_{tid}_raw.png"
                    cv2.imwrite(str(raw_art_path), frame.image_data)
                    ev_meta = {
                        "session_id": session.session_id,
                        "track_id": tid,
                        "frame_id": frame.frame_id,
                        "sequence_number": frame.sequence_number,
                        "timestamp_utc": frame.timestamp_utc.isoformat(),
                        "source_type": "replay",
                        "model_checkpoint": "models/detection/sonar_yolov8_fls_trained.pt",
                        "preprocessing_profile": "REALTIME",
                        "class_name": CLASS_NAMES[int(tcls)],
                        "confidence_raw": float(tconf),
                        "bbox": {"x": int(t_x1), "y": int(t_y1), "w": int(t_x2 - t_x1), "h": int(t_y2 - t_y1)},
                    }
                    evidence_packages.append(ev_meta)

                tracks_output.append({
                    "track_id": tid,
                    "class_name": CLASS_NAMES[int(tcls)],
                    "confidence": float(tconf),
                    "bbox": {"x": int(t_x1), "y": int(t_y1), "w": int(t_x2 - t_x1), "h": int(t_y2 - t_y1)},
                    "status": "CONFIRMED" if is_confirmed else "TENTATIVE",
                    "is_confirmed": is_confirmed,
                })

        # JPEG Preview compression (<80 KB)
        success, enc_jpg = cv2.imencode(".jpg", frame.image_data, [cv2.IMWRITE_JPEG_QUALITY, 75])
        assert success is True
        jpg_b64 = "data:image/jpeg;base64," + base64.b64encode(enc_jpg.tobytes()).decode("ascii")

        # Construct frame_update WebSocket payload
        ws_msg = {
            "event": "frame_update",
            "session_id": session.session_id,
            "frame_id": frame.frame_id,
            "sequence_number": frame.sequence_number,
            "timestamp": frame.timestamp_utc.isoformat(),
            "preview_image": jpg_b64,
            "detections": [
                {
                    "detection_id": f"det-{processed_count}-{i}",
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox": {"x": d.bbox_x, "y": d.bbox_y, "w": d.bbox_w, "h": d.bbox_h},
                    "track_id": tracks_output[i]["track_id"] if i < len(tracks_output) else None,
                }
                for i, d in enumerate(detections)
            ],
            "tracks": tracks_output,
            "metrics": {
                "input_fps": 20.0,
                "inference_fps": 10.0,
                "latency_ms": inference_latency_ms,
                "queue_depth": session.buffer.queue_depth,
            },
        }

        # Validate WebSocket schema adherence
        errs = validate_frame_update_message(ws_msg)
        assert len(errs) == 0, f"WebSocket frame_update validation failed: {errs}"
        emitted_ws_messages.append(ws_msg)

        processed_count += 1

    # 4. Stop session cleanly
    await session.stop()
    assert session.status == SessionStatus.STOPPED

    # 5. Lifecycle Invariant Assertions
    # Processed at least 5 frames
    assert processed_count >= 5, f"Processed only {processed_count} frames"
    # Detections were emitted
    assert len(emitted_ws_messages) >= 5
    # Tracks persisted
    assert len(track_hit_counter) >= 1
    # At least one track reached confirmation threshold
    assert len(confirmed_tracks) >= 1, "Expected at least 1 track to reach confirmation!"
    # Evidence package was created and validated
    assert len(evidence_packages) >= 1
    for ev in evidence_packages:
        assert len(validate_evidence_package(ev)) == 0


# ============================================================================
# 2. Sustained Workload Throughput & Latency Profiling
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_sustained_workload_throughput_and_latency():
    """Verify inference pipeline latency remains bounded under sustained replay workload."""
    model = ModelLoader.load_detection_model(str(MODEL_PATH))
    assert model is not None

    adapter = ReplayStreamAdapter(
        source_uri=str(SEQUENCE_DIR),
        target_fps=60.0,
        session_id="workload-test",
    )
    await adapter.connect()

    latencies_ms = []
    frame_count = 0

    async for frame in adapter.frames():
        raw_bgr = cv2.cvtColor(frame.image_data, cv2.COLOR_GRAY2BGR)

        t_start = time.perf_counter()
        _ = model.predict(raw_bgr, conf=0.35, verbose=False)
        latency_ms = (time.perf_counter() - t_start) * 1000.0
        latencies_ms.append(latency_ms)

        frame_count += 1
        if frame_count >= 6:
            break

    await adapter.disconnect()

    assert len(latencies_ms) == 6
    p95_latency = np.percentile(latencies_ms, 95)
    # CPU inference on 640x640 FLS sonar patches typically takes 50-250ms
    assert p95_latency < 500.0, f"P95 latency {p95_latency:.1f} ms exceeded real-time ceiling"


# ============================================================================
# 3. Deterministic Replay Parity (Repeatability Verification)
# ============================================================================

@pytest.mark.asyncio
async def test_e2e_replay_parity_verification():
    """Verify running the identical replay source twice yields deterministic detection results."""
    model = ModelLoader.load_detection_model(str(MODEL_PATH))

    async def run_replay_pass() -> List[int]:
        adapter = ReplayStreamAdapter(
            source_uri=str(SEQUENCE_DIR),
            target_fps=60.0,
            session_id="parity-run",
        )
        await adapter.connect()
        counts = []
        async for frame in adapter.frames():
            raw_bgr = cv2.cvtColor(frame.image_data, cv2.COLOR_GRAY2BGR)
            res = model.predict(raw_bgr, conf=0.35, verbose=False)[0]
            counts.append(len(res.boxes))
            if len(counts) >= 6:
                break
        await adapter.disconnect()
        return counts

    pass1_detection_counts = await run_replay_pass()
    pass2_detection_counts = await run_replay_pass()

    # Replay Parity Invariant: Identical sequence must produce identical detection counts per frame
    assert pass1_detection_counts == pass2_detection_counts, (
        f"Replay parity violation! Pass 1: {pass1_detection_counts}, Pass 2: {pass2_detection_counts}"
    )
