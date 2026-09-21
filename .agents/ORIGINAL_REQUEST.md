# Original User Request

## 2026-09-18T18:05:34Z

Implement a production-grade **Live Sonar AI Detection & Tracking subsystem** inside the existing `MarineDebris-Sonar-AI` repository. The system receives a continuous sonar frame stream, preprocesses frames using the existing sonar pipeline, performs AI detection using the existing production detector, maintains temporal object identities across frames via ByteTrack, and displays the live annotated sonar feed in the existing React/TypeScript frontend over WebSocket.

Working directory: `c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar`
Integrity mode: development

---

## Existing Repository Context

The existing codebase is a **FastAPI + React/TypeScript** marine sonar debris detection system:

- **Backend**: Python, FastAPI, SQLAlchemy 2.0 (async), Alembic, Celery, Redis pub/sub, YOLOv8 (ultralytics)
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, TanStack Query, Zustand, Recharts, Lucide icons
- **Database**: PostgreSQL via SQLAlchemy async session
- **Existing features**: Survey ingestion, sonar preprocessing (CLAHE, denoising, normalization, tiling), detection inference, dataset explorer, model registry, report generation, georeferencing, enhancement workbench, WebSocket for job progress
- **Production model**: `models/detection/sonar_yolov8_fls_trained.pt` — SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
- **Existing WebSocket**: Redis pub/sub pattern at `/ws/jobs/{job_id}`
- **Existing API prefix**: `/api/v1/`
- **Existing config**: Pydantic `BaseSettings` in `backend/config.py`
- **Existing inference**: `backend/inference/detector.py` (RawDetection dataclass, detect_tiles), `backend/inference/model_loader.py` (ModelLoader singleton)
- **Existing preprocessing**: `backend/preprocessing/` pipeline
- **Existing enhancement**: `backend/enhancement/` with providers, profiles, benchmark
- **Existing sonar parsers**: `backend/sonar_parser/`
- **Existing DB models**: `backend/database/models.py`
- **Existing exceptions**: `backend/exceptions.py`
- **Frontend pages**: CommandCenterPage, DashboardPage, SurveyListPage, SurveyDetailPage, ModelsPage, DatasetPage, SonarEnhancementPage, UploadPage, ModelEvaluationPage
- **Frontend layout**: AppLayout with Sidebar + Navbar, custom maritime color palette (`bg-primary: #F2EFE7`, accent: `#C8523B`)

Read `DEVELOPMENT_GUIDELINES.md`, `ARCHITECTURAL_BLUEPRINT.md`, `API_SPEC.md`, `DB_SCHEMA.md`, `UI_UX_SPEC.md`, `PRD.md`, and all docs/ before implementing.

---

## Critical Safety Constraints (NON-NEGOTIABLE)

These constraints are immutable. Violation of any one fails the entire implementation.

1. **Production model immutability**: `models/detection/sonar_yolov8_fls_trained.pt` must remain byte-identical. SHA256 must be `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7` before AND after implementation.
2. **Frozen dataset protection**: `datasets/sonar_debris_v2_clean`, held-out test sets, V2/V3 benchmark images, annotations, Dataset Explorer APIs — NONE may be modified.
3. **No fabricated data**: No fake detections, fake GPS, fake sonar telemetry, fake confidence values, fake FPS, fake connection states, fake model status. Unavailable values must be `null` or `NOT_AVAILABLE`.
4. **Existing functionality preservation**: All existing APIs, database behavior, ML artifacts, preprocessing behavior, survey processing, report generation, offline inference, WebSocket job progress — must remain working.

---

## Requirements

### R1. Live Sonar Streaming Infrastructure

Build a modular streaming subsystem in `backend/live_sonar/` following this architecture (acquisition and AI layers must be independently replaceable):

```
SONAR SOURCE → SOURCE ADAPTER → FRAME NORMALIZATION → FRAME BUFFER →
SONAR METADATA → PREPROCESSING → AI INFERENCE → TEMPORAL TRACKING →
GEOSPATIAL ASSOCIATION → EVENT PROCESSING → DATABASE → WEBSOCKET → FRONTEND
```

