# Backend Specification: Live Sonar AI Detection & Tracking Subsystem (R1, R2, R3, R5)

**Author:** teamwork_preview_spec_miner_backend_1  
**Target Subsystem:** `backend/live_sonar/` & Backend Architecture Extensions  
**Repository:** `MarineDebris-Sonar-AI`  
**Date:** 2026-09-19  
**Status:** Authoritative Specification Document (Phase 1 Mining)  

---

## 1. Executive Summary & Authoritative Specification Context

This document establishes the authoritative backend specification for the **Live Sonar AI Detection & Tracking Subsystem** within `MarineDebris-Sonar-AI`. It maps requirements **R1** (Live Sonar Streaming Infrastructure), **R2** (AI Pipeline Integration & ByteTrack), **R3** (Real-Time Communication & REST API), and **R5** (Persistence, Recording & Alembic Migration) as defined in `ORIGINAL_REQUEST.md`, reconciling them with existing codebase implementations and foundational specifications (`ARCHITECTURAL_BLUEPRINT.md`, `API_SPEC.md`, `DB_SCHEMA.md`, `DEVELOPMENT_GUIDELINES.md`, and `PRD.md`).

### Authoritative Reference Sources
1. **`ORIGINAL_REQUEST.md`**: Master requirements for live acquisition, frame buffer, inference worker, ByteTrack, WebSocket schemas, session persistence, and safety rules.
2. **`ARCHITECTURAL_BLUEPRINT.md`**: Modular monolith design, Celery/Redis pub/sub pattern, chunked processing, and technology versions.
3. **`backend/config.py` & `backend/api/main.py`**: Pydantic settings, FastAPI routers, lifespan handlers, CORS, and middleware.
4. **`backend/inference/detector.py` & `backend/inference/model_loader.py`**: YOLOv8 forward pass, `RawDetection` data contract, and singleton model loader.
5. **`backend/preprocessing/`**: Existing acoustic preprocessing chain (`assess_quality`, `detect_bottom`, `remove_water_column`, `normalize`, `apply_clahe`, `denoise`, `correct_slant_range`, `generate_tiles`).
6. **`backend/enhancement/`**: Acoustic enhancement registry (`PROFILE_REGISTRY`, `ProfileName`, bilateral CLAHE, log-domain filtering).
7. **`backend/database/models.py` & `backend/database/migrations/`**: SQLAlchemy 2.0 async models and Alembic revision lineage (`0001_initial_schema`, `0002_ml_segmentation_classification`).
8. **`backend/georeferencing/geotagger.py`**: WGS84 projection mathematics and truthfulness constraints.

### Immutable Safety & Integrity Constraints
- **Production Model Immutability:** `models/detection/sonar_yolov8_fls_trained.pt` must remain strictly byte-identical with SHA256 checksum:
  `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
- **Frozen Dataset Protection:** `datasets/sonar_debris_v2_clean`, test splits, and benchmark annotations must not be modified.
- **No Fabricated Data:** Telemetry (frequency, range, gain, beam angle, attitude), navigation coordinates (latitude, longitude, heading, depth), confidence scores, and FPS metrics must be real values. If unavailable, they must be `None` / `null` or `NOT_AVAILABLE`.
- **Existing Functionality Preservation:** Batch survey processing, offline inference, existing REST APIs (`/api/v1/surveys`, `/api/v1/jobs`), and existing WebSocket `/api/v1/ws/jobs/{job_id}` must remain 100% operational.

---

## 2. Requirement R1: Live Sonar Streaming Infrastructure

### 2.1 Subsystem Architecture & Data Flow
The streaming subsystem in `backend/live_sonar/` decouples acquisition from AI processing and communication:

```
SONAR SOURCE (Replay / RTSP / USB / Native)
      │
      ▼
SOURCE ADAPTER (SonarStreamAdapter ABC)
      │
      ▼
FRAME NORMALIZATION (Pixel format, geometry, uint8/float32)
      │
      ▼
FRAME BUFFER (Bounded queue: DROP_OLDEST / FIFO / DROP_NEWEST / LATEST)
      │
      ├───────────────────────────────┐
      ▼                               ▼
SONAR METADATA & TELEMETRY       PREPROCESSING PROFILES (REALTIME / BALANCED / QUALITY)
      │                               │
      └──────────────┬────────────────┘
                     ▼
             AI INFERENCE WORKER (YOLOv8 FLS detector, frame skipping)
                     │
                     ▼
             TEMPORAL TRACKER (ByteTrack / SonarObjectTracker)
                     │
                     ▼
             GEOSPATIAL ASSOCIATION (WGS84 Geotagger)
                     │
                     ▼
             EVENT PROCESSING & EVIDENCE DISK WRITER
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
DATABASE (PostgreSQL)    REDIS PUB/SUB CHANNEL (`live_sonar:{session_id}`)
                                 │
                                 ▼
                         WEBSOCKET ENDPOINT (`/ws/live-sonar/{session_id}`)
                                 │
                                 ▼
                         FRONTEND VIEWPORT & PANELS
```

### 2.2 Source Abstraction: `SonarStreamAdapter` (ABC)
Located at `backend/live_sonar/adapters/base.py`:

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any
from backend.live_sonar.models import SonarFrame, StreamHealth, SonarStreamMetadata

class SonarStreamAdapter(ABC):
    """Abstract Base Class for all sonar input stream sources."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the sonar hardware, stream, or file source.
        Raises:
            LiveSonarSourceConnectionError: If connection cannot be established.
            LiveSonarSecurityViolationError: If URI violates SSRF/allowlist rules.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully terminate stream connection and release underlying resources."""
        pass

    @abstractmethod
    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield normalized SonarFrame instances from the source."""
        pass

    @abstractmethod
    async def health(self) -> StreamHealth:
        """Return real-time health telemetry of the source connection."""
        pass

    @abstractmethod
    async def metadata(self) -> SonarStreamMetadata:
        """Return static or session-level sonar stream metadata."""
        pass
```

### 2.3 Concrete Adapters & Error Handling

#### 1. `ReplayStreamAdapter` (`backend/live_sonar/adapters/replay.py`)
- **Supported Formats:**
  - Video files: `.mp4`, `.mkv`, `.avi` (decoded via OpenCV / PyAV)
  - Sonar log files: `.xtf` (streamed chunk-by-chunk via existing `pyxtf` parser in `backend/sonar_parser/`)
  - Image directory sequences: Directory of `.png` / `.jpg` files (e.g. `data/test_sonar_images/`) sorted lexicographically
- **Execution Mode:** Uses the **exact same downstream pipeline** as live hardware.
- **Pacing Control:**
  - `target_fps`: Paced sleep interval $(1.0 / \text{target\_fps})$ between frames.
  - Video timestamp synchronization: If video has embedded PTS, pace against elapsed monotonic time.
  - Controls: Pause, Resume, Seek (frame index), Speed multiplier ($0.25\times, 0.5\times, 1\times, 2\times, 4\times$), Loop option.
