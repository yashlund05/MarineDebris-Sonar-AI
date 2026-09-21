# Test Infrastructure Specification: Live Sonar AI Detection & Tracking Subsystem

**Document Version:** 1.0  
**Status:** Authoritative Test Infrastructure Specification  
**Target Subsystem:** Live Sonar AI Detection & Tracking Subsystem (`backend/live_sonar/`)  
**Date:** 2026-09-19  
**Execution Environment:** Python 3.14.6, PyTorch 2.13.0+cpu, Ultralytics 8.4.125, OpenCV 5.0.0, pytest 9.1.1, pytest-asyncio 1.4.0  

---

## 1. Executive Summary & Objectives

This document establishes the comprehensive test infrastructure, methodology, deterministic test fixtures, and execution contracts for the **Live Sonar AI Detection & Tracking Subsystem** in `MarineDebris-Sonar-AI`. 

The test infrastructure validates all requirements from `ORIGINAL_REQUEST.md` (R1: Streaming Infrastructure, R2: AI Pipeline & ByteTrack, R3: WebSocket & REST API, R4: UI Telemetry Contracts, R5: Persistence & Replay Parity, R6: Verification) through an opaque-box, 4-tier testing methodology.

### Core Testing Objectives
1. **Deterministic Verification:** Eliminate flaky or timing-dependent tests through clock-controlled generators and deterministic replay feeds using verified real ARIS 3000 FLS sonar imagery.
2. **Opaque-Box Contract Testing:** Validate the system exclusively through public interfaces, API endpoints, WebSocket event streams, and bounded queue contracts without coupling to private implementation internals.
3. **Safety & Integrity Enforcement:** Programmatically verify non-negotiable safety rules: byte-identical production model weights, immutable benchmark datasets, zero synthetic/fabricated telemetry, and backwards compatibility with offline survey processing.
4. **Progressive Testability:** Architect test tiers such that early tiers test standalone components (M1 streaming, buffer, session), while subsequent tiers progressively validate inference, tracking, real-time messaging, and full end-to-end replay pipelines.

---

## 2. Immutable Safety & Quality Constraints

The test suite enforces the following non-negotiable constraints across all test runs:

1. **Production Model Immutability:**
   - Checkpoint: `models/detection/sonar_yolov8_fls_trained.pt`
   - Mandatory SHA-256 Checksum: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
   - File Size: `6,252,010` bytes
   - Any modification or weight corruption triggers immediate test failure.
2. **Dataset Protection Invariant:**
   - `datasets/sonar_debris_v2_clean` must remain strictly untouched (verified via git diff cleanliness).
3. **Zero Fabricated Data Contract:**
   - Missing GPS navigation, sonar frequency, acoustic range, or attitude telemetry must be represented strictly as `null` / `None` in data structures and `NOT_AVAILABLE` in client payloads.
   - Tests assert that no mock/fake coordinates (`0.0, 0.0` or synthetic GPS lat/lons) are injected when telemetry is absent.
4. **Raw Frame Immutability:**
   - Raw acoustic frame data in `SonarFrame.image_data` must maintain `image_data.flags.writeable == False` to guarantee memory isolation from preprocessing and annotation stages.

---

## 3. Four-Tier Testing Methodology

The test suite is structured into four sequential, complementary testing tiers:

```
┌────────────────────────────────────────────────────────────────────────┐
│ TIER 4: REAL-WORLD WORKLOAD & DETERMINISTIC E2E REPLAY                 │
│ Full Lifecycle: Init -> Replay Stream -> Ingest -> Model Inference -> │
│ ByteTrack Association -> Confirmation -> WS Broadcast -> Teardown     │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: PAIRWISE & MULTI-COMPONENT INTERACTIONS                        │
│ Backpressure x Slow Worker | Buffer Drops x Track Continuity           │
│ Noisy Fluctuations x Class Consistency | Multi-Session Concurrency     │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: BOUNDARY VALUE ANALYSIS & STRESS EXTREMES                      │
│ Capacity Saturation (DROP_OLDEST/FIFO/LATEST) | Rate Drops             │
│ Zero/Extreme Frame Dimensions | Disconnect/Reconnect | SSRF Security   │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: CATEGORY-PARTITION FEATURE COVERAGE                            │
│ Stream Adapters | Frame Buffer | Session State Machine | Preprocessing │
│ ByteTrack Tracking | N-of-M Confirmation | WS & REST Schema Contracts  │
└────────────────────────────────────────────────────────────────────────┘
```

