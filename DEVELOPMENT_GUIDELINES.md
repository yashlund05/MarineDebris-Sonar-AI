# DEVELOPMENT_GUIDELINES.md
## MarineDebris-Sonar-AI — Development Standards & AI Prompting Sequence

**Version:** 1.0 — August 2026  
**Team:** 3 Developers  

---

## 1. Directory Structure

```
MarineDebris-Sonar-AI/
│
├── backend/                          # Python 3.11 — FastAPI application
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app factory, middleware, routers
│   │   ├── dependencies.py           # DB session, settings injection
│   │   └── routers/
│   │       ├── surveys.py            # /api/v1/surveys/...
│   │       ├── jobs.py               # /api/v1/jobs/...
│   │       ├── detections.py         # /api/v1/detections/...
│   │       ├── reports.py            # /api/v1/reports/...
│   │       ├── models.py             # /api/v1/models/...
│   │       ├── ws.py                 # WebSocket /api/v1/ws/jobs/{id}
│   │       └── system.py            # /api/v1/health, /api/v1/demo/...
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── ingestor.py               # Entry point: routes to xtf_parser or PNG image loader (MVP); jsf_parser/TIFF routing wired but returns "not yet supported" (V1, see PRD.md §4.1)
│   │   ├── image_loader.py           # PNG sonar strip loader — MVP; TIFF loader deferred to V1
│   │   └── nav_csv_parser.py         # Parse optional navigation CSV for PNG uploads
│   │
│   ├── sonar_parser/
│   │   ├── __init__.py
│   │   ├── xtf_parser.py             # XTF binary format parsing (wraps pyxtf) — MVP, streaming/chunked
│   │   ├── jsf_parser.py             # JSF binary format parsing (custom) — V1, deferred (stub raising NotImplementedError until scheduled)
│   │   └── models.py                 # SonarFrame (chunk), SonarPing, SonarMetadata dataclasses (ARCHITECTURAL_BLUEPRINT.md §5)
│   │
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── quality.py                # Sonar Quality / Motion Robustness Layer — MVP: dropout detection, degraded-region flagging, quality score
│   │   ├── pipeline.py               # Preprocessing orchestrator
│   │   ├── bottom_detection.py       # Bottom-line detection algorithm
│   │   ├── normalization.py          # Radiometric correction, contrast normalization
│   │   ├── clahe.py                  # CLAHE implementation (wraps OpenCV)
│   │   ├── denoising.py              # Speckle noise reduction
│   │   ├── water_column.py           # Water-column removal
│   │   ├── slant_range.py            # Slant-range correction — MVP
│   │   └── tiler.py                  # Tile generator (640×640 with overlap); records chunk→tile→ping offset mapping for georeferencing
│   │
│   ├── inference/
│   │   ├── __init__.py
│   │   ├── detector.py               # YOLOv8 detection inference
│   │   ├── segmenter.py              # U-Net/SegFormer segmentation inference
│   │   └── model_loader.py           # Singleton model loading at worker startup
│   │
│   ├── postprocessing/
│   │   ├── __init__.py
│   │   ├── nms.py                    # Global NMS across tiles
│   │   ├── shadow_filter.py          # Acoustic-shadow context filter
│   │   ├── size_filter.py            # Object size/shape constraint filter
│   │   └── calibration.py            # Temperature scaling for confidence calibration
│   │
│   ├── georeferencing/
│   │   ├── __init__.py
│   │   ├── geotagger.py              # bbox pixel → WGS84 lat/lon
│   │   └── dimension_estimator.py   # Estimate object real-world dimensions
│   │
│   ├── reporting/
│   │   ├── __init__.py
│   │   ├── json_reporter.py
│   │   ├── csv_reporter.py
│   │   └── geojson_reporter.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py                # Async SQLAlchemy engine + session factory
│   │   ├── models.py                 # SQLAlchemy ORM models
│   │   └── migrations/
│   │       ├── env.py                # Alembic env
│   │       └── versions/             # Migration files
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   └── storage.py                # Abstraction over local / MinIO storage
│   │
│   ├── tasks.py                      # Celery task definitions
│   ├── celery_app.py                 # Celery app factory
│   ├── config.py                     # Pydantic Settings (reads .env)
│   └── requirements.txt
│
├── models/
│   ├── detection/
│   │   └── sonar_yolov8m_ghostpot_v1.pt   # NOT committed to git; tracked by DVC
│   ├── segmentation/
│   │   └── unet_shipwreck_v1.pt
│   └── edge/
│       └── sonar_yolov8n_ghostpot_v1.pt   # Lightweight edge model
│
├── training/
│   ├── datasets/
│   │   ├── ghost_pot_sss/            # Symlink or download script
│   │   ├── subpipe/
│   │   ├── ai4shipwrecks/
│   │   └── seabed_objects/
│   ├── conversion/
│   │   ├── coco_to_yolo.py
│   │   ├── custom_to_yolo.py
│   │   └── annotation_validator.py
│   ├── augmentation/
│   │   └── sonar_augment.py          # Speckle, contrast, shadow, dropout augmentations
│   ├── training/
│   │   ├── train_detector.py         # YOLOv8 training script
│   │   ├── train_segmenter.py        # U-Net/SegFormer training script
│   │   └── survey_split.py           # Survey-level train/val/test split generator
│   └── evaluation/
│       ├── eval_detector.py          # Per-class mAP50/mAP50-95/F1 evaluation
│       ├── eval_segmenter.py         # IoU/Dice evaluation
│       └── eval_geolocation.py       # Geolocation error measurement
│
├── simulator/
│   └── synthetic_sonar/
│       ├── generate_synthetic.py     # Synthetic SSS tile generator for augmentation
│       └── shadow_simulator.py       # Acoustic shadow simulation
│
├── frontend/                         # React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx                   # Router setup (React Router v6)
│   │   ├── api/
│   │   │   ├── client.ts             # Axios instance with base URL
│   │   │   ├── surveys.ts            # API calls for /surveys
│   │   │   ├── detections.ts
│   │   │   ├── reports.ts
│   │   │   ├── models.ts
│   │   │   └── ws.ts                 # WebSocket hook for job progress
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── upload/
│   │   │   ├── sonar/
│   │   │   ├── map/
│   │   │   ├── detections/
│   │   │   ├── reports/
│   │   │   ├── training/
│   │   │   └── ui/
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   ├── SurveyListPage.tsx
│   │   │   ├── SurveyDetailPage.tsx  # Main dashboard view
│   │   │   └── ModelsPage.tsx
│   │   ├── store/
│   │   │   └── useAppStore.ts        # Zustand global store
│   │   ├── hooks/
│   │   │   ├── useJobProgress.ts     # WebSocket job polling hook
│   │   │   └── useSonarViewer.ts     # Canvas pan/zoom hook
│   │   ├── types/
│   │   │   └── index.ts              # Shared TypeScript interfaces
│   │   └── utils/
│   │       ├── formatters.ts         # Coordinate, confidence, dimension formatters
│   │       └── classColors.ts        # Detection class → colour mapping
│   ├── public/
│   │   └── demo/                     # Demo sonar sample tiles (bundled)
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── edge/
│   └── inference/
│       ├── edge_detector.py          # Standalone edge inference script (ONNX/TorchScript)
│       └── benchmark.py              # CPU/GPU latency benchmarking
│
├── tests/
│   ├── backend/
│   │   ├── test_sonar_parser.py
│   │   ├── test_preprocessing.py
│   │   ├── test_detector.py
│   │   ├── test_georeferencing.py
│   │   ├── test_api_surveys.py
│   │   ├── test_api_detections.py
│   │   └── conftest.py
│   └── frontend/                     # Vitest unit tests
│       └── components/
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURAL_BLUEPRINT.md
│   ├── DB_SCHEMA.md
│   ├── API_SPEC.md
│   ├── UI_UX_SPEC.md
│   └── DEVELOPMENT_GUIDELINES.md
│
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 2. Coding Standards

### 2.1 Python (Backend)

- **Style:** PEP 8, enforced by `ruff` (formatter + linter).
- **Type hints:** All function signatures must have full type annotations (Python 3.11 style, e.g., `list[str]` not `List[str]`).
- **Naming:**
  - Variables and functions: `snake_case`
  - Classes: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: prefix with single underscore `_method_name`
- **Docstrings:** All public functions and classes must have a one-line docstring minimum. Use Google-style docstrings for complex functions.
- **Error handling:** Never catch bare `Exception` in production code. Catch specific exceptions and log with `structlog`. Use custom exception classes in `backend/exceptions.py`.
- **Async:** All FastAPI route handlers and database calls must be `async`. No sync blocking calls in async contexts.
- **No magic numbers:** All numeric constants (confidence thresholds, tile sizes, etc.) must reference config values, not be hardcoded inline.

```python
# CORRECT
async def get_survey(survey_id: uuid.UUID, session: AsyncSession) -> Survey:
    """Fetch a single survey by ID, raising NotFoundError if absent."""
    result = await session.get(Survey, survey_id)
    if result is None:
        raise SurveyNotFoundError(survey_id)
    return result