- **Error Behavior:**
  - File not found: Raises `LiveSonarSourceInvalidError(status_code=400)`.
  - Corrupted frame: Logs warning, increments `frames_corrupted`, skips to next frame without crashing stream.
  - End of Stream (EOF): If loop disabled, cleanly completes generator and transitions session to `STOPPED`.

#### 2. `RTSPStreamAdapter` (`backend/live_sonar/adapters/rtsp.py`)
- **Protocol:** `rtsp://[user:pass@]host:port/path` or `rtsps://`
- **Decoder:** OpenCV `VideoCapture` or `av.open` using TCP transport (`rtsp_transport=tcp`) to avoid UDP packet loss in maritime environments.
- **Asynchronous Execution:** Video decoding executes inside an `asyncio.to_thread` or dedicated thread loop, pushing decoded frames into an internal queue to prevent blocking the event loop.
- **Reconnection & Resilience:**
  - Auto-reconnect with exponential backoff ($1\text{s}, 2\text{s}, 4\text{s}, \dots, \max 30\text{s}$).
  - Maximum reconnect attempts: configurable (default 10).
  - Socket timeout: 5.0 seconds.
  - State signaling: Publishes `connection_lost` upon disconnect; transitions to `RECONNECTING`; publishes `connection_restored` upon success.
  - Never freeze-and-pretend: When connection drops, stops inference and signals UI immediately.

#### 3. `USBCameraStreamAdapter` (`backend/live_sonar/adapters/usb.py`)
- **Protocol:** `device://<index>` (e.g. `device://0`)
- **Mechanism:** OpenCV `VideoCapture(index, cv2.CAP_DSHOW)` on Windows, `cv2.CAP_V4L2` on Linux.
- **Error Behavior:**
  - Device index out of bounds / disconnected: Raises `LiveSonarSourceConnectionError("Device index not found")`.
  - Device busy: Raises `LiveSonarSourceConnectionError("Device occupied by another process")`.

#### 4. `NativeSonarStubAdapter` (`backend/live_sonar/adapters/native_stub.py`)
- **Target Hardware Class:** ARIS 3000 / DIDSON / Blueprint Subsea Oculus forward-looking sonars.
- **Status Reporting:** Defaults to `status = "NOT_CONFIGURED"`.
- **Behavior:**
  - Implements the `SonarStreamAdapter` interface boundary.
  - When SDK or hardware drivers are not installed or hardware is unreachable:
    - `connect()` raises `LiveSonarSourceConnectionError(code="NATIVE_SONAR_UNAVAILABLE", message="Native sonar SDK/driver not configured on host")`.
    - `health()` returns `StreamHealth(status="NOT_CONFIGURED", details="Driver not linked")`.
    - Yields zero frames without raising unhandled exceptions or crashing the server.

### 2.4 Bounded Frame Buffer (`backend/live_sonar/buffer.py`)
To prevent memory exhaustion during inference spikes or high incoming framerates, the buffer maintains a strict size bound:

```python
class DropPolicy(str, Enum):
    DROP_OLDEST = "DROP_OLDEST"  # Real-time monitoring: discard stale frames to prioritize lowest latency
    FIFO = "FIFO"                # Strict queue: block or reject until space is available
    DROP_NEWEST = "DROP_NEWEST"  # Discard incoming frame if buffer is saturated
    LATEST = "LATEST"            # Capacity 1: always keep the newest single frame
```

- **Default Buffer Size:** 60 frames (configurable via `LIVE_SONAR_BUFFER_SIZE`).
- **Default Drop Policy:** `DROP_OLDEST`.
- **Metrics Tracked:**
  - `frames_received`: Monotonic counter of all frames accepted from adapter.
  - `frames_processed`: Monotonic counter of frames dispatched to inference.
  - `frames_dropped`: Monotonic counter of frames discarded due to buffer overflow.
  - `queue_depth`: Current instantaneous frame count in buffer.
  - `drop_rate`: Rolling ratio of $\frac{\text{dropped}}{\text{received}}$ over the last 5 seconds.

### 2.5 Backpressure & Performance Telemetry
Calculated continuously over a 1.0-second sliding window:
- `input_fps`: $\frac{\Delta \text{frames\_received}}{\Delta t}$
- `processing_fps`: $\frac{\Delta \text{frames\_processed}}{\Delta t}$ (pipeline throughput)
- `effective_fps`: Rate of annotated frames pushed to WebSocket / UI
- `latency_ms`: Mean duration from `SonarFrame.timestamp_utc` to WebSocket dispatch
- **Degraded Threshold:**
  - If `input_fps > processing_fps` and `queue_depth > 0.8 * buffer_size`:
    - Session transitions to status `DEGRADED`.
    - Redis / WebSocket publishes `buffer_warning` and `processing_degraded` events.
    - Inference worker automatically enables/increases frame skipping while acquisition continues.

### 2.6 Exact Data Structure: `SonarFrame` (Live)
Defined in `backend/live_sonar/models.py`:

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import numpy as np
import uuid

@dataclass(frozen=True)
class LiveSonarTelemetry:
    """Sonar acoustic operating parameters. Null if source lacks telemetry."""
    frequency_hz: Optional[float] = None
    range_m: Optional[float] = None
    gain_db: Optional[float] = None
    beam_angle_deg: Optional[float] = None
    heading_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    roll_deg: Optional[float] = None
    depth_m: Optional[float] = None
    sound_speed_mps: Optional[float] = None

