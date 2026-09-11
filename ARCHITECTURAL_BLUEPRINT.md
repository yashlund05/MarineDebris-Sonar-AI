# ARCHITECTURAL_BLUEPRINT.md
## MarineDebris-Sonar-AI — System Architecture

**Version:** 1.0  
**Date:** August 2026  

---

## 1. Tech Stack

### Backend
| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.11 |
| API Framework | FastAPI | 0.111.x |
| ASGI Server | Uvicorn | 0.29.x |
| Task Queue | Celery | 5.4.x |
| Message Broker | Redis | 7.2 |
| ORM | SQLAlchemy | 2.0.x |
| DB Migrations | Alembic | 1.13.x |
| Database | PostgreSQL | 16 |
| File Storage | Local filesystem (S3-compatible interface via MinIO for prod) | MinIO latest |
| Sonar Parsing | pyxtf (XTF), custom JSF parser | pyxtf 1.4+ |
| Sonar Processing | OpenCV, NumPy, SciPy | cv2 4.9, numpy 1.26 |
| ML Framework | PyTorch | 2.3.x |
| Object Detection | Ultralytics YOLO — **YOLOv8 is the baseline detector** for all implementation. YOLOv9 is listed only for possible future experimentation/comparison; it is not an implementation choice for MVP/V1. | ultralytics 8.2.x |
| Segmentation | segmentation-models-pytorch (U-Net / SegFormer) | 0.3.x |
| Geospatial | pyproj, Shapely, GeoPandas | pyproj 3.6 |
| Config | Pydantic Settings | 2.x |
| Logging | structlog | 24.x |
| Testing | pytest, pytest-asyncio | pytest 8.x |

### Frontend
| Layer | Technology | Version |
|---|---|---|
| Language | TypeScript | 5.4 |
| Framework | React | 18.x |
| Build Tool | Vite | 5.x |
| UI Component Library | shadcn/ui + Tailwind CSS | Tailwind 3.x |
| Map | Leaflet + react-leaflet | Leaflet 1.9 |
| Sonar Viewer | Custom HTML5 Canvas component | — |
| State Management | Zustand | 4.x |
| Data Fetching | TanStack Query (React Query) | 5.x |
| Charts / Metrics | Recharts | 2.x |
| File Upload | react-dropzone | 14.x |
| HTTP Client | Axios | 1.6.x |

### Infrastructure / DevOps
| Layer | Technology |
|---|---|
| Containerisation | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| GPU Support | NVIDIA CUDA 12.1 (PyTorch GPU build) |
| Environment Config | .env files + Pydantic Settings |
| CI | GitHub Actions |

---

## 2. System Architecture — Monolith-first with internal module boundaries

The system uses a **modular monolith** architecture for V1. Each functional area is a clearly separated Python package inside the backend. This allows the team to move fast without microservice overhead while preserving the option to extract services (e.g., the inference worker) later.

**Event flow clarification (Celery / Redis / WebSocket):** Celery workers never manage browser WebSocket connections directly. The flow is: Celery task executes a pipeline stage → task publishes a progress event to Redis (pub/sub channel keyed by `job_id`, using Redis both as the Celery broker/result backend and as this lightweight event bus) → the FastAPI process's WebSocket router (`backend/api/routers/ws.py`) subscribes to that channel and relays matching events to any connected browser client for that `job_id`. The DB (`processing_jobs.progress_pct`, `current_stage`) remains the durable source of truth; the WebSocket push is a best-effort UI convenience, not the system of record.

**Streaming/chunked processing:** The system must remain usable on long sonar logs without loading an entire survey into RAM as one array. See §5 for the chunked `SonarFrame` contract and §9 for the processing flow.