# WRONG — bare exception, no types, sync
def get_survey(survey_id):
    try:
        return session.query(Survey).get(survey_id)
    except:
        return None
```

---

### 2.2 TypeScript (Frontend)

- **Style:** ESLint + Prettier (`.eslintrc.cjs` + `.prettierrc` in `frontend/`).
- **Naming:**
  - Variables, functions: `camelCase`
  - React components, types, interfaces: `PascalCase`
  - Constants: `UPPER_SNAKE_CASE`
  - CSS class names (Tailwind): utility classes inline; no custom class names unless in `globals.css`.
- **Types:** No `any`. Use `unknown` + type narrowing if the type cannot be determined. All API response shapes must be typed in `src/types/index.ts`.
- **Components:** Functional components only. No class components.
- **Props:** All component props must have a typed interface: `interface DetectionCardProps { ... }`.
- **State:** Local state with `useState`; cross-page state via Zustand store. No prop drilling deeper than 2 levels — use the store.
- **Effects:** Every `useEffect` must have a complete dependency array. No side-effectful logic outside of hooks or event handlers.

```typescript
// CORRECT
interface DetectionCardProps {
  detection: Detection;
  onSelect: (id: string) => void;
}

const DetectionCard: React.FC<DetectionCardProps> = ({ detection, onSelect }) => {
  return (
    <div
      className="p-3 rounded-lg bg-surface border border-border cursor-pointer hover:border-accent"
      onClick={() => onSelect(detection.detection_id)}
    >
      <ClassBadge className={detection.class_name} />
      <ConfidenceBadge value={detection.confidence_calibrated} />
    </div>
  );
};

