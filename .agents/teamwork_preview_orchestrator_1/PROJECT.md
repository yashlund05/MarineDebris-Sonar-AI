# Project: Live Sonar AI Detection & Tracking Subsystem

## Architecture
The Live Sonar subsystem is a modular, production-grade real-time acoustic streaming, detection, tracking, and visualization system.
Data Flow:
```
SONAR SOURCE (Replay/RTSP/USB/Native)
       │
       ▼
SOURCE ADAPTER (SonarStreamAdapter ABC -> SonarFrame)
       │
       ▼
BOUNDED FRAME BUFFER (drop_oldest / FIFO / LATEST, backpressure metrics)
       │
       ▼
PREPROCESSING PIPELINE (REALTIME / BALANCED / QUALITY profiles reusing backend/preprocessing/)
       │
       ▼
AI INFERENCE WORKER (ModelLoader singleton, sonar_yolov8_fls_trained.pt, detect_tiles, frame skipping)
       │
       ▼
TEMPORAL TRACKING (ByteTrack 2-stage association, Kalman filter, N-of-M confirmation)
       │
       ▼
GEOSPATIAL & SHADOW REASONING (Georeferencing or NOT_AVAILABLE, down-range acoustic shadow support)
       │
       ├──► DATABASE & EVIDENCE (LiveSonarSession, LiveTrack, LiveDetectionEvent, LiveEvidence, Alembic migration)
       │
       ▼
REDIS PUB/SUB & WEBSOCKET (/ws/live-sonar/{session_id}, preview JPEG/WebP + telemetry)
       │
       ▼
FRONTEND CANVAS VIEWPORT (RAW / ENHANCED / AI / SPLIT, targets panel, inspection drawer, metrics bar, controls)
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | SonarStreamAdapter ABC | Abstract base class defining connect, disconnect, frames, health, metadata | M1 | R1 |
| 2 | ReplayStreamAdapter | Stream adapter for PNG sequences, MP4, and synthetic sonar streams | M1 | R1 |
| 3 | RTSPStreamAdapter | Safe RTSP streaming decoder with reconnect and timeout logic | M1 | R1 |
| 4 | USBCameraStreamAdapter | Local video/camera device capture adapter | M1 | R1 |
| 5 | NativeSonarStubAdapter | ARIS-class hardware adapter boundary (reports NOT_CONFIGURED when no hardware) | M1 | R1 |
| 6 | SonarFrame Data Model | Immutable raw image, sonar metadata, navigation data, timestamps, quality flags | M1 | R1 |
| 7 | Bounded Async Frame Buffer | Ring buffer with DROP_OLDEST, FIFO, DROP_NEWEST, LATEST policies & drop metrics | M1 | R1 |
| 8 | Backpressure Telemetry | Exposure of input_fps, processing_fps, effective_fps, latency_ms, drop_rate | M1 | R1 |
| 9 | LiveSonarSession Manager | Lifecycle management (CONNECTING, CONNECTED, RUNNING, DEGRADED, STOPPING, STOPPED, ERROR) | M1 | R1 |
| 10 | Live Sonar Config Extension | Pydantic Settings for LIVE_SONAR_* flags and buffer thresholds | M1 | R1 |
| 11 | Preprocessing Profile Integration | Configurable profiles (REALTIME, BALANCED, QUALITY) reusing backend/preprocessing | M2 | R2 |
| 12 | Raw Frame Immutability | Strict separation of raw_frame, processed_frame, model_frame, annotated_frame | M2 | R2 |
| 13 | ModelLoader Inference Worker | Threaded/async inference loop decoupled from acquisition, frame skipping | M2 | R2 |
| 14 | ByteTrack Temporal Tracking | SonarObjectTracker interface wrapping BYTETracker with 2-stage association | M2 | R2 |
| 15 | Temporal Confirmation N-of-M | N-of-M frame confirmation gating to suppress single-frame false alarms | M2 | R2 |
| 16 | Class Consistency Filter | Smoothing class labels across track lifetime to prevent flickering | M2 | R2 |
| 17 | Acoustic Shadow Reasoning | Detection of down-range acoustic shadow support (detected / unavailable) | M2 | R2 |
| 18 | Geolocation Fallback Contract | Georeferencing when nav data exists; explicit GPS: NOT_AVAILABLE otherwise | M2 | R2 |
| 19 | LiveDetectionEvent Model | Pydantic and internal model capturing event, frame, track, bbox, conf, latency | M2 | R2 |
| 20 | WebSocket Stream Endpoint | `/ws/live-sonar/{session_id}` over Redis pub/sub with preview JPEG/WebP | M3 | R3 |
| 21 | WebSocket Protocol Events | session_started, session_stopped, connection_lost, track_confirmed, etc. | M3 | R3 |
| 22 | REST Session CRUD API | POST/GET `/api/v1/live-sonar/sessions`, GET detail, POST start/stop | M3 | R3 |
| 23 | REST Query Endpoints | GET `/api/v1/live-sonar/sessions/{id}/metrics|tracks|detections|evidence` | M3 | R3 |
| 24 | Health & Security Endpoint | Health check reporting real source, FPS, queue depth, GPU, model; SSRF validation | M3 | R3 |
| 25 | Database Schema Models | SQLAlchemy models: LiveSonarSession, LiveTrack, LiveDetectionEvent, LiveEvidence | M4 | R5 |
| 26 | Alembic Migration | `0003_live_sonar_subsystem.py` revision cleanly branching from 0002 | M4 | R5 |
| 27 | Evidence Capture Engine | Automated capture of raw/enhanced/annotated evidence on confirmed tracks | M4 | R5 |
| 28 | Session Recording Engine | Recording raw frames, telemetry, detections to local storage artifact conventions | M4 | R5 |
| 29 | Live Sonar Page Route & Shell | `/live-sonar` route, AppLayout integration, Sidebar navigation, Navbar breadcrumb | M5 | R4 |
| 30 | Canvas Viewport & Modes | Double-buffered Canvas 2D/WebGL rendering RAW, ENHANCED, AI, SPLIT modes | M5 | R4 |
| 31 | AI Overlay Visualization | Bounding boxes, track ID badges, trajectory trails, acoustic shadow indicators | M5 | R4 |
| 32 | Active Targets & Inspector Drawer | Real targets list; inspection drawer showing NOT_AVAILABLE for missing telemetry | M5 | R4 |
| 33 | Real-Time Metrics Bar | Runtime INPUT/INFERENCE/DISPLAY FPS, LATENCY, QUEUE DEPTH, DROPS, GPU | M5 | R4 |
| 34 | Connection & Stream Controls | Connect modal, Record, Snapshot, Layer Toggles, LIVE/REPLAY badge, disconnect alert | M5 | R4 |
| 35 | Replay Control Deck | Play/pause, step frame, 0.25x-4x speed selection, seek scrubber | M5 | R4 |
| 36 | E2E Test Suite (Tiers 1-4) | Systematic Category-Partition, BVA, Pairwise, Real-World Replay test cases | E2E-Track | R6 |
| 37 | Deterministic Replay Fixture | Automated E2E verification stream using ARIS 3K FLS sonar imagery | E2E-Track | R6 |
| 38 | Final Verification & Hardening | 100% test pass, Tier 5 adversarial coverage audit, regression check, zero fake data | M6 | R6 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| E2E | E2E Testing Track | Test infra, Tier 1-4 test cases, replay fixture, TEST_READY.md | none | IN_PROGRESS |
| M1 | Streaming Infrastructure | SonarFrame, Adapters (Replay/RTSP/USB/Native), Buffer, Session, Config | none | IN_PROGRESS |
| M2 | AI Pipeline & Tracking | Preprocessing profiles, ModelLoader worker, ByteTrack, N-of-M confirmation | M1 | PLANNED |
| M3 | WebSocket & REST API | `/ws/live-sonar/{session_id}`, `/api/v1/live-sonar/` REST routes, Security | M1, M2 | PLANNED |
| M4 | Persistence & Evidence | DB models, Alembic migration 0003, recording & evidence capture | M1, M2 | PLANNED |
| M5 | Frontend Live Sonar UI | React `/live-sonar`, Canvas viewport, 4 view modes, targets, metrics, controls | M3 | PLANNED |
| M6 | Final Verification & Hardening| Pass 100% E2E tests, Tier 5 adversarial hardening, regression check | M1-M5, E2E | PLANNED |

## Interface Contracts

### M1 ↔ M2: SonarFrame Acquisition to Processing
```python
class SonarFrame:
    frame_id: str
    sequence_number: int
    timestamp_utc: datetime
    source_type: str
    source_uri: str
    raw_image: np.ndarray          # 2D uint8/float32 grayscale, immutable
    sonar_metadata: SonarMetadataPayload | None # freq, range_m, gain, beam_angle, etc.
    navigation: NavPayload | None               # lat, lon, heading, depth, speed
    quality_flags: QualityPayload
