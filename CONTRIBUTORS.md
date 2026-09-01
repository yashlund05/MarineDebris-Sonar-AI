# Contributors

Welcome to the **MarineDebris-Sonar-AI** contributor registry. 

MarineDebris-Sonar-AI is an open-source, specification-driven platform dedicated to automated acoustic anomaly detection, Forward-Looking Sonar (FLS) imagery analysis, and underwater marine debris classification.

This document records the meaningful architectural, engineering, research, and design contributions made by each individual contributor to the repository.

---

## Contribution Philosophy

This registry highlights substantive, functional contributions to the platform rather than raw commit volume. Meaningful contributions include:

- **Architecture & System Design:** Authoring core blueprints, data schemas, API specifications, and workflow definitions.
- **Machine Learning & Acoustics:** Developing acoustic detectors, segmentation interfaces, candidate classifiers, model registry services, and decision fusion engines.
- **Dataset Engineering:** Curating, formatting, validating, and auditing real Forward-Looking Sonar (FLS) acoustic benchmarks.
- **Backend Infrastructure:** Implementing distributed task queues (Celery/Redis), REST API endpoints (FastAPI), database models (SQLAlchemy/PostGIS), and asynchronous WebSocket channels.
- **Frontend & UI/UX:** Designing and implementing interactive sonar imaging workstations, GIS mapping components, target inspection drawers, and design systems.
- **Testing & Quality Assurance:** Writing automated unit, integration, and end-to-end regression test suites.
- **DevOps & Developer Tooling:** Engineering automated local startup environments, Docker service definitions, and deployment scripts.
- **Technical Documentation:** Writing scientific architecture reports, integration audits, and dataset provenance manifests.

Trivial typo fixes, automated formatting changes, or routine dependency bumps are recorded in the Git history but are omitted here to keep this document concise and human-readable.

---

## Contributors

### Yash Lund