// WRONG — no types, class component, inline style
class DetectionCard extends React.Component {
  render() {
    return <div style={{ padding: 12 }}>{this.props.detection.class}</div>;
  }
}
```

---

### 2.3 Git Conventions

- **Branch naming:** `feat/<short-description>`, `fix/<issue>`, `chore/<task>`, `docs/<doc-name>`
- **Commit messages:** Conventional Commits format:
  ```
  feat(detector): add confidence calibration with temperature scaling
  fix(api): handle missing nav metadata in survey upload
  docs: update API_SPEC with /reports/generate endpoint
  ```
- **PRs:** All PRs require at least one review before merging to `main`.
- **`main` branch:** Always deployable. Feature branches only.
- **Model weights:** Never commit `.pt` files to git. Use `.gitignore` + DVC or manual management under `models/`.

---

## 3. Testing Strategy

### 3.1 Backend (pytest + pytest-asyncio)

| Test Type | Framework | Location | Minimum Coverage |
|---|---|---|---|
| Unit | pytest | `tests/backend/` | 80% per module |
| Integration (API) | pytest + httpx | `tests/backend/test_api_*.py` | All endpoints |
| Pipeline | pytest | `tests/backend/test_preprocessing.py` etc. | Core transforms |
| Fixtures | conftest.py | `tests/backend/conftest.py` | Shared DB, mock files |

**Run tests:**
```bash
cd backend
pytest tests/ -v --cov=backend --cov-report=term-missing
```

**Key fixture patterns:**
```python
@pytest.fixture
async def test_survey(async_session) -> Survey:
    """Insert a minimal survey record for tests."""
    survey = Survey(source_filename="test.xtf", ...)
    async_session.add(survey)
    await async_session.commit()
    return survey

@pytest.fixture
def sample_sonar_tile() -> np.ndarray:
    """Return a 640×640 float32 zero-padded sonar tile for preprocessing tests."""
    return np.zeros((640, 640), dtype=np.float32)