```

### M2 ↔ M3 / M4: Processed Frame & Live Detections
```python
class LiveDetectionPayload:
    detection_id: str
    track_id: int
    class_id: int
    class_name: str
    confidence: float
    bbox_xyxy: list[float]         # [x1, y1, x2, y2]
    is_confirmed: bool
    confirmation_count: int
    has_acoustic_shadow: bool | None
    sonar_range_m: float | None
    coordinates: dict | None       # {"lat": ..., "lon": ...} or None

class FrameOutputMessage:
    session_id: str
    frame_id: str
    sequence_number: int
    timestamp_utc: str
    preview_jpeg_b64: str          # JPEG compressed preview (<80KB)
    enhanced_jpeg_b64: str | None  # Available if enhanced mode active
    detections: list[LiveDetectionPayload]
    metrics: LiveMetricsPayload
```

### M3 ↔ M5: WebSocket Protocol
- Channel: `/ws/live-sonar/{session_id}`
- Message types:
  - `frame_update`: FrameOutputMessage
  - `session_event`: event type (`session_started`, `session_stopped`, `track_confirmed`, etc.)
  - `heartbeat`: ping/pong with timestamp

## Code Layout & Write Ownership Boundaries
- **M1**: `backend/live_sonar/models.py`, `backend/live_sonar/buffer.py`, `backend/live_sonar/session.py`, `backend/live_sonar/adapters/*`, `backend/config.py` (live settings additions only).
- **M2**: `backend/live_sonar/pipeline/*`, `backend/live_sonar/tracker.py`, `backend/live_sonar/confirmation.py`, `backend/live_sonar/shadow.py`.
- **M3**: `backend/live_sonar/api/*`, `backend/api/routers/live_sonar.py`, `backend/api/main.py` (mounting router).
- **M4**: `backend/database/models.py` (adding live models only), `backend/database/migrations/versions/0003_live_sonar_subsystem.py`, `backend/live_sonar/recording/*`.
- **M5**: `frontend/src/features/live-sonar/*`, `frontend/src/components/live-sonar/*`, `frontend/src/App.tsx`, `frontend/src/components/layout/Sidebar.tsx`, `frontend/src/components/layout/Navbar.tsx`.
- **E2E Testing Track**: `tests/live_sonar/*`, `tests/fixtures/live_sonar/*`, `TEST_INFRA.md`, `TEST_READY.md`.

## Immutability & Safety Rules
1. `models/detection/sonar_yolov8_fls_trained.pt` must remain byte-identical (SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`).
2. `datasets/sonar_debris_v2_clean` must remain untouched.
3. No fake data: Missing telemetry or GPS must be `null` in backend and render `NOT_AVAILABLE` in frontend.
4. Existing offline survey processing, evaluation endpoints, and offline inference remain intact.
