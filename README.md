# MarineDebris-Sonar-AI

**Competition / Problem Statement:** SIH 2026 — PS26057  
**Topic:** AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery  
**Status:** Implementation Complete (Phases 0–14 Verified, 40/40 Tests Passing)

## Quick Start (One-Click Launch)

To start both the Backend and Frontend with automated environment detection and dependency setup:

Simply double-click or run:
```cmd
run.bat
```

The script will automatically:
1. Detect Python (3.10+) and Node.js (18+).
2. Set up Python virtual environment (`.venv`) and install dependencies.
3. Install frontend dependencies (`npm install`).
4. Initialize local storage directories and database tables.
5. Launch the **FastAPI Backend on port 5039**: `http://localhost:5039`
6. Launch the **React Frontend on port 2671**: `http://localhost:2671`
7. Automatically open your browser to `http://localhost:2671`.

---

## Service URLs
- **Web Application UI:** [http://localhost:2671](http://localhost:2671)
- **FastAPI REST API:** [http://localhost:5039](http://localhost:5039)
- **Interactive Swagger Docs:** [http://localhost:5039/docs](http://localhost:5039/docs)

---

## Overview

MarineDebris-Sonar-AI is an end-to-end automated system designed to ingest side-scan sonar (SSS) imagery, preprocess acoustic data to remove artifacts and noise, detect and classify underwater marine debris and seabed anomalies (separating artificial man-made objects from natural seafloor features), georeference detections, and present actionable insights through an interactive dashboard with exportable reports.

## Authoritative Specification Documents (v1.0.0 Frozen)

The project architecture, data models, interface definitions, and development protocols are defined in the following frozen specifications:

* [PRD.md](PRD.md) — Product Requirements Document & Problem Statement Compliance Matrix
* [ARCHITECTURAL_BLUEPRINT.md](ARCHITECTURAL_BLUEPRINT.md) — System Architecture, Processing Pipelines & Hardware Specs
* [DB_SCHEMA.md](DB_SCHEMA.md) — PostgreSQL / PostGIS Relational Schema & Indices
* [API_SPEC.md](API_SPEC.md) — REST & WebSocket API Endpoint Specifications
* [UI_UX_SPEC.md](UI_UX_SPEC.md) — User Interface Architecture, Workflows & Component Design
* [DEVELOPMENT_GUIDELINES.md](DEVELOPMENT_GUIDELINES.md) — Coding Standards, Phase Plans & Definition of Done
* [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) — Phase-by-Phase Verification Log & Test Suite Results
