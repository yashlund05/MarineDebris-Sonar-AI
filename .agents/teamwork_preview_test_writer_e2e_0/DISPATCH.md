## 2026-09-19T06:02:51Z
You are teamwork_preview_test_writer_e2e_0.
Your working directory is: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_test_writer_e2e_0
Read and obey all constraints in: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md

MISSION:
Execute the E2E Testing Track for the Live Sonar AI Detection & Tracking Subsystem.
Follow the E2E Testing Track Principles and 4-tier methodology (Category-Partition, Boundary Value Analysis, Pairwise Combinations, and Real-World Workload Testing).

INPUTS:
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_orchestrator_1\PROJECT.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_backend_1\spec_backend.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_frontend_1\spec_frontend.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_explorer_testenv_1\baseline_env.md

TASKS:
1. Create `TEST_INFRA.md` at project root (`c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\TEST_INFRA.md`) adhering to the test infra template.
2. Build deterministic replay test fixtures in `tests/fixtures/live_sonar/` using the verified real ARIS 3K FLS sonar imagery in `data/test_sonar_images/`.
3. Author comprehensive opaque-box test suites in `tests/live_sonar/`:
   - `test_tier1_features.py`: Feature coverage for streaming, buffers, sessions, inference adapter, tracking, confirmation, and WebSocket message schemas.
   - `test_tier2_boundaries.py`: Boundary and corner cases (queue depth limit, drop policies DROP_OLDEST/FIFO/DROP_NEWEST/LATEST, backpressure latency, disconnect/reconnect, empty frames, extreme dimensions).
   - `test_tier3_interactions.py`: Pairwise and multi-component interactions (backpressure under slow inference, track continuity across buffer drops, class consistency with noisy detections).
   - `test_tier4_e2e_replay.py`: Full end-to-end replay lifecycle (session init -> frame streaming -> detection -> track persistence -> WebSocket broadcast -> stop).
4. Publish `TEST_READY.md` at project root (`c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\TEST_READY.md`) with the runner command (`python -m pytest tests/live_sonar/`), coverage table, and feature checklist.

EXCLUSIVE WRITE BOUNDARIES:
- `TEST_INFRA.md`
- `TEST_READY.md`
- `tests/live_sonar/test_tier1_features.py`
- `tests/live_sonar/test_tier2_boundaries.py`
- `tests/live_sonar/test_tier3_interactions.py`
- `tests/live_sonar/test_tier4_e2e_replay.py`
- `tests/fixtures/live_sonar/*`

SAFETY & INTEGRITY:
DO NOT modify `models/detection/sonar_yolov8_fls_trained.pt` or anything in `datasets/`.

Deliver `handoff.md` in your working directory and notify the orchestrator when `TEST_READY.md` is published.