@dataclass(frozen=True)
class LiveNavigationData:
    """GNSS/INS vessel/towfish position. Null if GPS/nav unavailable."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading_deg: Optional[float] = None
    depth_m: Optional[float] = None
    altitude_m: Optional[float] = None
    speed_knots: Optional[float] = None

@dataclass(frozen=True)
class QualityFlags:
    """Acoustic quality assessment flags."""
    is_dropout: bool = False
    motion_quality_score: Optional[float] = None
    is_degraded: bool = False

@dataclass
class SonarFrame:
    """Live Sonar Video Frame data contract. Raw image array is immutable."""
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    sequence_number: int = 0
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    image_data: np.ndarray = field(default_factory=lambda: np.zeros((1, 1), dtype=np.uint8))  # RAW IMMUTABLE
    sonar_metadata: LiveSonarTelemetry = field(default_factory=LiveSonarTelemetry)
    navigation: LiveNavigationData = field(default_factory=LiveNavigationData)
    quality_flags: QualityFlags = field(default_factory=QualityFlags)

    def __post_init__(self):
        # Guarantee raw image immutability by setting writeable flag to False
        if isinstance(self.image_data, np.ndarray):
            self.image_data.flags.writeable = False
```

### 2.7 Exact Data Structure: `LiveSonarSession`
Defined in `backend/live_sonar/models.py`:

```python
class SessionStatus(str, Enum):
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"

@dataclass
class StreamMetrics:
    input_fps: float = 0.0
    inference_fps: float = 0.0
    display_fps: float = 0.0
    processing_fps: float = 0.0
    latency_ms: float = 0.0
    queue_depth: int = 0
    frames_received: int = 0
    frames_processed: int = 0
    frames_dropped: int = 0
    drop_rate: float = 0.0
    active_tracks_count: int = 0
    confirmed_targets_count: int = 0

@dataclass
class LiveSonarSessionConfig:
    session_id: str
    name: str
    source_type: str  # "replay" | "rtsp" | "usb" | "native_stub"
    source_uri: str
    target_fps: float = 15.0
    inference_fps: float = 10.0
    buffer_size: int = 60
    drop_policy: DropPolicy = DropPolicy.DROP_OLDEST
    preprocessing_profile: str = "REALTIME"  # "REALTIME" | "BALANCED" | "QUALITY"
    enable_tracking: bool = True
    enable_recording: bool = False
    confidence_threshold: float = 0.35
    minimum_confirmed_frames: int = 3
    track_max_age_frames: int = 30
```

---

## 3. Requirement R2: AI Pipeline & ByteTrack Tracking Architecture

### 3.1 Preprocessing Profiles Integration
The live pipeline reuses `backend/preprocessing/` modules without modifying existing offline survey processing:

| Profile | Target Latency Budget | Operations Executed | Acoustic Target |
|---|---|---|---|
| **`REALTIME`** | $\le 15\text{ ms}$ | Fast uint8/float32 normalization (`normalize`), lightweight CLAHE (`apply_clahe` with `clip_limit=1.5`, `grid=(8,8)`). Skips bottom detection, water column removal, and slant-range correction. Fast resize/tile to $640\times 640$. | High-framerate FLS navigation, obstacle avoidance, low-power edge nodes. |
| **`BALANCED`** | $30\text{--}60\text{ ms}$ | Full standard pipeline: `assess_quality` $\to$ `detect_bottom` $\to$ `remove_water_column` $\to$ `normalize` $\to$ `apply_clahe` $\to$ `denoise` (median filter $k=3$) $\to$ `correct_slant_range` $\to$ tiling. | General-purpose survey operations, balanced noise reduction and edge retention. |
| **`QUALITY`** | $70\text{--}150\text{ ms}$ | Reuses `backend/enhancement/`: Bilateral CLAHE (`ProfileName.BALANCED`, $d=5, \sigma_c=0.1, \sigma_s=3.0$) or Log-Bilateral CLAHE (`ProfileName.LOW_SNR`), FFT stripe-noise attenuation, slant-range correction, quality scoring. | Turbid water inspection, forensic analysis, low-speed AUV survey passes. |

### 3.2 Raw Frame Immutability (The 4 Representations)
For every processed frame, four distinct representations are maintained to prevent accidental in-place mutation:
1. `raw_frame`: Original numpy array from adapter (`flags.writeable = False`). Preserved for recording and forensic evidence export.
2. `processed_frame`: Enhanced/filtered image resulting from the selected preprocessing profile (`REALTIME`, `BALANCED`, or `QUALITY`).
3. `model_frame`: Normalized, letterboxed, or tiled RGB tensor formatted specifically for YOLOv8 input tensor requirements.
4. `annotated_frame`: Preview image (downscaled to $640\text{px}$ width or native resolution) with drawn bounding boxes, track labels, trajectory trails, and status badges, encoded as compressed JPEG/WebP for WebSocket push.

### 3.3 Model Loading & Inference Worker Architecture
- **Model Checkpoint:** `models/detection/sonar_yolov8_fls_trained.pt` (SHA256 verified).
- **Loader:** Uses `backend.inference.model_loader.ModelLoader.get_detection_model()`. The model is loaded once per worker process into memory.
- **Forward Pass:** Executes `detect_tiles()` from `backend/inference/detector.py` inside `torch.inference_mode()`. Device selection: CUDA with CPU fallback.
- **Decoupled Asynchronous Worker:**
  - Frame acquisition pushes to `SonarFrameBuffer`.
  - An independent async worker loop drains the buffer.
  - **Frame Skipping Strategy:**
    - If `input_fps = 30.0` and `inference_fps = 10.0`, the worker runs inference on frame $k$, and skips inference on frames $k+1$ and $k+2$.
    - Skipped frames still update display/preview metrics, and active tracks are propagated forward using the Kalman filter velocity model!
    - Metrics explicitly report `input_fps`, `inference_fps`, and `display_fps` separately.

### 3.4 Temporal Tracking with ByteTrack (`SonarObjectTracker`)
Located at `backend/live_sonar/tracking/`:

#### Architecture & Interfaces:
```python
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime
from backend.inference.detector import RawDetection
from backend.live_sonar.models import Track

class SonarObjectTracker(ABC):
    @abstractmethod
    def update(self, detections: List[RawDetection], frame_id: str, timestamp: datetime) -> List[Track]:
        """Update tracker with detections from the current frame."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset internal Kalman filters and track registry."""
        pass

    @abstractmethod
    def get_active_tracks(self) -> List[Track]:
        """Return all currently active tracks."""
        pass
```

#### ByteTrack Two-Stage Association Algorithm:
1. **Stage 1 (High-Confidence Association):**
   - Partition detections into high-confidence ($conf \ge conf_{\text{high}}$, default $0.50$) and low-confidence ($conf_{\text{low}} \le conf < conf_{\text{high}}$, default $0.15 \le conf < 0.50$).
   - Predict next bounding box positions of existing active tracks using Kalman filter state $[\text{center\_x}, \text{center\_y}, \text{aspect\_ratio}, \text{height}, \dot{x}, \dot{y}, \dot{a}, \dot{h}]$.
   - Compute cost matrix using Intersection over Union (IoU) or distance metric.
   - Solve association using the Hungarian algorithm (`scipy.optimize.linear_sum_assignment`).
2. **Stage 2 (Low-Confidence Association for Acoustic Dropouts):**
   - Match remaining unassigned tracks from Stage 1 against the **low-confidence detections**.
   - This prevents target track fragmentation caused by acoustic multipath fading, speckle noise, or temporary target obscuration.
3. **Track Lifecycle & State Machine:**
   - Unmatched high-confidence detections spawn new tracks in state `TENTATIVE`.
   - Matched tracks update their Kalman filter state and increment `frames_seen`.
   - Unmatched tracks increment `frames_missing`.
   - If `frames_missing > max_lost_frames` (default 30 frames / 2.0 s at 15 FPS), status transitions to `LOST`, then deleted / completed.
   - **Isolation:** Tracker instances are tied 1:1 to `LiveSonarSession`. Tracker state is never shared between sessions.

### 3.5 Temporal Confirmation & Class Consistency
- **Temporal Confirmation Rule:**
  - A track starts as `status = "TENTATIVE"`.
  - It transitions to `status = "CONFIRMED"` only after being detected in at least `minimum_confirmed_frames` (default 3 frames within a window of 5 frames).
  - High-confidence alarms are NEVER triggered on a single isolated frame spike.
- **Class Consistency Mechanism:**
  - Tracks maintain an evidence histogram of predicted classes: $\sum_{t} conf_{t, c}$.
  - The displayed track class is the ArgMax of cumulative class evidence, preventing label flickering between `derelict_fishing_gear` and `general_marine_debris`.
- **Acoustic Shadow Verification:**
  - Analyzes the acoustic shadow region behind the highlight along the acoustic sweep direction.
  - Surfaces structured evidence language:
    - `"Shadow support: detected"`
    - `"Shadow support: unavailable"` (target near boundary or bottom echo clipped)
    - `"Shadow support: mismatched"`
- **Geolocation Association:**
  - If `SonarFrame.navigation.latitude` is present: maps bounding box centroid to WGS84 coordinates using `backend.georeferencing.geotagger.geotag_detection()`.
  - If navigation is null: sets `geotagging_available = False`, `latitude = None`, `longitude = None`, surfaced in UI as `GPS: NOT_AVAILABLE`.

### 3.6 Exact Data Structure: `LiveDetectionEvent` & `Track`
Defined in `backend/live_sonar/models.py`:

```python
@dataclass
class Track:
    track_id: int
    session_id: str
    class_name: str
    confidence: float
    confidence_history: List[float] = field(default_factory=list)
    bbox: Dict[str, int] = field(default_factory=dict)  # {"x": int, "y": int, "w": int, "h": int}
    velocity: Dict[str, float] = field(default_factory=lambda: {"vx": 0.0, "vy": 0.0})
    trajectory: List[Dict[str, Any]] = field(default_factory=list)  # [{"x": int, "y": int, "t": float}]
    first_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    age_frames: int = 1
    frames_seen: int = 1
    frames_missing: int = 0
    status: str = "TENTATIVE"  # "TENTATIVE" | "CONFIRMED" | "LOST" | "COMPLETED"
    is_confirmed: bool = False
    confirmed_at: Optional[datetime] = None
    shadow_status: str = "unavailable"  # "detected" | "unavailable" | "mismatched"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geotagging_available: bool = False
    evidence_path: Optional[str] = None

