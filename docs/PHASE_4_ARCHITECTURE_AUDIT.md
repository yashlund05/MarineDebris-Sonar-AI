# Phase 4 architecture audit — Acoustic intelligence workstation

**Audit date:** 2026-09-11  
**Scope:** current repository state before Phase 4 implementation. This is an architectural and safety audit, not a claim that every existing screen or report has been independently reproduced.

## Executive assessment

MarineDebris-Sonar-AI is a substantial FLS-first sonar-analysis application with a working React/Vite client, FastAPI service layer, asynchronous survey processing, a frozen YOLOv8 production detector, dataset provenance/evaluation controls, enhancement workflows, and model-governance endpoints. It is not yet a deployment-ready live-acoustic platform. In particular, it has no physical/external live source adapter, no live-frame WebSocket contract, no production segmentation implementation, and no cloud object-storage implementation.

Phase 4 must therefore turn the product into a truthful **3D Interactive Acoustic Intelligence Workstation**. A 3D scene may visualise available mission state and provenance, but it must never invent bathymetry, detections, metrics, locations, feed status, or operational telemetry.

## Repository map

| Area | Current responsibility | Audit finding |
| --- | --- | --- |
| `frontend/` | React 18, TypeScript, Vite, Tailwind, React Query, Zustand | Functional analysis UI; Leaflet/map and Recharts available. Three.js/R3F/drei and a motion library are not currently dependencies. |
| `backend/api/` | FastAPI factory, REST routers, job-progress WebSocket | Broad REST surface with consistent request IDs/error envelopes. WebSocket support is limited to Redis-backed job progress. |
| `backend/services/`, `backend/tasks/` | Survey pipeline, Celery work, reporting, evaluation | Good async foundation; needs an explicit live-ingestion boundary and durable event contract. |
| `backend/inference/`, `backend/ml/` | Detector/loading, registry, training/evaluation | Production detection is real. Segmentation route/interface is placeholder-only and must be labelled unavailable until implemented. |
| `backend/enhancement/` and `backend/services/sonar_enhancement/` | Enhancement providers and sonar-enhancement pipeline | Valuable capability, but two adjacent enhancement stacks need consolidation or a documented ownership boundary. |
| `datasets/`, `data/`, `reports/`, `models/` | datasets, frozen benchmark evidence, checkpoints and experiments | Safety-critical scientific assets; no Phase 4 UI work may mutate these. |
| `simulator/`, `edge/` | future integration surfaces | No production `DataSourceManager` or real live-source adapter was found. |
| `docker/`, `docker-compose.yml` | local container deployment | PostgreSQL/PostGIS, Redis, API, worker and frontend are defined; backend container still starts Uvicorn with `--reload`. |

## Existing product paths and real capabilities

### Frontend

The app routes users through command/overview, upload, survey list/detail, sonar viewer, detection review, map, enhancement workbench, models, datasets and reports. Its existing upload and survey flows are the correct foundation for Phase 4. The current command-centre experiment and canvas terrain are design exploration only; they are not evidence-backed terrain and must not be presented as operational data.

The app already uses server state through React Query and local UI state through Zustand. It contains a job-progress hook/client that connects to `/api/v1/ws/jobs/{job_id}`. It does not contain a live frame subscription client, 3D scene state store, WebGL fallback, or a source-mode model.

### Backend and API

`backend/api/main.py` mounts these versioned surfaces:

- datasets and canonical-status/manifest endpoints;
- survey upload, listing, details, deletion, reprocess, reanalyse and sonar-image retrieval;
- detections, per-survey detections, detail, segmentation and classification;
- jobs plus `/ws/jobs/{job_id}` progress events;
- reports, model registry/governance, inference and system health;
- general enhancement and sonar-enhancement endpoints.

`POST /api/v1/inference/predict` performs real single-image YOLO inference and returns detections, thresholds, timing, checkpoint path/hash and source-image provenance. This is the appropriate initial integration point for uploaded single FLS frames. It is not a persistent stream processor.