**Source abstraction** — `SonarStreamAdapter` (ABC): `connect()`, `disconnect()`, `frames()` (AsyncIterator[SonarFrame]), `health()`, `metadata()`. Implement concrete adapters for:
- **Replay** (`.mp4`, `.mkv`, `.avi`, XTF, PNG sequences) — critical for development; must use SAME pipeline as live
- **RTSP** (`rtsp://...`) — production-safe streaming decoder
- **USB/camera** (`device://0`) — local device index
- **Native sonar stub** — ARIS-class adapter boundary with `status = NOT_CONFIGURED` if protocol unavailable

**Frame buffer** — Bounded async queue with configurable policies: `DROP_OLDEST` (default), `FIFO`, `DROP_NEWEST`, `LATEST`. Never allow unbounded memory growth. Expose: `frames_received`, `frames_processed`, `frames_dropped`, `queue_depth`.

**Backpressure** — Expose `input_fps`, `processing_fps`, `effective_fps`, `latency_ms`, `drop_rate`. If `input_fps > inference_fps`, the UI must indicate processing is falling behind.

**SonarFrame** data model with: frame_id, sequence_number, timestamps (UTC), source metadata, image data (raw immutable), sonar metadata (frequency, range, gain, beam_angle, heading, pitch, roll, depth, sound_speed — null if unavailable), navigation (lat/lon/heading/depth — null if unavailable), quality flags.

**Session management** — `LiveSonarSession` with: session_id, source config, lifecycle statuses (`CONNECTING`, `CONNECTED`, `RUNNING`, `DEGRADED`, `STOPPING`, `STOPPED`, `ERROR`), aggregate metrics.

**Configuration** via existing `Settings` class with env vars: `LIVE_SONAR_ENABLED`, `LIVE_SONAR_SOURCE_TYPE`, `LIVE_SONAR_SOURCE_URI`, `LIVE_SONAR_TARGET_FPS`, `LIVE_SONAR_BUFFER_SIZE`, `LIVE_SONAR_DROP_POLICY`, etc.

### R2. AI Pipeline Integration

Reuse the existing production detector and preprocessing pipeline for live inference:

- **Preprocessing**: Reuse `backend/preprocessing/` pipeline. Support configurable profiles: `REALTIME` (minimal, fast), `BALANCED` (standard existing pipeline), `QUALITY` (full enhancement). Do NOT change existing offline pipeline behavior.
- **Raw frame immutability**: Maintain separate `raw_frame`, `processed_frame`, `model_frame`, `annotated_frame` representations. Never modify raw in place.
- **Model inference**: Use existing `ModelLoader` to load `sonar_yolov8_fls_trained.pt` once per worker/process. Use existing `detect_tiles()`. Support CUDA and CPU fallback.
- **Inference worker**: Isolated from HTTP request lifecycle. Frame skipping for controlled throughput (e.g., 30 FPS input → 10 FPS inference → 20 skipped, display still shows latest frame). Expose `display_fps`, `inference_fps`, `input_fps` separately.
- **Enhancement**: Integrate existing `backend/enhancement/` architecture where applicable (dB conversion, CLAHE, FFT stripe-noise, etc.). Enhancement layer must remain optional.
- **Temporal tracking**: ByteTrack behind a `SonarObjectTracker` interface. Per-track: `track_id`, `class`, `confidence`, `bbox`, `first_seen`, `last_seen`, `age`, `frames_seen`, `frames_missing`, `trajectory`, `status` (ACTIVE/LOST/COMPLETED). Tracker state isolated per session.
- **Temporal confirmation**: Configurable `minimum_confirmed_frames`, `minimum_track_age`, `confidence_threshold`. Do NOT create high-confidence alerts from single frames.
- **Class consistency**: Maintain class evidence over time; don't flip class every frame.
- **Acoustic shadow**: Reuse existing reasoning where available; use evidence language (`Shadow support: detected/unavailable`).
- **Geolocation**: Use existing georeferencing if navigation data exists; `GPS: NOT_AVAILABLE` otherwise.
- **Detection events**: `LiveDetectionEvent` model with event_id, stream_id, frame_id, track_id, timestamp, class, confidence, bbox, sonar_range, navigation, processing_latency, model_version, evidence path, status.