```
┌────────────────────────────────────────────────────┐
│                    FRONTEND (React)                │
│   Upload UI │ Sonar Viewer │ Map │ Reports │ Demo  │
└──────────────────────┬─────────────────────────────┘
                       │ HTTPS / REST + WebSocket
┌──────────────────────▼─────────────────────────────┐
│                FastAPI Backend                     │
│  /api/v1/...                                       │
│  Auth middleware │ Upload handler │ Job status WS  │
└─────────┬─────────────────────────────┬────────────┘
          │ Enqueue job                 │ Read results
┌─────────▼──────────┐      ┌───────────▼────────────┐
│   Celery Worker    │      │     PostgreSQL DB        │
│  (processing jobs, │      │  jobs, detections,      │
│   chunked/streamed)│      │  surveys, metadata       │
│                    │      └────────────────────────┘
│  Pipeline:         │
│  0. Quality/motion  │      ┌────────────────────────┐
│     scoring layer   │      │   Redis                │
│  1. Ingest (chunked)│◄────►│   - Celery broker/      │
│  2. Parse metadata  │      │     result backend      │
│  3. Preprocess      │      │   - job_progress        │
│  4. Tile             │     │     pub/sub channel,    │
│  5. Detect (YOLOv8) │      │     consumed by FastAPI │
│  6. Segment (opt.)   │      │     WS router only     │
│  7. NMS + filter    │      └────────────────────────┘
│  8. Geotag          │
│  9. Report export   │      ┌────────────────────────┐
└────────────────────┘      │   File Storage          │
                            │   (local / MinIO)       │
                            │   raw sonar, tiles,     │
                            │   reports, models       │
                            └────────────────────────┘
```

---

## 3. Data Flow Diagram (Mermaid)

```mermaid
flowchart TD
    A[User uploads XTF/JSF/PNG via Dashboard] --> B[FastAPI: POST /api/v1/surveys/upload]
    B --> C[Save raw file to File Storage]
    C --> D[Create Survey record in PostgreSQL]
    D --> E[Enqueue Celery processing job]
    E --> F{File type?}
    F -->|XTF| G[sonar_parser: streaming/chunked parse, extract pings + nav metadata]
    F -->|PNG strip| H[image_ingestor: load image + optional nav CSV]
    G --> QL[quality: dropout detection, degraded-region flagging, quality score]
    H --> QL
    QL --> I[preprocessing: bottom detection, slant-range, CLAHE, denoising, water-column removal]
    I --> J[tile_builder: generate overlapping tiles 640x640]
    J --> K[inference/detect: YOLOv8 forward pass per tile]
    K --> L{Segmentation enabled?}
    L -->|Yes| M[inference/segment: U-Net/SegFormer mask per detection]
    L -->|No| N[postprocessing: NMS, shadow context filter, confidence calibration]
    M --> N
    N --> O[georeferencing: pixel bbox + ping nav → lat/lon + dimensions]
    O --> P[reporting: write JSON + CSV + GeoJSON to File Storage]
    P --> Q[Update Detection records in PostgreSQL]
    Q --> R[WebSocket push: job complete]
    R --> S[Frontend: render sonar viewer + map + report links]
```

---

## 4. Pipeline Module Responsibilities

| Module | Package Path | Responsibility |
|---|---|---|
| Sonar Parser | `backend/sonar_parser/` | Stream/chunk-parse XTF binary format (MVP), extract ping data, navigation (lat/lon/heading/pitch/roll/altitude/range), sonar config. JSF parsing (`jsf_parser.py`) is present in the package for forward compatibility but deferred until XTF/PNG paths are validated (V1). |
| Image Ingestor | `backend/ingestion/` | Accept PNG sonar strips (MVP) + optional nav CSV; normalize to internal chunked `SonarFrame` format. TIFF ingestion deferred (V1). |
| Quality / Motion Robustness Layer | `backend/preprocessing/quality.py` | Sonar Quality / Motion Robustness Layer: per-chunk quality score, dropout/degraded-region detection; flags (not fully compensates) heave/pitch/roll effects when attitude metadata is present; runs before the rest of preprocessing |
| Preprocessor | `backend/preprocessing/` | MVP: bottom-line detection, slant-range correction, radiometric normalization, CLAHE, speckle denoising, water-column removal. V1: port/starboard channel separation as a distinct path. |
| Tile Builder | `backend/preprocessing/tiler.py` | Slice SonarFrame into 640×640 tiles with configurable overlap; store tile→ping mapping for georeferencing |
| Detector | `backend/inference/detector.py` | Load YOLOv8 weights; run batch inference; return raw bbox list per tile |
| Segmenter | `backend/inference/segmenter.py` | Load U-Net/SegFormer weights; run inference on tiles with detections; return pixel masks |
| Postprocessor | `backend/postprocessing/` | Global NMS across tiles, acoustic-shadow context filter, size/shape constraint filter, confidence calibration |
| Geotagger | `backend/georeferencing/` | Map tile-pixel bbox → survey-pixel → ping-relative range/bearing → WGS84 lat/lon; compute estimated object dimensions |
| Report Generator | `backend/reporting/` | Serialize DetectionResult list to JSON, CSV, GeoJSON; write to storage; create report record |
| API Layer | `backend/api/` | FastAPI routers for upload, job status (WebSocket), detections, reports, model info |
| Celery Worker | `backend/tasks.py` | Orchestrate pipeline steps; update job progress; handle errors |

