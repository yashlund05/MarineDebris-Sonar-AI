## 2026-09-19T06:02:51Z

You are teamwork_preview_worker_m1_0.
Your working directory is: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_worker_m1_0
Read and obey all constraints in: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MISSION:
Implement Milestone 1 (Streaming Infrastructure & Source Adapters) according to Requirement R1 of ORIGINAL_REQUEST.md and the specifications in `spec_backend.md`.

INPUTS:
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_orchestrator_1\PROJECT.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_backend_1\spec_backend.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_explorer_testenv_1\baseline_env.md

EXCLUSIVE WRITE BOUNDARIES:
- `backend/live_sonar/__init__.py`
- `backend/live_sonar/models.py` (SonarFrame, SonarMetadataPayload, NavPayload, QualityPayload, LiveMetricsPayload, SessionStatus)
- `backend/live_sonar/buffer.py` (Bounded async FrameBuffer with DROP_OLDEST, FIFO, DROP_NEWEST, LATEST policies, drop counters, queue metrics)
- `backend/live_sonar/session.py` (LiveSonarSession lifecycle manager: CONNECTING, CONNECTED, RUNNING, DEGRADED, STOPPING, STOPPED, ERROR)
- `backend/live_sonar/adapters/__init__.py`
- `backend/live_sonar/adapters/base.py` (SonarStreamAdapter ABC: connect, disconnect, frames, health, metadata)
- `backend/live_sonar/adapters/replay.py` (ReplayStreamAdapter: PNG sequences from image paths/folders, MP4/video files, synthetic streams)
- `backend/live_sonar/adapters/rtsp.py` (RTSPStreamAdapter: safe RTSP stream decoder with reconnect and timeout)
- `backend/live_sonar/adapters/usb.py` (USBCameraStreamAdapter: device index camera capture)
- `backend/live_sonar/adapters/native.py` (NativeSonarStubAdapter: hardware boundary reporting NOT_CONFIGURED when no physical hardware)
- `backend/config.py` (add LIVE_SONAR_* settings fields cleanly)
- Unit tests: `tests/live_sonar/test_buffer.py`, `tests/live_sonar/test_adapters.py`, `tests/live_sonar/test_session.py`

VERIFICATION REQUIREMENTS:
1. Run unit tests: `python -m pytest tests/live_sonar/test_buffer.py tests/live_sonar/test_adapters.py tests/live_sonar/test_session.py`
2. Run health regression check: `python -m pytest tests/backend/test_health.py`
3. Document exact commands and passing outputs in your handoff report.

Deliver a 5-component `handoff.md` in your working directory and notify the orchestrator upon completion.