@dataclass
class LiveDetectionEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    frame_id: str = ""
    track_id: Optional[int] = None
    sequence_number: int = 0
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    class_name: str = ""
    confidence: float = 0.0
    confidence_calibrated: Optional[float] = None
    bbox: Dict[str, int] = field(default_factory=dict)
    sonar_range_m: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geotagging_available: bool = False
    processing_latency_ms: float = 0.0
    model_version: str = "1.0.0"
    status: str = "TENTATIVE"
    is_confirmed: bool = False
    evidence_path: Optional[str] = None
```

---

## 4. Requirement R3: Real-Time Communication & REST API

### 4.1 WebSocket Protocol: `/ws/live-sonar/{session_id}`
- **Endpoint:** `/ws/live-sonar/{session_id}` (with `/api/v1/ws/live-sonar/{session_id}` mounted as alias).
- **Pub/Sub Mechanism:** Integrates with Redis via `redis.asyncio` on channel `live_sonar:{session_id}`.
- **Bandwidth Budget:** Maximum $80\text{ KB}$ per frame payload. Raw $1024\times 1024$ float32 frames ($4\text{ MB}$) are **NEVER** transmitted over WebSocket. A compressed JPEG/WebP preview ($480\text{--}640\text{px}$, quality 75) is transmitted along with lightweight metadata JSON.

#### Message Schema 1: Live Frame Update (`frame_update`)
Pushed on every processed frame:
```json
{
  "event": "frame_update",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "frame_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "sequence_number": 1042,
  "timestamp": "2026-09-19T05:45:12.345Z",
  "preview_image": "data:image/jpeg;base64,...",
  "detections": [
    {
      "detection_id": "e2a3b4c5-...",
      "class_name": "derelict_fishing_gear",
      "confidence": 0.87,
      "confidence_calibrated": 0.83,
      "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
      "track_id": 12
    }
  ],
  "tracks": [
    {
      "track_id": 12,
      "class_name": "derelict_fishing_gear",
      "confidence": 0.88,
      "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
      "status": "CONFIRMED",
      "is_confirmed": true,
      "age_frames": 15,
      "frames_seen": 14,
      "trajectory": [{"x": 300, "y": 210}, {"x": 308, "y": 215}, {"x": 314, "y": 220}],
      "shadow_status": "detected",
      "geotagging_available": true,
      "latitude": 38.812345,
      "longitude": -75.134567
    }
  ],
  "metrics": {
    "input_fps": 15.1,
    "inference_fps": 10.2,
    "display_fps": 15.0,
    "latency_ms": 65.4,
    "queue_depth": 3,
    "frames_dropped": 0,
    "drop_rate": 0.0
  }
}
```

#### Message Schema 2: Session & System Lifecycle Events
Pushed immediately upon state change:
```json
{
  "event": "track_confirmed",
  "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "track_id": 12,
  "class_name": "derelict_fishing_gear",
  "confidence": 0.88,
  "timestamp": "2026-09-19T05:45:12.350Z",
  "latitude": 38.812345,
  "longitude": -75.134567,
  "evidence_path": "/data/storage/live_sonar/3fa85f64/evidence/track_12.json"
}
```
Supported lifecycle events:
- `session_started`: Live pipeline launched and running
- `session_stopped`: Live pipeline stopped cleanly
- `connection_lost`: Source stream dropped (e.g. RTSP timeout)
- `connection_restored`: Source stream re-established
- `detection_created`: New candidate detection spotted
- `track_confirmed`: Target reached confirmation threshold (N-of-M frames)
- `track_lost`: Target expired or left field of view
- `buffer_warning`: Frame queue depth exceeded 75% capacity
- `processing_degraded`: Processing FPS falling behind acquisition rate
- `error`: Unrecoverable error occurred (with structured error code)

### 4.2 REST API Specification (`/api/v1/live-sonar/`)

#### 1. `POST /api/v1/live-sonar/sessions`
Create a new live sonar session.
- **Request Body:**
  ```json
  {
    "name": "Live Towfish Survey Run 4",
    "source_type": "replay",
    "source_uri": "data/test_sonar_images",
    "target_fps": 15.0,
    "inference_fps": 10.0,
    "buffer_size": 60,
    "drop_policy": "DROP_OLDEST",
    "preprocessing_profile": "REALTIME",
    "enable_tracking": true,
    "enable_recording": false,
    "confidence_threshold": 0.35,
    "minimum_confirmed_frames": 3
  }
  ```
- **Validation:**
  - `source_type` must be one of `['replay', 'rtsp', 'usb', 'native_stub']`.
  - `source_uri` validated against SSRF and directory traversal rules.
  - `target_fps` between 1.0 and 60.0.
  - `preprocessing_profile` must be one of `['REALTIME', 'BALANCED', 'QUALITY']`.
- **Response 201:** Full session object with `status: "CONNECTING"`.

#### 2. `GET /api/v1/live-sonar/sessions`
List all live sessions.
- **Query Parameters:** `status` (optional), `limit` (default 20), `offset` (default 0).
- **Response 200:** Standard envelope with array of sessions.

#### 3. `GET /api/v1/live-sonar/sessions/{session_id}`
Retrieve session detail, aggregate counters, and configuration.
- **Response 200:** Session metadata and current status.
- **Response 404:** If session does not exist.

#### 4. `POST /api/v1/live-sonar/sessions/{session_id}/start`
Start stream ingestion and inference worker for a session.
- **Response 200:** `{"success": true, "data": {"status": "RUNNING"}}`.

#### 5. `POST /api/v1/live-sonar/sessions/{session_id}/stop`
Stop stream ingestion and inference worker cleanly.
- **Response 200:** `{"success": true, "data": {"status": "STOPPED"}}`.

#### 6. `POST /api/v1/live-sonar/sessions/{session_id}/pause` & `resume`
Pause/resume frame ingestion (especially for replay sources).

#### 7. `GET /api/v1/live-sonar/sessions/{session_id}/metrics`
Returns current real-time telemetry: `input_fps`, `inference_fps`, `display_fps`, `latency_ms`, `queue_depth`, `frames_dropped`.

#### 8. `GET /api/v1/live-sonar/sessions/{session_id}/tracks`
List tracks observed in the session.
- **Query Parameters:** `status` (`CONFIRMED`, `ACTIVE`, `LOST`), `class_name`, `min_confidence`.

#### 9. `GET /api/v1/live-sonar/sessions/{session_id}/detections`
List detection events for audit.
- **Query Parameters:** `track_id`, `limit`, `offset`.

#### 10. `GET /api/v1/live-sonar/sessions/{session_id}/evidence`
List captured evidence packages for confirmed targets.

#### 11. `GET /api/v1/live-sonar/health`
System-wide live sonar health reporting:
- Source connection status
- Active sessions count
- GPU device and memory allocation
- Inference model readiness (`READY` / `MISSING_WEIGHTS`)
- Tracker registry memory load

### 4.3 Strict Security Constraints

#### 1. Server-Side Request Forgery (SSRF) Prevention
- **Protocol Allowlist:** Only `rtsp://`, `rtsps://`, `file://` (restricted), and `device://` schemes are accepted. Schemas such as `http://`, `https://`, `gopher://`, `dict://`, and `ftp://` are rejected.
- **IP Address & Hostname Validation:**
  - Cloud metadata IP `169.254.169.254` is strictly blocked.
  - Loopback (`127.0.0.1`, `localhost`) is blocked in production mode (allowed only when `ENVIRONMENT=development` or `LIVE_SONAR_ALLOW_LOCAL=true`).
  - Private network CIDR allowlisting: Configured via `LIVE_SONAR_NETWORK_ALLOWLIST` (e.g. `["192.168.0.0/16", "10.0.0.0/8"]`).
  - DNS Rebinding protection: Resolved IP address is checked prior to socket connection.

