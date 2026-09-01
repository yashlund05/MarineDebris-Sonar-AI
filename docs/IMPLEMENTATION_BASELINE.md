# MarineDebris-Sonar-AI: Implementation Baseline

**Date:** 2026-09-01  
**Baseline Test Status:** 41 passed, 0 failed (100% pass rate)  
**Execution Duration:** 32.64 seconds  
**Command Executed:** `python -m pytest tests/backend -v`  
**Host Platform:** Windows (win32)  
**Python Version:** Python 3.14.6  
**Git Commit Hash:** `662d165c8b0946507ba801592525802896e20717`  

---

## 1. Key Dependency Versions
- **FastAPI:** `0.139.0`
- **SQLAlchemy:** `2.0.51`
- **Pydantic:** `2.13.4`
- **OpenCV (opencv-python-headless):** `5.0.0`
- **Pytest:** `9.1.1`
- **HTTPX:** `0.28.1`
- **Celery:** `5.6.2`

---

## 2. Test Suite Composition (41 Tests)
1. `tests/backend/test_api_detections.py` (2 tests) - Query empty detections, 404 lookup.
2. `tests/backend/test_api_surveys.py` (6 tests) - Upload validation, mime, size, listing, cascade deletion.
3. `tests/backend/test_celery.py` (2 tests) - Broker config, health ping task.
4. `tests/backend/test_config.py` (3 tests) - Default settings, dual DB URL generation, Redis URL resolution.
5. `tests/backend/test_database.py` (2 tests) - ORM entity relations, model registry queries.
6. `tests/backend/test_e2e_backend_pipeline.py` (1 test) - Full 20-step lifecycle test.
7. `tests/backend/test_georeferencing.py` (4 tests) - WGS84 great-circle geodesy, missing GPS handling, dimension calculations.
8. `tests/backend/test_health.py` (2 tests) - Root health, `/api/v1/health` status.
9. `tests/backend/test_preprocessing.py` (12 tests) - Normalization, CLAHE, denoising, bottom detection, water column, tiling, quality scoring.
10. `tests/backend/test_sonar_parser.py` (7 tests) - Domain models, PNG loader, routing ingestor, nav CSV parsing.

---

## 3. Current Known Blockers & Model Weight State
- **Trained Model Weights:** **BLOCKED**. No `.pt`, `.onnx`, or `.safetensors` weight file exists in `models/detection/`.
- **Inference Behavior:** Truthful. `ModelLoader` logs missing weights and returns `None`; `detector.py` returns empty detection list without fabricating mock anomalies.
- **Production DDL Risk:** Application startup executes `Base.metadata.create_all`, which needs environment-level gating (`AUTO_CREATE_TABLES=false`) for production Alembic compliance.
