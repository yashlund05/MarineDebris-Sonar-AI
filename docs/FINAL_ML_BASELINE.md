# MarineDebris-Sonar-AI: Final Machine Learning Baseline Lock

**Lock Date:** 2026-09-01  
**Lead Engineer:** Senior ML Engineer & Backend QA Lead  
**Git Commit Hash:** `662d165c8b0946507ba801592525802896e20717`  
**Baseline Test Execution:** `python -m pytest tests/backend -v`  
**Test Result:** **50 passed, 0 failed in 37.50s (100% Pass Rate)**  

---

## 1. Environment & Hardware Matrix
- **Python Version:** `3.14.6 (tags/v3.14.6:c63aec6, Jun 10 2026)`
- **PyTorch Version:** `2.13.0+cpu`
- **Ultralytics (YOLO) Version:** `8.4.125`
- **CUDA Availability:** `False`
- **GPU Device:** `None (CPU)`
- **VRAM:** `N/A (Host System RAM)`
- **Operating System:** `Windows-11-10.0.26200-SP0`
- **PostgreSQL Version:** `16.3-alpine` (Docker) / `5432` (Host socket verified)
- **Redis Version:** `7.2-alpine` (Docker) / `6379` (Host RESP2 verified)
- **Celery Version:** `5.6.3`
- **FastAPI Version:** `0.139.0`
- **SQLAlchemy Version:** `2.0.51`

---

## 2. Test Suite Status (50 Tests)
- `tests/backend/test_api_detections.py` (2 tests): Empty query & 404 handler.
- `tests/backend/test_api_models.py` (2 tests): Truthful model loader state & API registry response.
- `tests/backend/test_api_surveys.py` (6 tests): Multipart upload, size, MIME, listing, cascade deletion.
- `tests/backend/test_celery.py` (2 tests): Celery config & health ping.
- `tests/backend/test_config.py` (3 tests): Settings, dual database URL generation, Redis URL.
- `tests/backend/test_database.py` (3 tests): Relations, model registry ORM, production DDL gating.
- `tests/backend/test_e2e_backend_pipeline.py` (1 test): Full 20-step lifecycle test.
- `tests/backend/test_georeferencing.py` (5 tests): WGS84 geodesy, missing GPS handling, dimension math, cardinal headings (0/90/180/270), channel symmetry.
- `tests/backend/test_health.py` (2 tests): Root & `/api/v1/health`.
- `tests/backend/test_postprocessing.py` (5 tests): True IoU calculation, global NMS suppression, class separation, size filter, Platt calibration.
- `tests/backend/test_preprocessing.py` (12 tests): Normalization, CLAHE, median denoising, bottom detection, water column removal, tiling, quality score.
- `tests/backend/test_sonar_parser.py` (7 tests): Domain models, PNG loader, routing ingestor, nav CSV parsing.

---

## 3. Machine Learning & Dataset Current Status
- **Model Checkpoint Status:** `MISSING_WEIGHTS` (File `models/detection/sonar_yolov8m_ghostpot_v1.pt` absent).
- **Dataset Availability:** `DATASET BLOCKED` (0 real Sidescan Sonar annotation files in repository).
- **Inference Pipeline:** Functional in zero-weight mode (returns empty detections cleanly without fabrication).
- **Anti-Fabrication Guardrail:** Active and verified.
