# Contributors

Welcome to the **MarineDebris-Sonar-AI** contributor registry.

MarineDebris-Sonar-AI is an open-source, specification-driven platform dedicated to automated acoustic anomaly detection, Forward-Looking Sonar (FLS) imagery analysis, side-scan sonar ingestion, and underwater marine debris classification.

---

## About Contributions

This document provides a human-maintained, professional record of the meaningful architectural, engineering, research, and design work contributed to the repository.

In alignment with the project's engineering standards:
- **Substantive attribution:** Highlights functional implementations, architectural milestones, verified dataset integrations, user interface engineering, test harnesses, and technical research rather than raw commit counts.
- **Evidence-based records:** All contributor summaries are cross-referenced with repository commits, pull requests, and verified file artifacts.
- **Anti-fabrication & clarity:** Clearly demarcates completed implementations from modular interfaces, candidate models, and future roadmap items.

---

## Contributors

### Yash Lund

**GitHub / Contact:** [@yashlund05](https://github.com/yashlund05)  
**Role:** Project Creator & Founding Systems Architect

#### Architecture & Specification
- Authored and froze the foundational v1.0.0 technical specifications for the Smart India Hackathon (SIH 2026, Problem Statement PS26057):
  - Product Requirements Document (`PRD.md`) defining system scope, user personas, canonical 5-class debris taxonomy, and PS26057 compliance matrix.
  - Architectural Blueprint (`ARCHITECTURAL_BLUEPRINT.md`) establishing the modular monolith system topology, streaming data contracts, and Celery/Redis event flows.
  - Database Schema Specification (`DB_SCHEMA.md`) detailing the 6 core ORM entities, spatial postGIS geometries, cascade deletion rules, and indexing strategies.
  - REST & WebSocket API Specification (`API_SPEC.md`) defining endpoints for ingestion, survey management, detections, reporting, and job monitoring.
  - UI/UX Design System Specification (`UI_UX_SPEC.md`) defining acoustic canvas viewport specifications, color token palettes, and GIS mapping guidelines.
  - Development Guidelines (`DEVELOPMENT_GUIDELINES.md`) formalizing anti-fabrication rules, acceptance standards, and phased engineering milestones.

#### Backend
- Scaffolded the initial FastAPI application structure (`backend/api/main.py`, `backend/api/dependencies.py`, `backend/api/routers/system.py`).
- Configured application settings using Pydantic Settings v2 (`backend/config.py`), logging formatters (`backend/logging_config.py`), and error hierarchy (`backend/exceptions.py`).
- Initialized database connection sessions and base SQLAlchemy 2.0 ORM models for surveys, sonar metadata, processing jobs, detections, and audit reports (`backend/database/models.py`, `backend/database/session.py`).
- Set up Alembic database migration environment and initial schema migration (`alembic.ini`, `backend/database/migrations/versions/0001_initial_schema.py`).
- Established Celery worker baseline configuration (`backend/celery_app.py`, `backend/tasks.py`).

#### Infrastructure & DevOps
- Implemented multi-service containerization with `docker-compose.yml` (PostgreSQL/PostGIS, Redis, FastAPI backend, Vite frontend, and Nginx reverse proxy).
- Authored `docker/Dockerfile.backend`, `docker/Dockerfile.frontend`, and `docker/nginx.conf`.
- Set up initial testing infrastructure and shared Pytest fixtures (`pytest.ini`, `tests/backend/conftest.py`).

---

### Ayush Vishwakarma

**Git / Contact:** `officialayush5839@gmail.com`  
**Role:** Lead Systems Engineer & ML/Full-Stack Architect

#### Machine Learning
- Integrated the genuine Forward-Looking Sonar (FLS) acoustic dataset from the ARIS Explorer 3000 (3.0 MHz) benchmark (University of Groningen / Heriot-Watt University, DOI `10.5281/zenodo.15101686`).
- Implemented primary 2D detector pipeline using YOLOv8m (`backend/ml/detector/yolo_detector.py`, `backend/inference/detector.py`), verified with active repository trained weights (`models/detection/sonar_yolov8_fls_trained.pt`, `models/detection/sonar_yolov8m_ghostpot_v1.pt`).
- Architected the modular ML service framework in `backend/ml/`:
  - Base detector, segmenter, and classifier abstractions with runtime verification and graceful unavailable-state handling.
  - Semantic segmentation boundary extraction interfaces for U-Net and SegFormer (`backend/ml/segmentation/unet.py`, `backend/ml/segmentation/segformer.py`).
  - Secondary candidate crop verification classifier interfaces for MobileNet and ResNet (`backend/ml/classifier/mobilenet.py`, `backend/ml/classifier/resnet.py`).
  - Decision fusion engine (`backend/ml/fusion/inference_fusion.py`) assessing multi-model consensus without overriding primary detector detections.
  - Model Registry service (`backend/ml/registry/model_registry.py`) providing runtime status gating (`READY`, `MISSING_WEIGHTS`, `UNAVAILABLE`) and metadata endpoints (`GET /api/v1/models`).
  - End-to-end chained inference pipeline orchestrator (`backend/ml/pipeline/inference_pipeline.py`).
- Implemented post-processing inference algorithms: cross-tile Global NMS ($IoU = 0.45$), acoustic shadow context verification, bounding box dimension filtering, and temperature-calibrated confidence scaling.

#### Backend
- Implemented the complete 11-stage asynchronous Celery task pipeline (`backend/tasks.py`) supporting both distributed Redis execution and local standalone eager mode.
- Engineered real-time WebSocket progress bridge (`backend/api/routers/ws.py`) subscribing to Redis Pub/Sub channels (`job_progress:{job_id}`) and broadcasting granular stage updates to clients.
- Built complete REST API routers for survey management (`backend/api/routers/surveys.py`), detection queries and filtering (`backend/api/routers/detections.py`), job status polling (`backend/api/routers/jobs.py`), model registry (`backend/api/routers/models.py`), and report generation (`backend/api/routers/reports.py`).
- Developed the file storage manager (`backend/storage/storage.py`) with UUID directory isolation, MIME/extension validation, size limit checks, and cascade disk deletion.
- Authored database migration `0002_ml_segmentation_classification.py` adding segmentation mask geometry, classifier verification fields, and model registry metrics columns.
- Implemented multi-format report export generators for JSON audit summaries, 18-column CSV files, and RFC 7946 WGS84 GeoJSON FeatureCollections (`backend/reporting/`).

#### Data & Sonar Processing
- Developed the acoustic preprocessing pipeline in `backend/preprocessing/`:
  - Acoustic dropout analysis and motion quality scoring (`quality.py`).
  - Seabed bottom line detection using threshold and gradient fallbacks (`bottom_detection.py`).
  - Water-column masking and zeroing above the detected bottom line (`water_column.py`).
  - Contrast Limited Adaptive Histogram Equalization (`clahe.py`).
  - Median and bilateral speckle noise reduction filtering (`denoising.py`).
  - Dynamic min-max range normalization (`normalization.py`).
  - Geometric slant-range correction (`slant_range.py`).
  - 640×640 overlapping tile generation preserving coordinate offsets (`tiler.py`).
- Developed the streaming sonar ingestion suite:
  - Generator-based chunked XTF parser using `pyxtf` (`backend/sonar_parser/xtf_parser.py`).
  - PNG sidescan strip loader (`backend/ingestion/image_loader.py`).
  - External navigation CSV parser (`backend/ingestion/nav_csv_parser.py`).
- Built dataset format converters (`training/conversion/coco_to_yolo.py`, `training/conversion/voc_to_yolo.py`) and dataset validation tooling.
- Integrated sequence-split partitioning for the FLS benchmark dataset (238 images, 371 annotations across Train, Validation, and Test splits) with 0% cross-sequence leakage.
- Created synthetic sidescan waterfall generator and survey seeder (`simulator/generator.py`, `simulator/demo_data.py`).
- Implemented WGS84 great-circle geodesy algorithms (`backend/georeferencing/geotagger.py`) and metric physical dimension estimation (`backend/georeferencing/dimension_estimator.py`) with zero-fabrication safety rules when navigation metadata is absent.

#### Frontend / UI/UX
- Architected the complete React 18 single-page application with TypeScript, Vite, TanStack Query, and Zustand state management.
- Executed the comprehensive UI/UX redesign establishing a light-first Maritime Operations & Intelligence theme with strict WCAG 4.5:1 contrast compliance.
- Developed the high-performance Sonar Imaging Workstation (`SonarViewer.tsx`, `useSonarViewer.ts`, `SonarToggle.tsx`) featuring HTML5 Canvas pan, zoom ($25\% - 800\%$), fit-to-viewport, raw vs CLAHE enhanced toggles, and swath switching.
- Implemented SVG detection overlays (`DetectionOverlay.tsx`) supporting dynamic bounding boxes, class color coding, segmentation contours, and confidence badges.
- Created interactive Leaflet GIS mapping components (`DetectionMap.tsx`) with custom pin markers and coordinate popups, respecting zero-fabrication empty states when GPS telemetry is absent.
- Built the Target Inspection Drawer (`DetectionDetail.tsx`) showing classification agreement, segmentation status, WGS84 coordinates, and dimensional metrics.
- Developed core operational views: Ingestion Wizard (`UploadPage.tsx`, `FileUploader.tsx`), Surveys Catalog (`SurveyListPage.tsx`), Survey Detail Workspace (`SurveyDetailPage.tsx`), Model Center (`ModelsPage.tsx`), Dataset Explorer (`DatasetPage.tsx`), and Dashboard (`DashboardPage.tsx`).
- Built the live pipeline execution monitor (`JobStatusBar.tsx`) connected to WebSocket progress updates.

#### Testing & Quality
- Created end-to-end and modular Pytest test suites across API endpoints, database persistence, georeferencing math, preprocessing steps, and ML integration (`tests/backend/`), achieving 65/65 passing tests.
- Implemented dataset validation smoke tests (`tests/backend/test_dataset_validation.py`, `scripts/smoke_test_model.py`) and pipeline benchmarks (`scripts/benchmark_pipeline.py`).
- Verified zero TypeScript errors and clean Vite production build compilation.
- Engineered automated cross-platform startup tooling (`run.bat`, `scripts/wait_for_server.py`) with preflight checks and HTTP readiness verification.

#### Documentation / Research
- Authored in-depth technical documentation in `docs/`:
  - Machine Learning architecture and integration reports (`ML_ARCHITECTURE.md`, `ML_INTEGRATION_FINAL_REPORT.md`, `ML_FINAL_AUDIT.md`, `REAL_ML_PERFORMANCE.md`).
  - Dataset provenance, quality, split, and class mapping specifications (`DATASET_PROVENANCE.md`, `DATASET_QUALITY_REPORT.md`, `DATASET_SPLIT.md`, `DATASET_CLASS_MAPPING.md`).
  - Technical audit reports (`BACKEND_ACCEPTANCE_AUDIT.md`, `BACKEND_IMPLEMENTATION_STATUS.md`, `UI_UX_REDESIGN_REPORT.md`).
  - Edge optimization and ONNX export tools (`edge/export_onnx.py`, `edge/benchmark_edge.py`).

---

## Major Contribution Areas

The MarineDebris-Sonar-AI platform is built on collaborative engineering across key technical domains:

- **Sonar Ingestion & Acoustic Preprocessing:** Chunked XTF streaming, PNG strip decoding, external navigation ingestion, acoustic dropout detection, bottom tracking, water-column removal, CLAHE enhancement, median denoising, slant-range correction, and tile generation.
- **Machine Learning & Decision Fusion:** Primary YOLOv8m detection with trained weights, modular U-Net/SegFormer segmentation interfaces, candidate crop classifier interfaces, multi-model consensus fusion, global NMS, and temperature confidence calibration.
- **Georeferencing & Spatial Geodesy:** WGS84 great-circle projection, towfish position/heading tracking, physical metric dimension estimation, and zero-fabrication coordinate validation.
- **Backend & Distributed Systems:** FastAPI REST routing, Celery asynchronous task execution, Redis Pub/Sub event broadcasting, WebSocket streaming, and UUID-isolated storage management.
- **Database & Persistence:** Dual-engine persistence (PostgreSQL/PostGIS for containerized production, SQLite for standalone local execution), SQLAlchemy 2.0 ORM entities, cascade constraints, and Alembic versioned migrations.
- **Frontend Visualization & GIS:** High-resolution HTML5 Canvas sonar workstation, SVG detection/mask overlays, Leaflet geospatial mapping, target inspection drawers, and WCAG-compliant design tokens.
- **Data Engineering & Benchmarking:** FLS acoustic dataset curation, sequence-level partitioning, annotation format conversion, synthetic sonar simulation, and latency profiling.
- **Quality Assurance & Verification:** Comprehensive automated unit, integration, and E2E regression test suites with 100% pass verification.

---

## Attribution Policy

1. **Evidence-Based Attribution:** Contributions listed in this document reflect verified engineering, architecture, testing, research, and documentation work evidenced in repository commits, pull requests, and codebase artifacts.
2. **Human-Maintained Summary:** This registry summarizes substantive architectural milestones and feature implementations rather than transcribing raw commit logs or automated bot activities.
3. **Repository History as Final Authority:** Git commit history remains the definitive, unalterable record of exact diffs, commit hashes, timestamps, and line-level authorship.
4. **Scope Demarcation:** In keeping with project integrity guidelines, implemented features with active weights/artifacts are strictly distinguished from modular interfaces, candidate models, and future roadmap goals.

---

## Repository History

The complete, granular history of all repository changes—including commits, branches, author identities, timestamps, and line-by-line diffs—is maintained by Git.

To review the full chronological commit log:

```bash
git log --all --format="%h | %an | %ae | %ad | %s" --date=short
```

To review contributor statistics:

```bash
git shortlog -sne --all
```

---

## Updating This File

Future contributors should update this registry when submitting significant new features, architectural components, dataset integrations, or documentation milestones:

1. **Implement and Test:** Complete the code or documentation contribution with relevant tests.
2. **Commit Changes:** Submit the work via a standard Git commit or pull request.
3. **Record Attribution:** Add or update the contributor's entry under [## Contributors](#contributors) using the standard subsections:
   - `#### Machine Learning`
   - `#### Backend`
   - `#### Frontend / UI/UX`
   - `#### Data & Sonar Processing`
   - `#### Testing & Quality`
   - `#### Documentation / Research`
4. **Maintain Standards:** Use clear, technical, concise bullet points. Summarize functional accomplishments rather than individual commit messages, and ensure all claims are verified by repository artifacts.