### R3. Real-Time Communication & API

**WebSocket** at `/ws/live-sonar/{session_id}` using existing Redis pub/sub pattern:
- Frame results: detections, tracks, metrics (NOT full-size raw frames — use JPEG/WebP preview + metadata)
- Events: `session_started`, `session_stopped`, `connection_lost`, `connection_restored`, `detection_created`, `track_confirmed`, `track_lost`, `buffer_warning`, `processing_degraded`, `error`
- Bandwidth must remain bounded.

**REST API** following existing `/api/v1/` conventions:
- `POST/GET /api/v1/live-sonar/sessions` — create/list sessions
- `GET /api/v1/live-sonar/sessions/{id}` — session detail
- `POST /api/v1/live-sonar/sessions/{id}/start|stop` — lifecycle
- `GET /api/v1/live-sonar/sessions/{id}/metrics|tracks|detections|evidence` — query
- Health endpoint reporting real source status, FPS, queue depth, GPU, model, tracker state

**Security**: Validate source URIs, prevent SSRF/command injection, never store credentials in source code, implement allowlist for external network sources.

### R4. Live Sonar Frontend UI

Add a **Live Sonar** page to the existing React frontend, matching the existing maritime design language (warm neutrals, `#C8523B` accent, restrained professional UI — NOT neon cyberpunk):

**Main viewport** — Large live sonar display with view modes: `RAW`, `ENHANCED`, `AI`, `SPLIT`. AI overlay showing bounding boxes, class labels, confidence, track IDs, confirmation state, acoustic shadow indicators, and track trajectory trails.

**Right-side target panel** — Active targets list (track ID, class, confidence). Clicking opens a target inspection panel with: class, confidence history, first/last seen, duration, frames observed, trajectory, geolocation, sonar range, acoustic shadow status, evidence frames, model version, preprocessing profile. Unavailable values show `NOT_AVAILABLE`.

**Live metrics bar** — INPUT FPS, INFERENCE FPS, DISPLAY FPS, LATENCY, GPU, QUEUE DEPTH, DROPPED FRAMES, ACTIVE TRACKS, CONFIRMED TARGETS — all from real runtime values.

**Connection panel** — Source type, URI (no credentials), sonar model, frequency, range, GNSS status (only `CONNECTED` if actually receiving nav data), connection state with `RECONNECTING...` during retries. On disconnect: show `CONNECTION LOST` with last frame timestamp, stop inference, never freeze-and-pretend.

**Controls** — Pause, Resume, Record (`● RECORDING` indicator), Snapshot (captures raw+enhanced+annotated+metadata), Enhancement toggle, Detection toggle, Tracking toggle, `LIVE`/`REPLAY` indicator (never ambiguous).

**Replay controls** — Speed (0.25x, 0.5x, 1x, 2x, 4x), pause, step frame, seek.

**Performance** — Canvas/WebGL for viewport, no thousands of DOM elements, responsive even when inference is slower than acquisition.

### R5. Evidence, Recording & Session Persistence

**Recording**: Optional live recording of raw frames, processed frames, metadata, detections, tracks, navigation using existing storage abstraction.

**Evidence capture**: When a target becomes confirmed, optionally save raw/enhanced/annotated evidence frames + metadata JSON, organized per session/track. Use existing artifact storage conventions.

**Replay parity**: Recorded streams must be replayable through the exact same inference/tracking pipeline as live — only `FrameSource` differs.

**Database**: Extend existing SQLAlchemy models for `LiveSonarSession`, `LiveDetectionEvent`, track data. Use Alembic migrations. Do NOT create a second database. Every confirmed target must be traceable to source → session → frame → model → preprocessing → timestamp → navigation → evidence artifact.

### R6. Testing & Verification

**Unit tests**: Frame model, validation, frame buffer, queue overflow/drop policies, adapter interface, replay adapter, preprocessing integration, inference output conversion, tracker state/reset, temporal confirmation, confidence smoothing, metadata propagation.

