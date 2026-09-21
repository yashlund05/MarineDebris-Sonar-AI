# Execution Plan: Live Sonar AI Detection & Tracking Subsystem

## Objective
Implement production-grade Live Sonar AI Detection & Tracking subsystem according to `ORIGINAL_REQUEST.md`, preserving model immutability, dataset frozenness, existing functionality, and strictly avoiding any fake/fabricated data.

## Phase 0: Survey (3 Parallel Explorers/Spec Miners)
- Agent 1 (Spec Miner - Backend & Specs): Extract specifications from `DEVELOPMENT_GUIDELINES.md`, `ARCHITECTURAL_BLUEPRINT.md`, `API_SPEC.md`, `DB_SCHEMA.md`, `PRD.md`, and backend structure (`backend/inference/`, `backend/preprocessing/`, `backend/enhancement/`, `backend/config.py`, `backend/database/models.py`).
- Agent 2 (Spec Miner - Frontend & UX): Extract specifications from `UI_UX_SPEC.md`, `frontend/src/`, components, routing, maritime design system, WebSocket hooks, and state management.
- Agent 3 (Explorer - Testing & Baseline): Survey existing test suites (`pytest`), fixtures, sample data/video/images for replay adapter, verification commands, environment dependencies, model hash confirmation.

## Phase 1: Decomposition & Global Index (PROJECT.md)
- Feature Inventory mapping all requirements R1-R6 to milestones.
- Milestone definitions M1 to M6 + E2E Testing Track.
- Interface contracts between modules.
- Code layout and write ownership boundaries.

## Phase 2: Dual Track Execution
- E2E Testing Track: Design test harness, replay fixture, and Tier 1-4 tests (`TEST_READY.md`).
- Implementation Track:
  - M1: Streaming Infrastructure (`backend/live_sonar/adapters/`, `buffer.py`, `session.py`, `models.py`)
  - M2: AI Pipeline & Tracking (`backend/live_sonar/pipeline/`, `tracker.py`, `confirmation.py`)
  - M3: WebSocket & REST API (`backend/live_sonar/api/`, routers, schemas, health)
  - M4: Persistence & Evidence (`backend/database/`, Alembic migration, recording/evidence manager)
  - M5: Frontend Live Sonar UI (`frontend/src/features/live-sonar/`, canvas viewport, targets, metrics, controls)
  - M6: Full E2E Test Pass & Hardening.

## Phase 3: Gate & Integrity Verification
- Reviewers (2) + Challengers (2) + Forensic Auditor (1)
- Verify production model SHA256 matches exact hash.
- Verify datasets are unmodified.
- Verify zero fake/fabricated data across backend and frontend.
- Verify passing tests and build.

## Phase 4: Delivery
- Handoff report and victory claim to Sentinel.