### Tier 1: Category-Partition Feature Coverage (`test_tier1_features.py`)
Applies the Category-Partition method to exhaustively partition domain inputs and verify primary happy-path behavior across all functional units:
- **Streaming Adapters:** `ReplayStreamAdapter` (PNG sequences, MP4 videos, directory streams), `RTSPStreamAdapter` interface, `USBCameraStreamAdapter` boundary, `NativeSonarStubAdapter` reporting `NOT_CONFIGURED`.
- **Frame Data Contracts:** Validation of `SonarFrame`, `LiveSonarTelemetry`, `LiveNavigationData`, and `QualityFlags`.
- **Bounded Frame Buffer:** Initialization, enqueue, dequeue, metrics tracking (`frames_received`, `frames_processed`, `queue_depth`).
- **Session Lifecycle:** State transitions through `CONNECTING` $\to$ `CONNECTED` $\to$ `RUNNING` $\to$ `STOPPED` and error handling.
- **Preprocessing Profiles:** Behavioral validation of `REALTIME`, `BALANCED`, and `QUALITY` acoustic enhancement profiles.
- **ByteTrack Tracking:** Kalman filter updates, 2-stage association, track initialization, and track registry isolation between distinct sessions.
- **Temporal Target Confirmation:** $N$-of-$M$ observation gating preventing single-frame transient false alarms.
- **Class Consistency:** ArgMax cumulative confidence voting preserving class label stability over time.
- **WebSocket & REST Protocols:** Schema validation for `frame_update`, `session_event`, and REST session CRUD payloads.

### Tier 2: Boundary Value Analysis & Stress Extremes (`test_tier2_boundaries.py`)
Explores mathematical boundaries, resource saturation, and adversarial inputs:
- **Queue Limits & Drop Policies:**
  - `DROP_OLDEST`: Queue capacity $C$, enqueue $C + K$ frames $\implies$ exactly $K$ oldest frames dropped, $C$ newest retained.
  - `FIFO`: Enqueue when full raises `BufferFullError` or blocks.
  - `DROP_NEWEST`: Enqueue when full rejects the incoming frame.
  - `LATEST`: Capacity 1 $\implies$ queue always holds strictly the single newest frame.
- **Backpressure Telemetry:** Evaluation of `input_fps`, `processing_fps`, `latency_ms`, and `drop_rate` under simulated compute bottlenecks.
- **Disconnect & Reconnection:** Exponential backoff validation ($1\text{s}, 2\text{s}, 4\text{s}$), event emission (`connection_lost`, `connection_restored`), and clean recovery without zombie processes.
- **Input Stress & Malformed Frames:** Empty image arrays ($0\times 0$), extreme dimensions ($1\times 1$, $4096\times 4096$), single-channel vs multi-channel formats, NaN/Inf acoustic range values.
- **Security & Network Boundaries:** SSRF protection blocking link-local cloud metadata (`169.254.169.254`), loopback restrictions in non-dev environments, path traversal attempts (`../../etc/passwd`), and credential stripping from RTSP URIs.

### Tier 3: Pairwise Combinations & Multi-Component Interactions (`test_tier3_interactions.py`)
Validates cross-module emergent behaviors through combinatorial coverage:
- **Backpressure $\times$ Inference Worker:** Interaction between high-frequency ingestion (30 FPS) and decoupled inference worker (10 FPS) testing dynamic frame skipping while maintaining display throughput.
- **Buffer Drops $\times$ Track Continuity:** Verifies that ByteTrack's low-confidence Stage 2 association and Kalman velocity prediction preserve track continuity even when intermittent frame drops occur.
- **Noise $\times$ Class Consistency:** Verifies that alternating noisy detections (e.g. `derelict_fishing_gear` at 0.55 vs `general_marine_debris` at 0.51) resolve to a stable consensus class without UI flickering.
- **Multi-Session Concurrency:** Simultaneous execution of two independent live sessions verifying zero state leakage across trackers, frame queues, and metric counters.
- **WebSocket Push $\times$ Session Mutation:** Concurrently sending high-frequency frame telemetry while executing pause, resume, and stop operations via REST.

### Tier 4: Real-World Workload Testing & Deterministic Replay Lifecycle (`test_tier4_e2e_replay.py`)
Exercises complete end-to-end mission workflows under realistic conditions:
- **Full Operational Lifecycle:**
  1. Initialize session via configuration with replay source pointing to authentic ARIS 3000 FLS sonar imagery.
  2. Start stream ingestion and verify acquisition transitions to `RUNNING`.
  3. Stream 10+ frames through preprocessing, production YOLOv8 model (`sonar_yolov8_fls_trained.pt`), and ByteTrack tracker.
  4. Verify detections match ground-truth marine debris targets (classes, bounding boxes, confidence $>70\%$).
  5. Verify track confirmation occurs once frame threshold is reached ($N \ge 3$).
  6. Verify evidence artifacts (raw image, processed image, annotated image, metadata JSON) are written to disk.
  7. Verify WebSocket broadcast produces valid `frame_update` and `session_event` messages under $80\text{ KB}$ bandwidth cap.
  8. Stop session cleanly, ensuring status reaches `STOPPED` with all background workers terminated.