#### 2. Path Traversal Prevention
- Replay files must resolve strictly within permitted storage roots:
  - `./data/storage/`
  - `./data/demo/`
  - `./data/test_sonar_images/`
  - `./data/recordings/`
- Attempts containing `..`, leading slashes outside root, or null bytes return `400 VALIDATION_ERROR`.

#### 3. Credential Hygiene
- Any embedded credentials in RTSP URIs (e.g. `rtsp://admin:secretPass@192.168.1.100/sonar`) are stripped immediately upon validation.
- Sanitized URI stored in DB: `rtsp://***:***@192.168.1.100/sonar`.
- Credentials are NEVER exposed in REST responses, WebSocket messages, log files, or database columns.

#### 4. Command Injection Prevention
- All video capture and decoder interfaces use Python native bindings or safe API parameters. No shell commands (`os.system` or `subprocess.Popen(..., shell=True)`) are executed.

---

## 5. Requirement R5: Persistence, Recording, Database Schema & Alembic Migration

### 5.1 Database Models (`backend/database/models.py`)
Four new SQLAlchemy 2.0 async ORM models extend the existing schema without creating a separate database:

```python
class LiveSonarSession(Base):
    """Represents a live sonar acquisition and tracking session."""
    __tablename__ = "live_sonar_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_uri_sanitized: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="CONNECTING")
    preprocessing_profile: Mapped[str] = mapped_column(String(32), nullable=False, default="REALTIME")
    target_fps: Mapped[float] = mapped_column(Float, nullable=False, default=15.0)
    inference_fps: Mapped[float] = mapped_column(Float, nullable=False, default=10.0)
    is_recording: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    recording_storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    total_frames_received: Mapped[int] = mapped_column(BigInteger, default=0)
    total_frames_processed: Mapped[int] = mapped_column(BigInteger, default=0)
    total_frames_dropped: Mapped[int] = mapped_column(BigInteger, default=0)
    total_detections: Mapped[int] = mapped_column(Integer, default=0)
    total_tracks: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('replay', 'rtsp', 'usb', 'native_stub')",
            name="ck_live_sessions_source_type"
        ),
        CheckConstraint(
            "status IN ('CONNECTING', 'CONNECTED', 'RUNNING', 'DEGRADED', 'STOPPING', 'STOPPED', 'ERROR')",
            name="ck_live_sessions_status"
        ),
        Index("idx_live_sessions_status", "status"),
        Index("idx_live_sessions_created", text("created_at DESC")),
    )

    # Relationships
    tracks: Mapped[List["LiveTrack"]] = relationship("LiveTrack", back_populates="session", cascade="all, delete-orphan")
    detection_events: Mapped[List["LiveDetectionEvent"]] = relationship("LiveDetectionEvent", back_populates="session", cascade="all, delete-orphan")
    evidence_items: Mapped[List["LiveEvidence"]] = relationship("LiveEvidence", back_populates="session", cascade="all, delete-orphan")


class LiveTrack(Base):
    """Persistent representation of a target track generated by ByteTrack."""
    __tablename__ = "live_tracks"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UuidType, ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False)  # Tracker integer ID within session
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence_initial: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_latest: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_smoothed: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="TENTATIVE")
    is_confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    confirmed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(nullable=False)
    total_frames_seen: Mapped[int] = mapped_column(Integer, default=1)
    trajectory: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)  # List of {x, y, t}
    last_bbox: Mapped[Optional[Dict[str, Any]]] = mapped_column(JsonType, nullable=True)    # {x, y, w, h}
    estimated_length_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    estimated_width_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geotagging_available: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    shadow_status: Mapped[str] = mapped_column(String(32), default="unavailable")
    evidence_storage_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("session_id", "track_id", name="uq_session_track_id"),
        Index("idx_live_tracks_session", "session_id"),
        Index("idx_live_tracks_status", "status"),
        Index("idx_live_tracks_confirmed", "is_confirmed"),
        Index("idx_live_tracks_latlon", "latitude", "longitude"),
    )

    # Relationships
    session: Mapped["LiveSonarSession"] = relationship("LiveSonarSession", back_populates="tracks")
    events: Mapped[List["LiveDetectionEvent"]] = relationship("LiveDetectionEvent", back_populates="track", cascade="all, delete-orphan")
    evidence: Mapped[Optional["LiveEvidence"]] = relationship("LiveEvidence", back_populates="track", uselist=False)


class LiveDetectionEvent(Base):
    """Audit log of candidate and confirmed detection events across frames."""
    __tablename__ = "live_detection_events"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UuidType, ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False)
    live_track_id: Mapped[Optional[uuid.UUID]] = mapped_column(UuidType, ForeignKey("live_tracks.id", ondelete="SET NULL"), nullable=True)
    frame_id: Mapped[str] = mapped_column(String(64), nullable=False)
    sequence_number: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timestamp_utc: Mapped[datetime] = mapped_column(nullable=False)
    class_name: Mapped[str] = mapped_column(String(64), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    confidence_calibrated: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    sonar_range_m: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    geotagging_available: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    processing_latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    model_version: Mapped[str] = mapped_column(String(64), default="1.0.0")
    is_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=text("now()"))

    __table_args__ = (
        Index("idx_live_events_session", "session_id"),
        Index("idx_live_events_track", "live_track_id"),
        Index("idx_live_events_seq", "sequence_number"),
        Index("idx_live_events_timestamp", "timestamp_utc"),
    )

    # Relationships
    session: Mapped["LiveSonarSession"] = relationship("LiveSonarSession", back_populates="detection_events")
    track: Mapped[Optional["LiveTrack"]] = relationship("LiveTrack", back_populates="events")


class LiveEvidence(Base):
    """Forensic evidence package captured when a target is confirmed."""
    __tablename__ = "live_evidence"

    id: Mapped[uuid.UUID] = mapped_column(UuidType, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UuidType, ForeignKey("live_sonar_sessions.id", ondelete="CASCADE"), nullable=False)
    live_track_id: Mapped[uuid.UUID] = mapped_column(UuidType, ForeignKey("live_tracks.id", ondelete="CASCADE"), nullable=False, unique=True)
    frame_id: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    processed_image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    annotated_image_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JsonType, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, server_default=text("now()"))

    __table_args__ = (
        Index("idx_live_evidence_session", "session_id"),
        Index("idx_live_evidence_track", "live_track_id"),
    )

    # Relationships
    session: Mapped["LiveSonarSession"] = relationship("LiveSonarSession", back_populates="evidence_items")
    track: Mapped["LiveTrack"] = relationship("LiveTrack", back_populates="evidence")
```

