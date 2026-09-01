# MarineDebris-Sonar-AI: Architecture & Specification Reconciliation

**Date:** 2026-09-01  
**Auditor:** Principal Backend & ML Infrastructure Engineer  
**Objective:** Compare current codebase against `PRD.md`, `ARCHITECTURAL_BLUEPRINT.md`, `DB_SCHEMA.md`, `API_SPEC.md`, `DEVELOPMENT_GUIDELINES.md`, and `BACKEND_ACCEPTANCE_AUDIT.md`.

---

## 1. Executive Reconciliation Summary

The backend implementation exhibits high architectural fidelity to the authoritative specifications:
- Data contracts (`SonarPing`, `SonarMetadata`, `SonarFrame`) match `ARCHITECTURAL_BLUEPRINT.md` §5.
- 8-stage preprocessing sequence matches `ARCHITECTURAL_BLUEPRINT.md` §6.
- Georeferencing geodesic math matches `ARCHITECTURAL_BLUEPRINT.md` §7.
- Database relational entities, cascade rules, and check constraints match `DB_SCHEMA.md`.
- REST endpoints and response envelopes match `API_SPEC.md`.

Below is the categorized reconciliation of genuine gaps and operational discrepancies.

---

## 2. Categorized Findings

### [CRITICAL] Missing Pre-Trained Weights Checkpoint
- **Specification:** `ARCHITECTURAL_BLUEPRINT.md` §9 & `DB_SCHEMA.md` specify `sonar_yolov8m_ghostpot_v1.pt` as the default active detection model.
- **Current Codebase:** `models/detection/` contains no `.pt`, `.onnx`, or `.safetensors` weight files.
- **Impact:** System runs the full pipeline and persists jobs, but produces 0 detections because `ModelLoader` truthfully returns `None` and `detector.py` returns empty detection lists.
- **Resolution Plan:** Check for dataset availability in `training/` or acquire marine debris sidescan sonar checkpoints. In the absence of real weights, retain the truthful empty-detection state without data fabrication.

---

### [HIGH] Unconditional Schema DDL Execution on Startup
- **Specification:** `DEVELOPMENT_SETUP.md` & `DB_SCHEMA.md` §6 mandate Alembic (`alembic upgrade head`) as the authoritative schema migration engine.
- **Current Codebase:** `backend/api/main.py` runs `Base.metadata.create_all` unconditionally in the `lifespan` handler on startup.
- **Impact:** When `alembic upgrade head` is later executed against the same database, Alembic crashes with `table surveys already exists` because `create_all` created tables without stamping `alembic_version`.
- **Resolution Plan:** Introduce `AUTO_CREATE_TABLES` configuration flag. Default to `true` only for lightweight local standalone development (`ENVIRONMENT=development` and SQLite), and enforce `false` for production / Docker where Alembic runs as part of entrypoint migrations.

---

### [HIGH] XTF In-Memory Reading Profile
- **Specification:** `ARCHITECTURAL_BLUEPRINT.md` §5 & Master Build Prompt §17 explicitly require streaming chunked processing without loading entire multi-GB sonar files into RAM.
- **Current Codebase:** `backend/sonar_parser/xtf_parser.py` yields pings in configurable chunks (default 2000), but uses `pyxtf.xtf_read(file_path)` which reads the raw binary file into Python objects in memory before iteration.
- **Impact:** While downstream processing is chunked and memory-bounded, the initial read of a 2GB+ raw XTF file incurs high memory spikes.
- **Resolution Plan:** Document the memory constraint; investigate low-level packet-header streaming for future iteration.

---

### [MEDIUM] Port Mapping Differences Between Docker and Local Standalone
- **Specification:** `docker-compose.yml` binds `8000:8000`, while `run.bat` and `frontend/vite.config.ts` configure local ports `5039` (backend) and `2671` (frontend).
- **Impact:** Minor configuration confusion when toggling between Docker Compose and Windows native scripts.
- **Resolution Plan:** Ensure `PORT` environment variable and `.env.example` explicitly document the dual port conventions.

---

### [LOW] SQLAlchemy Subquery Cartesian Product Warnings
- **Specification:** Clean query execution without warnings.
- **Current Codebase:** `surveys.py` subqueries generate `SAWarning: SELECT statement has a cartesian product between FROM element(s) "detections" and FROM element "anon_1"`.
- **Impact:** Query succeeds and returns correct counts, but logs warnings during test execution.
- **Resolution Plan:** Explicitly correlate subqueries on `Detection.survey_id == Survey.id`.

---

### [COSMETIC] UTC Datetime Deprecation Warnings
- **Current Codebase:** SQLAlchemy models and task updates trigger `DeprecationWarning: datetime.datetime.utcnow() is deprecated`.
- **Resolution Plan:** Use `datetime.now(timezone.utc)` uniformly across models.