```

**What to test per module:**

- `sonar_parser`: Valid XTF parses to correct ping count and nav data. Corrupt file raises `SonarParseError` gracefully.
- `preprocessing`: Bottom detection returns a valid row index within bounds. CLAHE output is in [0, 1] range. Tile count matches expected overlap formula.
- `detector`: Model loads without error. Input tensor shape is correct. Output contains expected keys (boxes, scores, classes).
- `georeferencing`: Known pixel-to-latlon conversion against a synthetic test case with known nav metadata. Absent nav metadata returns `geotagging_available=False`.
- `api/surveys`: POST /upload returns 201 and a job_id. POST with oversized file returns 413. GET /surveys returns list. GET /surveys/{bad_id} returns 404.

---

### 3.2 Frontend (Vitest + React Testing Library)

```bash
cd frontend
npm run test
```

- Test every UI component's state variations: idle, loading, empty, error, success.
- Test that `DetectionCard` renders correct class badge colour and confidence value.
- Test `FilterBar` updates applied filter state correctly.
- Do not test Leaflet map internals — mock the map component.
- Do not test network calls directly — mock API hooks with msw (Mock Service Worker).

---

## 4. Step-by-Step AI Prompting Sequence

Use this sequence when prompting an AI coding assistant to build the project. Each step must be completed and verified before moving to the next. Always provide the relevant spec files as context for each step.

---

### Step 0 — Project Scaffold
**Context files:** `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Create the full directory scaffold for MarineDebris-Sonar-AI exactly as defined in DEVELOPMENT_GUIDELINES.md section 1. Create placeholder `__init__.py` files in all Python packages, `index.ts` barrel files in all frontend directories, and a `docker-compose.yml` with services: `postgres`, `redis`, `backend` (FastAPI+Uvicorn), `worker` (Celery), `frontend` (Vite dev), `nginx`. Include `.env.example` with all variables from `ARCHITECTURAL_BLUEPRINT.md` section 8.

---

### Step 1 — Database Layer
**Context files:** `DB_SCHEMA.md`, `ARCHITECTURAL_BLUEPRINT.md`  
**Prompt:**
> Implement `backend/database/models.py` with SQLAlchemy 2.0 async ORM models for all 6 tables defined in `DB_SCHEMA.md`: `surveys`, `sonar_metadata`, `processing_jobs`, `detections`, `reports`, `model_registry`. Include all columns, constraints, and indexes. Then implement `backend/database/session.py` with an async engine and session factory. Then generate the first Alembic migration with `alembic revision --autogenerate -m "initial_schema"`. Verify the migration matches the schema exactly.

---

### Step 2 — Configuration & App Factory
**Context files:** `ARCHITECTURAL_BLUEPRINT.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/config.py` using Pydantic Settings v2 to read all environment variables from `.env.example`. Implement `backend/api/main.py` as a FastAPI app factory that: registers all routers with the `/api/v1` prefix, adds CORS middleware (reads `API_CORS_ORIGINS` from config), adds a request-ID middleware, and mounts a static files route for `/api/v1/tiles/{survey_id}`. Implement `backend/api/dependencies.py` with an `async_session` dependency.

---

### Step 3 — File Upload & Ingestion API
**Context files:** `API_SPEC.md`, `DB_SCHEMA.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/api/routers/surveys.py` with these endpoints from `API_SPEC.md`: `POST /upload`, `GET /` (list surveys), `GET /{survey_id}`, `DELETE /{survey_id}`. The upload endpoint must: validate MIME type and file extension, reject files over `MAX_UPLOAD_SIZE_MB`, save the file to storage using `backend/storage/storage.py`, create a `Survey` database record, enqueue a Celery task (stub for now), and return HTTP 201 with the response schema from API_SPEC.md. Implement `backend/storage/storage.py` with `save_file()` and `get_file_path()` for local storage.

---

### Step 4 — Sonar Parser
**Context files:** `ARCHITECTURAL_BLUEPRINT.md`, `PRD.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/sonar_parser/models.py` with the chunked `SonarFrame`, `SonarPing` (including optional `pitch`/`roll`/`is_dropout`), and `SonarMetadata` dataclasses from `ARCHITECTURAL_BLUEPRINT.md` section 5. Implement `backend/sonar_parser/xtf_parser.py` using the `pyxtf` library as a generator that yields `SonarFrame` chunks (configurable ping-window size) rather than loading the whole file into one array — this is the MVP, fully-supported format (`PRD.md` §4.1). Implement `backend/ingestion/image_loader.py` for PNG sonar strips (also MVP). Implement `backend/ingestion/ingestor.py` that routes `.xtf` → `xtf_parser`, `.png` → `image_loader`, and `.jsf`/`.tif`/`.tiff` → a stub that raises a clear "format not yet supported" error (V1/deferred, not silently ignored). Write unit tests in `tests/backend/test_sonar_parser.py` that: parse a minimal synthetic multi-chunk XTF fixture, assert ping count and chunk boundaries are correct, assert nav metadata is extracted, assert a missing nav raises a handled warning (not an exception), and assert the deferred-format stub raises the expected error rather than returning empty data.