### 5.2 Alembic Migration Plan: `0003_live_sonar_subsystem.py`
The migration cleanly applies on top of existing revision `0002_ml_segmentation_classification`:
- **File:** `backend/database/migrations/versions/0003_live_sonar_subsystem.py`
- **Revision ID:** `0003_live_sonar_subsystem`
- **Down Revision:** `0002_ml_segmentation_classification`
- **Upgrade Operations:**
  1. `op.create_table('live_sonar_sessions', ...)`
  2. `op.create_table('live_tracks', ...)`
  3. `op.create_table('live_detection_events', ...)`
  4. `op.create_table('live_evidence', ...)`
  5. Create all corresponding indexes and foreign key cascades.
- **Downgrade Operations:**
  1. `op.drop_table('live_evidence')`
  2. `op.drop_table('live_detection_events')`
  3. `op.drop_table('live_tracks')`
  4. `op.drop_table('live_sonar_sessions')`

### 5.3 Unbroken Traceability Chain
Every confirmed target in the system satisfies the full traceability invariant:
$$\text{Source Stream / File} \longrightarrow \text{Live Session} \longrightarrow \text{Frame (ID + Sequence)} \longrightarrow \text{Model Checkpoint (SHA256)} \longrightarrow \text{Preprocessing Profile} \longrightarrow \text{UTC Timestamp} \longrightarrow \text{Navigation Telemetry} \longrightarrow \text{Evidence Artifact (Raw + Annotated)}$$

Verification schema in `live_evidence.metadata_json`:
```json
{
  "traceability": {
    "session_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "track_id": 12,
    "frame_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    "sequence_number": 1042,
    "timestamp_utc": "2026-09-19T05:45:12.345Z",
    "source_type": "replay",
    "source_uri_sanitized": "data/test_sonar_images/marine-debris-aris3k-64.png",
    "model_checkpoint": "models/detection/sonar_yolov8_fls_trained.pt",
    "model_sha256": "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7",
    "preprocessing_profile": "REALTIME",
    "class_name": "derelict_fishing_gear",
    "confidence_raw": 0.88,
    "confidence_calibrated": 0.84,
    "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
    "navigation": {
      "latitude": 38.812345,
      "longitude": -75.134567,
      "heading_deg": 184.2,
      "depth_m": 14.5
    },
    "artifacts": {
      "raw_frame": "live_sonar/3fa85f64/evidence/track_12_raw.png",
      "processed_frame": "live_sonar/3fa85f64/evidence/track_12_processed.png",
      "annotated_frame": "live_sonar/3fa85f64/evidence/track_12_annotated.png"
    }
  }
}
```

### 5.4 Recording & Replay Parity
- **Recording Architecture:** When `is_recording = True`, the adapter writes incoming frames to `{STORAGE_ROOT}/live_sonar/{session_id}/recording/` in MP4 container format (H.264 / MJPEG) alongside `telemetry.jsonl` (streaming JSON Lines with per-frame GPS and sonar telemetry).
- **Parity Principle:** Any recorded stream can subsequently be selected as a `ReplayStreamAdapter` source. Because the replay adapter yields the exact same `SonarFrame` structure, the identical preprocessing, detection, tracking, and WebSocket code paths are executed, guaranteeing 100% replay parity.

---