The job WebSocket is a Redis Pub/Sub relay for processing status only. There is no endpoint for `frame`, `detection`, `telemetry`, `source_status`, backpressure or reconnect semantics. Consequently, Phase 4 must use **file/API mode** as the default operational mode and must render live mode unavailable until an audited source adapter and live contract exist.

### ML, evaluation and model registry

The canonical evaluation contract fixes 640-pixel input, benchmark confidence `0.001`, benchmark IoU `0.70`, operational confidence `0.25`, operational IoU `0.45`, a five-class taxonomy, and expected held-out-data counts. The contract names the production checkpoint SHA-256 below.

The immutable production checkpoint is:

`models/detection/sonar_yolov8_fls_trained.pt`  
`e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`

The inference router independently points at this checkpoint and computes the returned hash at inference time. Model registry routes provide model detail, health, metrics, runs, artifacts, promotion, traceability, error analysis, comparison and promotion-audit views.

Important limitation: `backend/inference/segmenter.py` writes a dummy RLE mask when a model is supplied and identifies itself as a placeholder. Phase 4 must not draw segmentation overlays or market segmentation as an available capability until this is replaced with a real model and evaluated endpoint.

### Enhancement, ingestion and storage

Enhancement is a genuine feature area: the API exposes profiles, palettes, methods, sample images, processing, comparison and enhanced detection; `/api/v1/sonar/*` separately exposes enhancement/upload, recolour and download operations. The split surface risks duplicated domain logic and divergent output/provenance semantics.

PNG/JPEG/TIFF decoding is currently handled for inference. JSF parsing and one ingestion format path are explicitly deferred, so the UI must treat JSF as unsupported/not configured rather than accepting it optimistically. MinIO is named in configuration but deliberately raises `NotImplementedError`; local storage is the only implemented backend.

## Dataset, benchmark and provenance controls

The repository dataset card identifies a real forward-looking-sonar V3 corpus: 660 images, 899 boxes, 84 negative frames and 36 sequences, with a sequence-aware 480/100/80 train/validation/test split. It records V2 as 238 images and 371 annotations, and V3 held-out test expectations as 80 images and 127 annotations. Class distribution is materially imbalanced; the UI must not imply broad equal-class performance.

The audit treats all frozen manifests, held-out data, benchmark reports, provenance records and experiment results as scientific records. They are display-only inputs to Phase 4.

## Test inventory

Backend tests cover configuration, Celery, health, database, survey/detection/model/dataset APIs, end-to-end pipeline, inference, preprocessing/postprocessing, georeferencing, sonar enhancement, side-scan tools, evaluation integrity, data expansion, model optimization, traceability, promotion and error analysis. The frontend package has build/lint scripts but no frontend unit or browser test suite was found in its package scripts.

The frontend build was run successfully before this audit; the bundle warning above 500 kB is a Phase 4 performance concern and must be remeasured after adding 3D dependencies.

## Deployment-readiness gaps

1. **Truthful live mode:** no `DataSourceManager`, adapter registry, source health endpoint, live-frame transport, event schema, or reconnect/backpressure policy.
2. **Production security:** no verified authentication, role model, tenant isolation, rate limit, audit trail for user actions, secret-management policy, or upload malware/content scanning in the audited paths.
3. **Storage:** MinIO/S3-compatible storage is declared but not implemented; local filesystem is not a resilient production object-store strategy.
4. **Runtime:** Compose starts the API with `--reload`; readiness/liveness distinction, migration strategy, resource limits, image scanning and production observability need hardening.
5. **ML transparency:** segmentation is a placeholder; modality/documentation use both FLS and side-scan language, so source modality must appear with every result.
6. **3D truthfulness/performance:** an exploratory canvas visual exists but is not connected to authoritative mission data. Production 3D must use R3F, a WebGL fallback, reduced-motion support, adaptive DPR and a mobile simplified mode.
7. **Frontend quality:** no frontend automated test suite, and the current build has a large entry chunk. New 3D code must be lazy-loaded and verified on mobile.
8. **Enhancement governance:** enhancement result provenance, reversible comparisons and detector-on-enhanced-image behaviour must be explicit; duplicate enhancement service layers need a single contract.