---

### Step 5 — Preprocessing Pipeline
**Context files:** `ARCHITECTURAL_BLUEPRINT.md`, `PRD.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/preprocessing/quality.py` (Sonar Quality / Motion Robustness Layer, PS26057 heave/pitch/roll/dropout requirement): per-chunk `dropout_pct` (fraction of pings with missing/invalid ping data), a `motion_quality_score` (0-1) that degrades when `pitch`/`roll` are present and exceed a configurable threshold or when nav data is missing/discontinuous between consecutive pings, and per-ping `is_dropout` flagging. This module does not attempt full physical heave/pitch/roll compensation — it flags and scores, consistent with `ARCHITECTURAL_BLUEPRINT.md` §4 and `PRD.md` §7. Implement the remaining modules in `backend/preprocessing/`: `bottom_detection.py` (return row index of seabed bottom line using threshold/gradient method), `normalization.py` (min-max normalize to float32 [0,1]), `clahe.py` (wrap OpenCV CLAHE, clip_limit configurable), `denoising.py` (median filter + optional bilateral filter for speckle), `water_column.py` (zero out columns above bottom line), `slant_range.py` (slant-range correction using range_resolution_m and altitude where available), `tiler.py` (slice a `SonarFrame` chunk's image array into 640×640 tiles with configurable overlap, return list of tiles + their pixel offsets, recording chunk_index/ping_offset for later georeferencing). Implement `pipeline.py` to chain quality-scoring → preprocessing steps → tiling per chunk, and save the processed image to storage. Write unit tests for each module using the `sample_sonar_tile` fixture, plus a `quality.py` test asserting a synthetic dropout ping is correctly flagged.

---

### Step 6 — Celery Task Orchestration & Job Status API
**Context files:** `ARCHITECTURAL_BLUEPRINT.md` (§2 event flow clarification), `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/celery_app.py` (Celery instance configured with Redis as broker/result backend). Implement `backend/tasks.py` with a `process_survey` Celery task that calls each pipeline step in sequence, per chunk: ingest (chunked) → quality-score → preprocess → tile → detect (stub) → postprocess (stub) → geotag (stub) → report (stub). The task must update `processing_jobs.progress_pct` and `current_stage` in the database at each step (durable source of truth) **and** publish a progress event to a Redis pub/sub channel keyed by `job_id`. Implement `backend/api/routers/ws.py` with the WebSocket endpoint `WS /api/v1/ws/jobs/{job_id}` from `API_SPEC.md` — this endpoint subscribes to the Redis channel and relays events to the connected client; it does not receive events directly from the Celery worker process. Implement `backend/api/routers/jobs.py` with `GET /api/v1/jobs/{job_id}` as a polling fallback for clients that miss WS frames.

---

### Step 7 — Detection Inference
**Context files:** `ARCHITECTURAL_BLUEPRINT.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/inference/model_loader.py` as a singleton that loads the YOLOv8 model once at Celery worker startup using the `DETECTION_MODEL_PATH` env variable. Implement `backend/inference/detector.py` with a `detect_tiles(tiles: list[np.ndarray]) -> list[list[DetectionResult]]` function that runs batched YOLOv8 inference and returns raw detections per tile. Implement `backend/postprocessing/nms.py` to merge tile detections into survey image space coordinates and apply global NMS. Implement `backend/postprocessing/calibration.py` with temperature scaling. Integrate these into the Celery task from Step 6.

---

### Step 8 — Georeferencing Engine
**Context files:** `ARCHITECTURAL_BLUEPRINT.md` (§7 Basic vs. Advanced Georeferencing), `DB_SCHEMA.md`, `PRD.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `backend/georeferencing/geotagger.py` with a `geotag_detections(detections, sonar_frame)` function implementing **Basic georeferencing** (MVP tier, `ARCHITECTURAL_BLUEPRINT.md` §7). For each detection bbox, identify which ping row it falls on using `tiler.py`'s chunk/pixel offset mapping. Use the ping's lat/lon, heading, altitude (where available), and range_resolution_m to compute the target lat/lon via WGS84 bearing/distance. If navigation metadata is absent for that ping, set `geotagging_available=False` and leave `latitude`/`longitude` null — never interpolate or fabricate a coordinate. Implement `backend/georeferencing/dimension_estimator.py` to compute estimated object length and width in metres from bbox pixel dimensions and range resolution. Write a unit test with a synthetic `SonarPing` at a known lat/lon and known heading/range and verify the computed target location matches the expected geometric result within a small numerical tolerance (this validates the projection math against a synthetic ground truth — it is not a claim about real-survey accuracy, which is only evaluated where real ground truth exists, per `PRD.md` §6). Advanced georeferencing (attitude-corrected, V2) is out of scope for this step.

---

### Step 9 — Reporting & Detections API
**Context files:** `API_SPEC.md`, `DB_SCHEMA.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement all three report generators in `backend/reporting/`: `json_reporter.py` (serialize DetectionResult list to the JSON schema in `API_SPEC.md` section 11), `csv_reporter.py` (one row per detection, all fields from the schema), `geojson_reporter.py` (FeatureCollection with Point geometry per detection, properties including all detection fields). Implement `backend/api/routers/detections.py` with `GET /api/v1/surveys/{survey_id}/detections` and `GET /api/v1/detections/{detection_id}`. Implement `backend/api/routers/reports.py` with `GET /api/v1/surveys/{survey_id}/reports`, `POST /api/v1/surveys/{survey_id}/reports/generate`, and `GET /api/v1/reports/{report_id}/download`.

---

### Step 10 — Frontend Scaffold & Upload Page
**Context files:** `UI_UX_SPEC.md`, `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Scaffold the React frontend using Vite + React 18 + TypeScript. Install: tailwindcss, shadcn/ui, react-router-dom v6, zustand, @tanstack/react-query, axios, react-dropzone, leaflet, react-leaflet. Configure Tailwind with the design tokens from `UI_UX_SPEC.md` section 2 as CSS variables in `globals.css`. Implement `AppLayout`, `Sidebar`, and `Navbar` from the component inventory. Implement the Upload page (`/upload`) with `FileUploader` component exactly matching the layout in `UI_UX_SPEC.md` section 4.1. Connect the upload form to `POST /api/v1/surveys/upload`. Implement all 5 FileUploader states.

---

### Step 11 — Sonar Viewer & Detection Overlay
**Context files:** `UI_UX_SPEC.md`, `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `SonarViewer` as an HTML5 Canvas component with pan (click-drag) and zoom (scroll wheel) controls. The canvas renders the sonar image PNG fetched from `GET /api/v1/surveys/{survey_id}/sonar-image`. Implement `DetectionOverlay` as an SVG layer absolutely positioned over the canvas, drawing bounding boxes coloured by class (using `classColors.ts` which maps class names to the colour tokens in `UI_UX_SPEC.md` section 2.1), with confidence label badges. Implement `SonarToggle` to switch between raw and processed image modes. Implement `useJobProgress` hook using the WebSocket endpoint. Implement the `JobStatusBar` with all 4 states.

---

### Step 12 — Detection Panel & Map
**Context files:** `UI_UX_SPEC.md`, `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `DetectionPanel` with `FilterBar` (class dropdown, confidence slider, show-filtered toggle) and a scrollable list of `DetectionCard` components, fetched from `GET /api/v1/surveys/{survey_id}/detections`. Implement `ClassBadge` and `ConfidenceBadge` components. Implement `DetectionDetail` modal with tile image, all metadata fields, and the layout from `UI_UX_SPEC.md` section 4.3. Implement `DetectionMap` using react-leaflet with coloured `MapPin` components per detection class. Clicking a pin opens `DetectionDetail`. Show the survey bounding box as a rectangle on the map. Handle the no-nav-data state with a banner.

---

### Step 13 — Survey List, Report Downloader & Models Page
**Context files:** `UI_UX_SPEC.md`, `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`  
**Prompt:**
> Implement `SurveyListPage` (`/surveys`) showing a table of surveys with status badges, detection counts, and [View] links. Implement `ReportDownloader` component with three buttons (JSON / CSV / GeoJSON) that call `POST /api/v1/surveys/{survey_id}/reports/generate` and then trigger a download via `GET /api/v1/reports/{report_id}/download`. Implement `ModelsPage` (`/models`) showing the active model card with metrics and the per-class `MetricsPanel` table. Implement `DemoModeBanner` and wire up Demo Mode using `GET /api/v1/demo/surveys` to pre-select a demo survey.

---

### Step 14 — Integration, Edge Model & Polish
**Context files:** All spec files  
**Prompt:**
> Complete integration end-to-end: upload a sample XTF → pipeline runs → detections appear on sonar viewer and map → GeoJSON downloads correctly. Implement `edge/inference/edge_detector.py` that exports the active YOLOv8 model to ONNX and runs inference on a tile using onnxruntime. Implement `edge/inference/benchmark.py` to measure per-tile latency on CPU and GPU. Add `GET /api/v1/health` endpoint from `API_SPEC.md`. Add `DemoModeBanner` + pre-loaded demo data so the system works without a real sonar file upload. Write the full `README.md` with setup instructions, dataset download steps, and reproduction instructions for training.

---

## 5. Environment Setup for Developers

```bash
# Clone and enter the project
git clone https://github.com/your-org/MarineDebris-Sonar-AI.git
cd MarineDebris-Sonar-AI

# Copy env file and fill in values
cp .env.example .env

# Start all services
docker-compose up --build

# Backend available at: http://localhost:8000
# Frontend dev server:  http://localhost:5173
# FastAPI docs:         http://localhost:8000/docs
# MinIO console:        http://localhost:9001

# Run backend tests
docker-compose exec backend pytest tests/ -v

# Run frontend tests
docker-compose exec frontend npm run test
```

---

## 6. Definition of Done — Per Feature

A feature is considered done when:
- [ ] The implementation matches the spec in the relevant `.md` file.
- [ ] All relevant unit tests pass with no errors.
- [ ] API endpoints return the exact response schema from `API_SPEC.md`.
- [ ] No `any` types in TypeScript; no untyped Python function signatures.
- [ ] `ruff` (Python) and ESLint (TypeScript) report zero errors.
- [ ] The feature was manually tested end-to-end in the running Docker environment.
- [ ] A PR has been reviewed and approved by at least one other developer.

---

## 7. Specification Governance Rules (post-freeze)

These rules apply to every implementation step above, and to any AI coding assistant or developer working from these six files:

- **Do not silently change architecture.** If an implementation detail in `ARCHITECTURAL_BLUEPRINT.md` turns out to be wrong or impractical, stop and raise it as a spec-change request rather than deviating in code while the docs stay stale.
- **Do not invent unspecified APIs.** Every endpoint implemented must already exist in `API_SPEC.md`. If a needed endpoint is missing, that is a spec gap — raise it, don't silently add one.
- **Do not invent database fields.** Every column implemented must already exist in `DB_SCHEMA.md`. Schema drift between code and docs is exactly the failure mode this audit closed.
- **Do not invent model metrics.** Never write a real number (mAP, latency, accuracy) into code, logs, or docs as if it were a validated result unless it came from an actual evaluation run. Placeholder/example values must stay clearly marked as such, as they are throughout these six files.
- **Do not claim a feature is complete without tests.** "Implemented" in the Definition of Done (§6) requires passing tests, not just code that compiles.
- **Do not change specifications without documenting the reason.** If a spec file must change post-freeze, the change and its rationale are recorded (commit message or a changelog note in the relevant file), not made silently.
- **If two specifications conflict, STOP and resolve the conflict before implementation continues.** This audit's job was to eliminate the conflicts that existed as of the freeze below; if a new one is discovered during implementation, it is resolved by explicit decision (not by an implementation agent picking one side arbitrarily) before the affected code is written.

---

# SPECIFICATION STATUS

**STATUS: FROZEN — IMPLEMENTATION READY**

**Version:** `1.0.0`

**Competition:** `SIH 2026 — PS26057`

**Specification files:**

* PRD.md
* ARCHITECTURAL_BLUEPRINT.md
* DB_SCHEMA.md
* API_SPEC.md
* UI_UX_SPEC.md
* DEVELOPMENT_GUIDELINES.md

These six documents constitute the authoritative project specification for implementation.

After freeze, implementation agents must not modify architecture, APIs, database schema, taxonomy, or core requirements without an explicit specification-change request.

---

*End of DEVELOPMENT_GUIDELINES.md*