## 6. Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|---|---|---|---|---|---|---|
| 1 | R1 Streaming | `SonarStreamAdapter` Interface | Abstract base class defining common stream lifecycle and frame delivery contract | Hardware/network/file URI | AsyncIterator[SonarFrame], health, metadata | Strict subclass verification | `ORIGINAL_REQUEST.md` R1 |
| 2 | R1 Streaming | `ReplayStreamAdapter` | Replays video files (.mp4/.mkv), XTF logs, and PNG sequences using live pipeline | File/dir path, target FPS, loop flag | Normalized `SonarFrame` stream | 400 on missing file, graceful EOF | `ORIGINAL_REQUEST.md` R1 |
| 3 | R1 Streaming | `RTSPStreamAdapter` | Connects to live IP sonar / camera encoder feeds over RTSP/RTSPS | RTSP URI, auth, transport mode | Decoded `SonarFrame` stream | Exponential backoff reconnect, `connection_lost` event | `ORIGINAL_REQUEST.md` R1 |
| 4 | R1 Streaming | `USBCameraStreamAdapter` | Captures from local direct-show / v4l2 capture cards | Device index (`device://0`) | Native resolution frames | Error if device busy/disconnected | `ORIGINAL_REQUEST.md` R1 |
| 5 | R1 Streaming | `NativeSonarStubAdapter` | Integration boundary for ARIS/DIDSON/Blueprint acoustic heads | Driver config | Stream with `status=NOT_CONFIGURED` | Structured error, zero unhandled crashes | `ORIGINAL_REQUEST.md` R1 |
| 6 | R1 Streaming | `SonarFrameBuffer` | Bounded async queue with configurable drop policies preventing RAM overflow | `SonarFrame`, policy (`DROP_OLDEST`) | Dequeued frame, drop metrics | Increments `frames_dropped` on full | `ORIGINAL_REQUEST.md` R1 |
| 7 | R1 Streaming | Backpressure Telemetry | Real-time calculation of input, processing, effective FPS and latency | Frame arrival & process timestamps | FPS metrics & queue depth | Triggers `DEGRADED` state | `ORIGINAL_REQUEST.md` R1 |
| 8 | R1 Streaming | `LiveSonarSession` Lifecycle | State machine managing session transitions (CONNECTING $\to$ RUNNING $\to$ STOPPED) | User start/stop commands | Session status & aggregate stats | Transitions to `ERROR` on crash | `ORIGINAL_REQUEST.md` R1 |
| 9 | R2 Preprocessing | `REALTIME` Profile | High-speed normalization + fast CLAHE targeting $\le 15\text{ ms}$ budget | Raw `SonarFrame` image | Preprocessed tensor for YOLOv8 | Fallback to raw copy if CLAHE fails | `ORIGINAL_REQUEST.md` R2 |
| 10 | R2 Preprocessing | `BALANCED` Profile | Reuses standard pipeline (quality $\to$ bottom $\to$ water $\to$ CLAHE $\to$ denoise $\to$ slant) | Raw `SonarFrame` image | Cleaned acoustic image | Skips steps if ping metadata missing | `backend/preprocessing/pipeline.py` |
| 11 | R2 Preprocessing | `QUALITY` Profile | Integrates `backend/enhancement/` (Bilateral / Log-Bilateral CLAHE + de-striping) | Raw `SonarFrame` image | High-fidelity enhanced image | Reverts to CLAHE if filter fails | `backend/enhancement/profiles.py` |
| 12 | R2 AI Pipeline | Raw Frame Immutability | Strict memory isolation between raw, processed, model, and annotated representations | Incoming frame array | 4 separate frame buffers | `writeable = False` prevents mutation | `ORIGINAL_REQUEST.md` R2 |
| 13 | R2 AI Pipeline | YOLOv8 Model Singleton | Reuses `ModelLoader` singleton with production checkpoint | `sonar_yolov8_fls_trained.pt` | In-memory YOLO model instance | Returns `MISSING_WEIGHTS` if missing | `backend/inference/model_loader.py` |
| 14 | R2 AI Pipeline | Decoupled Inference Worker | Asynchronous background worker running forward pass with frame skipping | Frame queue, target inference FPS | RawDetection instances, latency | Automatically scales skipping under load | `ORIGINAL_REQUEST.md` R2 |
| 15 | R2 Tracking | ByteTrack Tracking Engine | 2-stage association (high-conf + low-conf matching) via Kalman filter | `RawDetection` list, frame timestamp | Updated `Track` objects | Preserves track during acoustic dropout | `ORIGINAL_REQUEST.md` R2 |
| 16 | R2 Tracking | Tracker Isolation | Isolated Kalman filter and track registry per live session | Session ID | Session-scoped tracker instance | No cross-session track leakage | `ORIGINAL_REQUEST.md` R2 |
| 17 | R2 Tracking | Temporal Target Confirmation | Requires target observation across $N$-of-$M$ frames before confirmation alert | Track observation history | Track status `CONFIRMED` | Suppresses single-frame false alarms | `ORIGINAL_REQUEST.md` R2 |
| 18 | R2 Tracking | Multi-Frame Class Consistency | Cumulative class probability voting across track lifetime | Per-frame class predictions | Stable track class label | Prevents class flipping on noise | `ORIGINAL_REQUEST.md` R2 |
| 19 | R2 Tracking | Acoustic Shadow Reasoning | Evaluates presence of shadow behind target highlight | Bbox and polar/cartesian acoustic patch | `Shadow support: detected/unavailable` | Emits `unavailable` at boundary | `backend/postprocessing/shadow_filter.py` |
| 20 | R2 Tracking | Live Georeferencing | WGS84 bearing-distance projection using real-time towfish navigation | Ping lat, lon, heading, bbox | Target lat/lon coordinates | Sets null if GPS unavailable | `backend/georeferencing/geotagger.py` |
| 21 | R3 WebSocket | Live Frame Push | High-frequency stream of detections, tracks, metrics, and preview JPEG | Redis pub/sub channel | Client WebSocket frame message | Client disconnect handled cleanly | `backend/api/routers/ws.py` |
| 22 | R3 WebSocket | Lifecycle Event Push | Pushes discrete events (`session_started`, `track_confirmed`, `connection_lost`) | Pipeline events | Client WebSocket event JSON | Non-blocking broadcast | `ORIGINAL_REQUEST.md` R3 |
| 23 | R3 REST API | Session Management API | Endpoints for creating, listing, starting, stopping, pausing sessions | HTTP requests at `/api/v1/live-sonar` | JSON response envelope | Standard 400/404/409 error responses | `ORIGINAL_REQUEST.md` R3 |
| 24 | R3 REST API | Live Telemetry & Health API | Endpoints querying live FPS, latency, GPU load, tracker state | GET `/metrics`, GET `/health` | Real-time performance JSON | Degraded status returned if dropping | `ORIGINAL_REQUEST.md` R3 |
| 25 | R3 Security | SSRF Validation | Validates source IP and hostname against allowlists and blocks loopback/metadata | Source URI string | Sanitized URI or error | 400 Bad Request on SSRF attempt | `ORIGINAL_REQUEST.md` R3 |
| 26 | R3 Security | Credential Scrubbing | Strips username/password from RTSP URIs before logging/storage | Raw RTSP URI | Sanitized URI (`***:***`) | Logs never expose plain credentials | `ORIGINAL_REQUEST.md` R3 |
| 27 | R5 Persistence | Live Session ORM Model | Persists live session parameters, status, and aggregate metrics | SQLAlchemy ORM | Database row in `live_sonar_sessions` | Transaction rollback on failure | `backend/database/models.py` |
| 28 | R5 Persistence | Live Track ORM Model | Persists confirmed tracks, trajectory history, and georeference coordinates | SQLAlchemy ORM | Database row in `live_tracks` | Cascade delete on session removal | `ORIGINAL_REQUEST.md` R5 |
| 29 | R5 Persistence | Live Detection Event Model | Audit log of individual detection events linked to frames and tracks | SQLAlchemy ORM | Database row in `live_detection_events` | Indexed for time-series queries | `ORIGINAL_REQUEST.md` R5 |
| 30 | R5 Persistence | Forensic Evidence Storage | Saves raw, processed, and annotated image artifacts for confirmed tracks | Confirmed target trigger | PNG images and JSON metadata on disk | Log warning if disk write fails | `ORIGINAL_REQUEST.md` R5 |
| 31 | R5 Persistence | Alembic Lineage Extension | Migration `0003_live_sonar_subsystem.py` applying clean schema changes | Alembic CLI | PostgreSQL schema upgraded | Clean downgrade drops new tables | `backend/database/migrations/` |
| 32 | R5 Persistence | Stream Recording & Replay | Records live feed into video container + JSONL telemetry for replay | Live frame stream | Storage artifacts ready for replay | Ensures 100% live/replay parity | `ORIGINAL_REQUEST.md` R5 |