**GitHub / Contact:** [@yashlund05](https://github.com/yashlund05)  
**Role:** Project Creator & Founding Systems Architect

#### Architecture & Specification
- Authored and froze the foundational v1.0.0 technical specifications for the Smart India Hackathon (SIH 2026, Problem Statement PS26057), including:
  - Product Requirements Document (`PRD.md`)
  - Architectural Blueprint (`ARCHITECTURAL_BLUEPRINT.md`)
  - Database Schema & Spatial Indexing (`DB_SCHEMA.md`)
  - REST & WebSocket API Specification (`API_SPEC.md`)
  - UI/UX Design System Specification (`UI_UX_SPEC.md`)
  - Development Standards & Phased Implementation Plan (`DEVELOPMENT_GUIDELINES.md`)

#### Engineering Foundation
- Scaffolding of the core repository structure and runtime configurations (`backend/config.py`, `backend/logging_config.py`, `backend/exceptions.py`).
- Configured PostgreSQL / PostGIS database connection infrastructure, session factories, and Alembic database migration environment (`alembic.ini`, `0001_initial_schema.py`).
- Established base SQLAlchemy ORM relational models for surveys, acoustic metadata, processing jobs, detections, and audit reports (`backend/database/models.py`).
- Implemented Docker containerization stack including backend Dockerfile, frontend Dockerfile, Nginx reverse proxy configuration, and multi-service `docker-compose.yml`.
- Implemented initial FastAPI health routing (`/health`, `/api/v1/health`), baseline Celery worker configuration, and foundational test fixtures (`tests/backend/conftest.py`).

---

### Ayush Vishwakarma

**Git / Contact:** `officialayush5839@gmail.com`  
**Role:** Lead Systems Engineer & ML/Full-Stack Architect

#### Machine Learning & Acoustic AI Architecture
- Integrated the real Forward-Looking Sonar (FLS) acoustic dataset from the ARIS Explorer 3000 (3.0 MHz) benchmark (University of Groningen / Heriot-Watt University, DOI `10.5281/zenodo.15101686`).
- Designed and implemented the modular ML service framework in `backend/ml/`:
  - Primary multi-target 2D detector abstraction (`backend/ml/detector/base.py`, `yolo_detector.py`) with truthful weight verification.
  - Semantic segmentation boundary extraction (`backend/ml/segmentation/base.py`, `unet.py`, `segformer.py`) with graceful degradation fallbacks.
  - Secondary candidate crop verification classifier (`backend/ml/classifier/base.py`, `mobilenet.py`, `resnet.py`).
  - Decision fusion engine (`backend/ml/fusion/inference_fusion.py`) assessing multi-model consensus without overriding primary detector predictions.
  - Centralized Model Registry service (`backend/ml/registry/model_registry.py`) with truthful runtime status gating (`MISSING_WEIGHTS`, `UNAVAILABLE`, `EXPERIMENTAL`).
  - Chained inference pipeline orchestrator (`backend/ml/pipeline/inference_pipeline.py`).
- Enforced strict zero-fabrication safety gates to prevent unverified model outputs or synthetic labels.

#### Backend Systems & Distributed Pipeline
- Engineered the complete 10-stage Celery processing pipeline in `backend/tasks.py` (`Ingest → Preprocess → Tile → Detect → Filter → Segment → Classify → Georeference → Persist → Report`).
- Integrated real-time Redis WebSocket progress streaming, publishing granular stage events to connected clients.
- Developed the complete acoustic preprocessing cascade in `backend/preprocessing/` (dropout quality assessment, bottom detection, water-column removal, CLAHE contrast enhancement, median/bilateral denoising, slant-range correction, and 640×640 overlapping tiling).
- Implemented post-processing spatial algorithms (`backend/postprocessing/`): global coordinate restoration, Global NMS ($IoU = 0.45$), acoustic shadow filter, size constraint filter, and confidence temperature calibration.
- Implemented WGS84 georeferencing and physical metric dimension estimators (`backend/georeferencing/`).
- Built REST API routers for surveys, detections, processing jobs, WebSocket relays, audit reports, and model metadata.
- Implemented audit report generators supporting `JSON`, `CSV`, and `GeoJSON` FeatureCollections (`backend/reporting/`).
- Authored database schema migration `0002_ml_segmentation_classification.py` for segmentation masks and secondary classification tracking.

#### Frontend & UI/UX Transformation
- Architected the complete React + TypeScript single-page application using TanStack Query and Zustand.
- Led the comprehensive UI/UX redesign based on the **UI/UX Pro Max** skill, eliminating dark/neon cyberpunk motifs and establishing a commercial-grade, light-first Maritime Operations & Intelligence interface.
- Built the high-resolution Sonar Imaging Workstation (`SonarViewer.tsx`, `DetectionOverlay.tsx`, `SonarToggle.tsx`) featuring zoom ($25\% - 800\%$), pan, fit-to-screen, fullscreen mode, and multi-layer checkbox toggles (`Detections`, `Masks`, `Classifier`, `Confidence`, `GPS`).
- Created the scientific Target Inspection Drawer (`DetectionDetail.tsx`) displaying structured classification agreement, segmentation status, physical metric dimensions, and WGS84 coordinates.
- Implemented the Model Center (`ModelsPage.tsx`), Dataset Explorer (`DatasetPage.tsx`), Surveys Archive data table (`SurveyListPage.tsx`), Ingestion Wizard (`UploadPage.tsx`, `FileUploader.tsx`), and live Pipeline Flow monitor (`JobStatusBar.tsx`).
- Centralized light-mode design tokens in `tailwind.config.ts` and `index.css`, ensuring full WCAG 4.5:1 contrast compliance.

#### Dataset & Data Engineering
- Extracted, standardized, and validated 238 acoustic sonar images and 371 ground-truth bounding boxes (`datasets/sonar_debris/`) on 640×640 letterboxed canvases.
- Built sequence-split partitioning (Train: 166, Validation: 35, Test: 37) with strict sequence independence and 0% cross-split leakage.
- Developed dataset format converters (`training/conversion/voc_to_yolo.py`, `coco_to_yolo.py`), validation suites, and smoke test routines.

#### Testing, QA & Tooling
- Expanded backend automated test coverage to 65 passing tests with zero regressions across API, database, Celery, georeferencing, preprocessing, and ML integration modules.
- Created automated cross-platform startup tooling (`run.bat`, `scripts/wait_for_server.py`) with preflight checks and HTTP readiness verification.
- Authored technical documentation: `docs/ML_ARCHITECTURE.md`, `docs/ML_REFERENCE_INTEGRATION.md`, `docs/BLOCKER_1_DATASET_FINAL_REPORT.md`, `docs/ML_INTEGRATION_FINAL_REPORT.md`, and `docs/UI_UX_REDESIGN_REPORT.md`.

---

## Contribution Areas

The repository represents collaborative engineering across the following domains:

| Domain | Focus & Key Technologies |
| :--- | :--- |
| **Acoustic Imaging & FLS** | ARIS Explorer 3000 Forward-Looking Sonar (3.0 MHz), sidescan sonar strip ingestion, slant-range correction, CLAHE, and tiling. |
| **Machine Learning & AI** | YOLOv8m object detection, U-Net / SegFormer segmentation interfaces, MobileNet classifier, decision fusion, and model registry. |
| **Backend & Distributed Systems** | FastAPI, asynchronous SQLAlchemy, Celery distributed tasks, Redis pub/sub, PostgreSQL / PostGIS, and WebSocket streaming. |
| **Frontend & UI/UX** | React 18, TypeScript, Tailwind CSS, Leaflet GIS mapping, HTML5 Canvas visualization, and UI/UX Pro Max design tokens. |
| **Data Engineering** | Sequence-level dataset splitting, Pascal VOC to YOLO conversion, dataset manifest integrity, and zero-leakage validation. |
| **Quality & DevOps** | Pytest test suite (65 tests), Docker containerization, Alembic migrations, and automated startup launchers. |

---

## Attribution & Repository History

This document summarizes major architectural and implementation contributions based on the repository's verified Git commit history and project documentation.

Git commit history remains the authoritative, permanent record of exact code changes, commit hashes, timestamps, line-by-line diffs, and authorship. To inspect the full granular commit log, run:

```bash
git log --all --format="%h | %an | %ad | %s" --date=short
```

---

## How to Update This File

When a contributor completes a major feature, new architecture module, dataset integration, or significant documentation milestone:

1. Identify the meaningful technical contribution.
2. Locate (or add) the contributor's section under [## Contributors](#contributors).
3. Group the work under standard technical categories (e.g., `Machine Learning`, `Backend`, `Frontend / UI/UX`, `Dataset & Data Engineering`, `Testing & Quality`, `Documentation`).
4. Write concise, specific bullet points focusing on what was built or improved.
5. Do not duplicate individual commit messages or raw commit counts.
6. Verify all claims against actual repository code and Git commit history before submitting.