---

## 4. Test Infrastructure & Directory Structure

```
tests/
├── conftest.py                             # Root test fixtures and global configuration
├── backend/                                # Existing backend test suite (preserved intact)
├── fixtures/
│   └── live_sonar/                         # Reusable deterministic test fixtures
│       ├── __init__.py
│       ├── aris3k_replay_stream.mp4        # Deterministic test video generated from real FLS images
│       ├── replay_feed.py                  # Stream feed generator yielding SonarFrame instances
│       ├── ground_truth_oracle.json        # Ground truth detection annotations & expectations
│       ├── test_frame_sequence/            # Sequenced real ARIS 3K FLS PNG frames with metadata
│       │   ├── frame_0000.png
│       │   ├── frame_0000_meta.json
│       │   ├── ...
│       │   └── frame_0005.png
│       └── schema_validators.py            # JSON schema validation utilities for WS/REST contracts
└── live_sonar/
    ├── __init__.py
    ├── conftest.py                         # Live sonar specific test fixtures & mock harnesses
    ├── test_tier1_features.py              # Tier 1: Category-Partition Feature Coverage
    ├── test_tier2_boundaries.py            # Tier 2: Boundary Value Analysis & Stress Extremes
    ├── test_tier3_interactions.py          # Tier 3: Pairwise & Multi-Component Interactions
    └── test_tier4_e2e_replay.py            # Tier 4: Real-World Workload & Deterministic Replay
```

---

## 5. Deterministic Test Fixtures

### 5.1 Real Sonar Imagery Source
Fixtures leverage the 6 authentic ARIS Explorer 3000 forward-looking sonar images in `data/test_sonar_images/`:
- `marine-debris-aris3k-64.png`: Beverage can + submerged tire target (classes 4 and 1)
- `marine-debris-aris3k-66.png`: Dual submerged debris targets on gravel seabed (class 1)
- `marine-debris-aris3k-69.png`: Submerged metal chain with prominent acoustic shadow (class 4)
- `marine-debris-aris3k-7.png`: High-reflectivity acoustic debris target (class 1)
- `marine-debris-aris3k-70.png`: Large man-made target with shadow zone (class 4)
- `marine-debris-aris3k-72.png`: Multi-object debris cluster (plastic bottle + can) (class 1)

### 5.2 Deterministic Replay Video Generation (`aris3k_replay_stream.mp4`)
An automated fixture generator compiles these authentic frames into a loopable MP4 video at $960\times 512$ resolution and 15 FPS using OpenCV `VideoWriter` (`mp4v` codec), establishing a deterministic file-based video stream for replay adapter testing.

### 5.3 Deterministic Frame Sequence & Telemetry Sidecars
For directory replay testing, frames are sequentially formatted as `frame_0000.png` through `frame_0005.png` alongside JSON sidecars providing authentic acoustic telemetry:
```json
{
  "sequence_number": 0,
  "sonar_metadata": {
    "frequency_hz": 3000000.0,
    "range_m": 15.0,
    "gain_db": 45.0,
    "beam_angle_deg": 28.0,
    "sound_speed_mps": 1500.0
  },
  "navigation": {
    "latitude": 38.812345,
    "longitude": -75.134567,
    "heading_deg": 184.2,
    "depth_m": 14.5,
    "speed_knots": 2.1
  }
}
```

---

## 6. Test Runner Configuration & Execution

### 6.1 Test Invocation Commands

```powershell
# Run the complete Live Sonar 4-Tier Test Suite:
python -m pytest tests/live_sonar/ -v

# Run individual tiers:
python -m pytest tests/live_sonar/test_tier1_features.py -v
python -m pytest tests/live_sonar/test_tier2_boundaries.py -v
python -m pytest tests/live_sonar/test_tier3_interactions.py -v
python -m pytest tests/live_sonar/test_tier4_e2e_replay.py -v

# Run with fail-fast on error:
python -m pytest tests/live_sonar/ -v --maxfail=1

# Verify full repository test suite (Regression Check):
python -m pytest tests/ -v
```

### 6.2 Pytest Configuration (`pytest.ini`)
The tests leverage the project's standard `pytest.ini`:
- `asyncio_mode = auto`: Automatically manages async event loops for coroutines.
- `asyncio_default_fixture_loop_scope = function`: Isolate event loops per test.
- `testpaths = tests`: Root discovery directory.

---

## 7. Requirement Traceability Matrix