---

## 5. Internal Data Contracts

### SonarFrame — represents one CHUNK of a survey, not the whole survey

A survey (potentially tens of thousands of pings) is never materialized as a single in-memory array. Ingestion streams the raw file and yields a sequence of `SonarFrame` chunks (default chunk size: a configurable window of pings, e.g. 2,000), each processed independently through preprocessing → tiling → inference before results are aggregated at the survey level. This keeps memory bounded regardless of survey length. See §9 for the chunked processing flow.

```python
@dataclass
class SonarFrame:
    survey_id: str
    source_file: str
    channel: str              # "port" | "starboard"
    chunk_index: int          # position of this chunk within the survey (0-based)
    ping_offset: int          # index of this chunk's first ping within the full survey
    pings: List[SonarPing]
    image_array: np.ndarray   # (chunk_H, W) float32, normalized 0-1 — ONE CHUNK, not the full survey
    metadata: SonarMetadata

@dataclass
class SonarPing:
    ping_number: int           # absolute index within the full survey
    timestamp: float
    latitude: Optional[float]
    longitude: Optional[float]
    heading: Optional[float]
    pitch: Optional[float]     # degrees; populated only if source file provides attitude data
    roll: Optional[float]      # degrees; populated only if source file provides attitude data
    altitude: Optional[float]
    range_m: Optional[float]
    is_dropout: bool           # flagged by the Quality/Motion Robustness Layer
    pixel_y: int               # row index within this chunk's image_array

@dataclass
class SonarMetadata:
    frequency_hz: Optional[float]
    samples_per_ping: int
    range_resolution_m: Optional[float]
    along_track_resolution_m: Optional[float]
    motion_quality_score: Optional[float]   # 0-1, set by the Quality/Motion Robustness Layer for this chunk
    dropout_pct: Optional[float]            # % of pings in this chunk flagged as dropout
```

### DetectionResult (output of postprocessor)
```python
@dataclass
class DetectionResult:
    detection_id: str
    survey_id: str
    source_file: str
    timestamp: str
    class_name: str                          # canonical taxonomy value (PRD.md §8); 'natural_feature' only when is_filtered
    confidence: float                        # Model Confidence — raw YOLOv8 score, NOT a calibrated probability (PRD.md §1.1)
    confidence_calibrated: Optional[float]    # Final Anomaly Confidence — confidence after temperature/Platt calibration + sonar-aware verification adjustment (PRD.md §1.1)
    bbox: Dict               # {x, y, w, h} in survey image pixels
    mask_rle: Optional[str]  # Run-length encoded segmentation mask
    estimated_dimensions_m: Optional[Dict]  # {length, width}
    latitude: Optional[float]     # None when geotagging_available is False
    longitude: Optional[float]    # None when geotagging_available is False
    geotagging_available: bool    # False when source file/ping lacked navigation metadata — never fabricate coordinates
    ping_number: Optional[int]
    filtered_reason: Optional[str]  # Set if detection was suppressed, e.g. "acoustic_shadow_mismatch"
    processing: Dict         # preprocessing_version, model, model_version
```