---

## 7. Edge Cases & Boundary Behaviors

| # | Feature | Input / Condition | Expected & Observed Behavior |
|---|---|---|---|
| 1 | `ReplayStreamAdapter` | Replay source file does not exist on disk | Raises `ValidationError` / `LiveSonarSourceInvalidError` with HTTP 400; returns structured error JSON; session is not started. |
| 2 | `ReplayStreamAdapter` | Replay video file finishes (End of Stream) with `loop=False` | Frame generator terminates cleanly; worker catches termination; session automatically transitions to `status="STOPPED"`; publishes `session_stopped` WebSocket event. |
| 3 | `RTSPStreamAdapter` | Network cable unplugged or RTSP server unreachable | Adapter attempts reconnection with exponential backoff (1s, 2s, 4s... max 30s); emits `connection_lost` event; UI shows `RECONNECTING...`; after max attempts transitions to `ERROR`. Never freezes-and-pretends. |
| 4 | `USBCameraStreamAdapter` | Device index disconnected during active capture | Frame grab returns `False`; adapter signals connection drop; closes capture handle; session marks error `DEVICE_DISCONNECTED`. |
| 5 | `NativeSonarStubAdapter` | Native SDK drivers / hardware absent | Adapter `connect()` raises `LiveSonarSourceConnectionError("NATIVE_SONAR_UNAVAILABLE")`; reports `status="NOT_CONFIGURED"`; does not crash FastAPI server. |
| 6 | `SonarFrameBuffer` | Ingestion produces 30 FPS, inference handles 10 FPS (`DROP_OLDEST`) | Queue depth fills to limit (60); incoming frames displace oldest unconsumed frames; `frames_dropped` counter increments; `drop_rate` metric exposed; no memory leak. |
| 7 | `SonarFrameBuffer` | Queue capacity set to 1 with `LATEST` policy | Buffer holds strictly newest single frame; inference always processes the most recent acoustic sweep; drops all intervening frames. |
| 8 | Preprocessing | Input frame has corrupt dimensions or zero size (`image.size == 0`) | Quality check flags dropout; preprocessing pipeline logs warning and returns empty tile list; inference worker safely skips forward pass. |
| 9 | Preprocessing | Frame lacks sonar altitude or slant-range parameters | `correct_slant_range()` falls back to raw or identity mapping; `SonarFrame.sonar_metadata.range_m` remains `None`. No synthetic values inserted. |
| 10 | ByteTrack Tracker | Target temporarily obscured by acoustic multipath fading (conf drops to 0.2) | Stage 2 association matches low-confidence detection with active Kalman track; track ID persists across consecutive frames without resetting. |
| 11 | ByteTrack Tracker | Target moves out of field of view for > 30 frames (`frames_missing > max_age`) | Track status changes from `ACTIVE` / `CONFIRMED` to `LOST`; emits `track_lost` WebSocket event; track removed from active tracker pool. |
| 12 | Target Confirmation | Transient single-frame false alarm spike ($conf = 0.92$, 1 frame only) | Track initialized as `TENTATIVE`; fails the $N$-of-$M$ (3 frames) confirmation gate; no alert emitted; drops after track expires. |
| 13 | Georeferencing | Towfish telemetry lacks GPS fix (`latitude = None`, `longitude = None`) | `geotag_detection()` returns `geotagging_available = False`, `latitude = None`, `longitude = None`; UI displays `GPS: NOT_AVAILABLE`. Never fabricates lat/lon. |
| 14 | WebSocket Server | Client suddenly disconnects or closes browser tab | FastAPI WebSocket handler catches `WebSocketDisconnect`; cleans up Redis pub/sub subscription and task; avoids leaked socket handles. |
| 15 | WebSocket Server | Redis pub/sub broker temporarily offline | WebSocket endpoint falls back gracefully or returns HTTP 503 `WORKER_UNAVAILABLE`; does not crash core FastAPI process. |
| 16 | Security (SSRF) | User supplies `rtsp://169.254.169.254/sonar` (cloud metadata IP) | URI validation detects link-local metadata address; raises `LiveSonarSecurityViolationError` HTTP 400; blocks socket creation. |
| 17 | Security (SSRF) | User supplies `rtsp://127.0.0.1:8554/live` in production environment | Rejected unless `LIVE_SONAR_ALLOW_LOCAL=true`; blocks access to loopback network interfaces. |
| 18 | Security (Path Traversal)| User supplies `file:///etc/passwd` or `replay://../../windows/system32` | Path resolution verifies file is not within authorized `./data/storage` or `./data/demo` roots; raises `ValidationError` HTTP 400. |
| 19 | Security (Credentials) | User supplies `rtsp://admin:hunter2@192.168.1.55:554/stream` | Adapter parses and strips credentials; stores sanitized URI `rtsp://***:***@192.168.1.55:554/stream`; plain password never printed in logs or DB. |
| 20 | Model Loader | Detection checkpoint file corrupted or truncated | `ModelLoader.get_model_status()` catches loading failure; reports `state="INVALID_WEIGHTS"`; inference worker falls back to zero-weight mode with clear error. |

---

## 8. Implementation Guidance & Non-Negotiable Checklist for Implementers

1. **Module Directory Structure:** Place all live streaming code strictly inside `backend/live_sonar/`:
   - `backend/live_sonar/__init__.py`
   - `backend/live_sonar/models.py` (Dataclasses and Pydantic schemas)
   - `backend/live_sonar/buffer.py` (Bounded async frame buffer)
   - `backend/live_sonar/adapters/` (`base.py`, `replay.py`, `rtsp.py`, `usb.py`, `native_stub.py`)
   - `backend/live_sonar/tracking/` (`tracker.py`, `kalman.py`, `matching.py`)
   - `backend/live_sonar/worker.py` (Decoupled inference loop)
   - `backend/live_sonar/service.py` (Session manager and orchestration)
   - `backend/live_sonar/security.py` (SSRF, allowlist, and path validation)
2. **FastAPI Router Integration:**
   - Mount REST routes under `/api/v1/live-sonar/` in `backend/api/routers/live_sonar.py`.
   - Include router in `backend/api/main.py`.
   - Mount WebSocket route at `/ws/live-sonar/{session_id}` (and alias under `/api/v1/ws/live-sonar/{session_id}`).
3. **Database & Migrations:**
   - Add ORM models in `backend/database/models.py`.
   - Add migration script `backend/database/migrations/versions/0003_live_sonar_subsystem.py`.
4. **Safety Confirmation:**
   - Checksum of `models/detection/sonar_yolov8_fls_trained.pt` must remain `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`.
   - `datasets/sonar_debris_v2_clean` must remain untouched.
   - All tests in `tests/backend/` must continue to pass (`pytest`).