## Files and assets that must not be modified

- `models/detection/sonar_yolov8_fls_trained.pt` and its SHA-256 contract;
- frozen held-out V2/V3 evaluation data, split manifests, provenance JSONL and benchmark manifests;
- published reports and Phase 3 experiment artifacts/results;
- canonical evaluation constants unless a separately approved scientific evaluation revision is created;
- original source files and datasets solely to make a demo look more impressive.

## Safe extension areas

- new frontend feature folders for `mission`, `scene`, `evidence`, `source`, `accessibility` and their tests;
- a lazy-loaded R3F scene wired only to a typed mission-state model, with an honest static fallback;
- a new backend `sources`/`live` router, typed source adapters, WebSocket/SSE event schema, source health and capability endpoints;
- database migrations for source configuration, mission sessions and immutable event provenance;
- audit-safe UI telemetry derived from API responses and job events;
- integration, contract, accessibility and browser tests; deployment documentation and environment validation.

## Phase 4 implementation gate and sequence

1. Establish the design system and an evidence-first mission-state contract. Replace hard-coded operational labels with available/unavailable states.
2. Add `three`, `@react-three/fiber` and `@react-three/drei` only after dependency/security review. Build a lazy-loaded R3F bathymetry/mission scene with mobile/reduced-motion/WebGL fallbacks.
3. Keep the 2D sonar raster and its metadata central. Route actual uploaded-frame inference responses to the evidence pane and mission timeline.
4. Define sources as `FILE_UPLOAD`, `EXTERNAL_API` and `PHYSICAL_SENSOR`; implement adapters and only enable a source when health/capabilities prove it available. No simulated operational feed.
5. Reconcile enhancement ownership and surface provenance alongside every transformed image.
6. Add frontend test coverage, API contracts for source events, security/deployment controls and performance budgets before calling the platform production-ready.

## Research and licensing gate

Any external research, datasets, checkpoints, visual assets or implementation references proposed for Phase 4 must be recorded with repository/paper URL, license, attribution requirement, compatibility with the current data/model licenses, and whether it is code, model, data or visual inspiration. No external model or dataset may be connected silently to the production route.

### Initial research register (not integrated)

| Candidate | Relevant value | License / compatibility position | Decision |
| --- | --- | --- | --- |
| [SEGSID](https://github.com/deng-ai-lab/SEGSID) | Semantic-guided sonar-image despeckling research with published checkpoints for multiple sonar datasets. | Repository declares MIT; the supplied checkpoints and their training data require separate provenance/licence verification. | Research reference only. Do not place in the inference or enhancement production path without a reproducible evaluation and an enhancement-provenance contract. |
| [SidescanTools](https://github.com/sonoware/sidescantools) | Side-scan processing, gain normalisation, slant-range correction and GeoTIFF/waterfall export; relevant to the deferred XTF/JSF branch. | Licence must be confirmed from the project's licence file before vendoring or linking. It is an SSS-oriented tool and therefore cannot be represented as an FLS enhancement model. | Candidate adapter/reference for a separately scoped SSS workflow, not a dependency of the current FLS detector. |
| [AI4Shipwrecks](https://umfieldrobotics.github.io/ai4shipwrecks/) | A peer-reviewed SSS shipwreck segmentation benchmark that makes the modality gap visible. | Dataset terms and attribution must be taken from the official download before any acquisition; its class/task does not match the frozen FLS detector. | Benchmark research only; no silent dataset merge, transfer-performance claim or segmentation feature. |