**Integration tests**: Replay file → frame adapter → preprocessing → model → tracker → WebSocket — using real repository artifacts where practical.

**End-to-end test**: One deterministic replay fixture verifying: stream starts → frames arrive → frames process → detections emitted → tracks persist → WebSocket messages arrive → session metrics update → stream stops.

**Performance test**: Measure input/preprocessing/inference/tracking FPS, end-to-end latency, GPU utilization, memory, queue depth, drop rate under 5/10/15/30 FPS loads.

**Regression**: Existing backend tests pass, frontend builds, existing offline inference works, survey processing works, report generation works, Dataset Explorer APIs unchanged.

---

## Acceptance Criteria

### Safety & Integrity
- [ ] Production model SHA256 is `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7` after implementation (verified by script)
- [ ] `datasets/sonar_debris_v2_clean` is unmodified (verified by checking no git changes to that path)
- [ ] No fake detections, fake GPS, fake telemetry, fake FPS, fake connection states anywhere in the codebase (verified by grep audit for hardcoded fake values)
- [ ] All existing tests pass (`pytest` exits 0)
- [ ] Frontend builds successfully (`npm run build` exits 0)
- [ ] Existing API endpoints return same responses (spot-check survey, dataset, model endpoints)

### Streaming Infrastructure
- [ ] Source abstraction with ABC interface exists; replay adapter functional
- [ ] Frame buffer is bounded; `frames_dropped` metric increments under backpressure (unit test)
- [ ] Session lifecycle transitions work: CONNECTING → CONNECTED → RUNNING → STOPPED
- [ ] Replay of a `.mp4` or image sequence produces frames through the full pipeline

### AI Pipeline
- [ ] Detections from replay are real model output (not hardcoded)
- [ ] Track IDs persist across consecutive frames (integration test)
- [ ] Tracker state is isolated per session (unit test showing two sessions don't cross-contaminate)
- [ ] Temporal confirmation requires configurable N-of-M frames
- [ ] Preprocessing reuses existing pipeline code (imports from `backend/preprocessing/`)

### Frontend
- [ ] Live Sonar page loads in the browser with sonar viewport
- [ ] RAW/ENHANCED/AI view modes toggle correctly
- [ ] Active targets panel shows track ID, class, confidence for real detections
- [ ] Metrics bar shows real INPUT FPS, INFERENCE FPS, LATENCY values
- [ ] Connection status reflects actual state (not hardcoded "CONNECTED")
- [ ] `LIVE` vs `REPLAY` indicator is displayed and accurate
- [ ] Target click opens inspection panel with available metadata

### WebSocket & API
- [ ] `/ws/live-sonar/{session_id}` delivers detection/track/metric messages
- [ ] REST endpoints for session CRUD and lifecycle work
- [ ] Full-size raw frames are NOT sent through WebSocket

### Testing
- [ ] Unit tests for frame buffer, tracker, confirmation logic pass
- [ ] Integration test: replay file → detections → WebSocket messages works
- [ ] E2E replay fixture completes successfully

### Documentation
- [ ] `docs/live-sonar.md` exists with architecture, configuration, supported sources, and limitations
- [ ] Hardware integration status is explicitly marked as `NOT_VERIFIED` unless actually tested

---

## Verification Plan

All acceptance criteria above are verifiable programmatically:

1. **Model integrity**: Run `certutil -hashfile models\detection\sonar_yolov8_fls_trained.pt SHA256` and compare
2. **Dataset integrity**: Run `git diff --name-only datasets/` and verify empty output
3. **No fake data audit**: Run `grep -rn "fake|hardcoded|mock.*detection|simulated.*gps" backend/live_sonar/ frontend/src/features/live-sonar/` and review hits
4. **Existing tests**: Run `pytest` from repo root
5. **Frontend build**: Run `npm run build` in frontend/
6. **New unit tests**: Run `pytest tests/live_sonar/`
7. **Integration test**: Run the replay E2E fixture
8. **API smoke test**: Start server, POST to create session, start it with a replay source, GET metrics