---

## 6. Streaming / Chunked Processing Flow

```
Raw XTF file
  → streaming/chunked parser (yields SonarFrame chunks, e.g. 2,000 pings each)
  → per-chunk: quality/motion scoring → preprocessing → tile generation → inference
  → detection aggregation across chunks (global NMS in survey-pixel space)
  → geotagging → reporting
```

This is a simple chunked/streaming design, not a distributed-computing system — chunks are processed sequentially (or with a small worker-local queue) within one Celery task. This is sufficient for the batch, single-survey-at-a-time workload defined in scope (PRD.md §4); do not introduce a distributed job-splitting framework unless a concrete requirement demands it.

## 7. Georeferencing — Basic vs. Advanced

**Basic georeferencing (MVP):** For each detection, use the pixel row's associated `SonarPing` — its latitude/longitude, heading, altitude (where available), and slant range — plus sonar geometry (port/starboard, range resolution) to compute a target lat/lon via WGS84 bearing/distance projection. This is available whenever the source file provides per-ping navigation.

**Advanced georeferencing (V2):** Higher-accuracy correction using additional attitude data (pitch/roll, when present) and richer navigation metadata. Not implemented until source datasets are confirmed to provide the required fields — do not claim advanced-tier accuracy from basic-tier inputs.

If navigation metadata is absent for a ping, the corresponding detection(s) are marked `geotagging_available: false` with `latitude`/`longitude` left null. Synthetic/sample navigation metadata may be used only for demo-mode data and must be clearly labeled as simulated in the survey record (e.g. `source_filename` prefixed `demo_`, as in the seed data in `DB_SCHEMA.md`).

---

## 8. Security & Auth

### V1 (Single-user / Internal Deployment)
- No user authentication in V1 (internal research/demo tool).
- API is deployed behind Nginx with IP allowlist.
- CORS restricted to the frontend origin.
- File uploads validated for MIME type and size (max 2 GB per file).
- No user-supplied data is executed or eval'd; sonar files are processed by Python libraries only.

### V2 (Multi-user / Production)
- JWT-based authentication (python-jose).
- Role-based access: `admin`, `operator`, `viewer`.
- All file paths resolved through a storage abstraction; no path traversal possible.
- Secrets managed via environment variables (never hardcoded).
- HTTPS enforced by Nginx + Let's Encrypt.

---

## 9. Model Artifact Management

- Trained model weights stored in `models/` directory (not committed to git; tracked via DVC or manual versioning).
- Model registry entry in PostgreSQL: `model_name`, `version`, `task` (detection/segmentation), `dataset`, `mAP50`, `mAP50_95`, `created_at`. Any specific numeric values shown elsewhere in this documentation (e.g. `DB_SCHEMA.md` seed data) are illustrative/mock until a real training run populates them.
- The active model version for each task is set via environment variable `DETECTION_MODEL_PATH` and `SEGMENTATION_MODEL_PATH`.
- Models are loaded once at Celery worker startup and reused across jobs.

---

## 10. Configuration

All runtime configuration via `.env`:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/marinedebris

# Redis
REDIS_URL=redis://localhost:6379/0

# Storage
STORAGE_BACKEND=local          # local | minio
STORAGE_ROOT=/data/storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=...
MINIO_SECRET_KEY=...

# Models (paths illustrative — actual filenames set once a model is trained and registered)
DETECTION_MODEL_PATH=/models/detection/sonar_yolov8m_ghostpot_v1.pt
SEGMENTATION_MODEL_PATH=/models/segmentation/unet_shipwreck_v1.pt
DETECTION_CONF_THRESHOLD=0.35
NMS_IOU_THRESHOLD=0.45
CALIBRATION_TEMPERATURE=1.4

# Processing
TILE_SIZE=640
TILE_OVERLAP=0.2
DEVICE=cuda                    # cuda | cpu

# API
API_CORS_ORIGINS=http://localhost:5173
MAX_UPLOAD_SIZE_MB=2048
```

---

*End of ARCHITECTURAL_BLUEPRINT.md*