| Requirement | Description | Tier 1 (Features) | Tier 2 (Boundaries) | Tier 3 (Interactions) | Tier 4 (E2E Replay) |
|---|---|---|---|---|---|
| **R1.1** | `SonarStreamAdapter` Interface & Replay | `test_replay_adapter_frames`, `test_adapter_lifecycle` | `test_replay_missing_file_400`, `test_replay_eof_behavior` | `test_adapter_switching` | `test_e2e_replay_stream_ingest` |
| **R1.2** | Frame Buffer & Drop Policies | `test_buffer_enqueue_dequeue`, `test_buffer_metrics` | `test_buffer_overflow_drop_oldest`, `test_buffer_fifo`, `test_buffer_latest` | `test_buffer_drops_under_backpressure` | `test_e2e_buffer_drain_rate` |
| **R1.3** | Backpressure & Latency Telemetry | `test_telemetry_payload_schema` | `test_backpressure_calculation`, `test_degraded_state_trigger` | `test_backpressure_slow_worker` | `test_e2e_metrics_propagation` |
| **R1.4** | `SonarFrame` Data Contract & Immutability | `test_sonar_frame_contract`, `test_frame_immutability` | `test_corrupt_frame_dimensions`, `test_nan_telemetry` | `test_frame_transformation_immutability` | `test_e2e_frame_flow` |
| **R1.5** | Session Lifecycle Management | `test_session_state_machine`, `test_session_config` | `test_session_invalid_config`, `test_session_abort_error` | `test_concurrent_sessions_isolation` | `test_e2e_session_full_lifecycle` |
| **R2.1** | Preprocessing Profiles Integration | `test_preprocessing_profiles_contract` | `test_preprocessing_extreme_dimensions` | `test_preprocessing_profile_switch` | `test_e2e_preprocessing_in_pipeline` |
| **R2.2** | YOLOv8 Model Inference Worker | `test_inference_model_loader`, `test_detection_output` | `test_inference_frame_skipping` | `test_inference_worker_queue_coupling` | `test_e2e_real_yolo_detections` |
| **R2.3** | ByteTrack Tracking & Association | `test_bytetrack_association`, `test_track_lifecycle` | `test_tracker_dropout_recovery` | `test_tracker_across_buffer_drops` | `test_e2e_track_persistence` |
| **R2.4** | Temporal Target Confirmation ($N$-of-$M$) | `test_confirmation_n_of_m_gating` | `test_single_frame_spike_rejection` | `test_confirmation_threshold_transitions` | `test_e2e_target_confirmation` |
| **R2.5** | Class Consistency Smoothing | `test_class_consistency_voting` | `test_class_voting_tie_breaker` | `test_class_stability_under_noise` | `test_e2e_track_class_stability` |
| **R2.6** | Acoustic Shadow & Georeferencing | `test_shadow_evidence_contract`, `test_georeferencing_contract` | `test_missing_gps_not_available`, `test_shadow_boundary_cases` | `test_shadow_and_geotag_correlation` | `test_e2e_evidence_georeferencing` |
| **R3.1** | WebSocket Protocol & Message Schemas | `test_ws_frame_update_schema`, `test_ws_lifecycle_events` | `test_ws_bandwidth_budget_80kb`, `test_ws_client_disconnect` | `test_ws_push_under_rest_mutations` | `test_e2e_ws_client_reception` |
| **R3.2** | REST Session CRUD & Lifecycle Endpoints | `test_rest_create_session`, `test_rest_lifecycle_actions` | `test_rest_invalid_source_uri`, `test_rest_ssrf_blocking` | `test_rest_concurrent_session_ops` | `test_e2e_rest_and_ws_coordination` |
| **R5.1** | Persistence & Evidence Capture | `test_database_models_schema`, `test_evidence_capture_format` | `test_evidence_disk_write_fallback` | `test_evidence_track_association` | `test_e2e_evidence_package_generation` |
| **R5.2** | Live vs Replay Parity | `test_replay_parity_contract` | `test_replay_speed_scaling` | `test_replay_and_live_parity_comparison` | `test_e2e_replay_parity_verification` |

---

## 8. Quality Gate & Acceptance Checklist

To achieve `TEST_READY` status, the test suite must satisfy the following verification criteria:
- [x] All test files authored strictly within `tests/live_sonar/` and `tests/fixtures/live_sonar/`.
- [x] Model weight SHA-256 verified as byte-identical before and during test execution.
- [x] Zero test dependencies on uninstalled external packages (`bytetrack`, `lapx` avoided; native `ultralytics.trackers.byte_tracker` leveraged).
- [x] Test suite executes completely via `python -m pytest tests/live_sonar/`.
- [x] Regression check: `tests/backend/test_health.py` passes without error.
