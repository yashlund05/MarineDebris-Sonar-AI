## 2026-09-19T06:17:33Z

You are teamwork_preview_worker_m1_remediate_0.
Your working directory is: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_worker_m1_remediate_0
Read and obey all constraints in: c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

MISSION:
Execute the remediation of Milestone 1 streaming infrastructure based on adversarial review findings from Reviewer 2, Challenger 1, and E2E Test Writer.

INPUTS:
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\ORIGINAL_REQUEST.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_reviewer_m1_2\handoff.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_challenger_m1_1\handoff.md
- c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\TEST_READY.md

REQUIRED REMEDIATIONS:
1. `backend/live_sonar/adapters/rtsp.py`:
   - Enforce `network_allowlist`: parse IP/subnets with `ipaddress` module and check if candidate host matches allowed CIDRs or hostnames.
   - Harden SSRF: block link-local network `169.254.0.0/16`, alternative decimal/octal/IPv6-mapped notations, and cloud metadata hostnames (`metadata.google.internal`).
   - In `sanitize_rtsp_uri()`, redact sensitive query parameters (e.g. `token`, `pwd`, `password`, `key`).
2. `backend/live_sonar/session.py`:
   - In `_ingestion_loop()`, when stream finishes naturally (EOF on unlooped replay or disconnect), call `await self.buffer.close()` so downstream consumers awaiting `buffer.get()` do not hang.
3. `backend/live_sonar/buffer.py`:
   - In `clear()`, make sure it does not fail silently on unacquired condition locks, or implement async `aclear()` that acquires `self._lock` and wakes waiting producers. In `put_nowait()`, ensure `_has_items` is notified.
   - Bound timestamp history deques (`_received_timestamps`, `_dropped_timestamps`, etc.) with a `maxlen` (e.g. 10000) or prune on `put()` to prevent unbounded memory growth when `get_metrics()` is not polled.
   - Fix initial FPS calculation: measure elapsed time since buffer creation (`time.monotonic() - self._start_time`) instead of raw monotonic uptime.
4. `backend/live_sonar/adapters/replay.py`:
   - Reject empty or whitespace URIs (`if not self.source_uri or not self.source_uri.strip(): raise LiveSonarSourceInvalidError(...)`).
   - Guard against 0-byte corrupt image files before calling `cv2.imread()`.
5. `backend/inference/detector.py`:
   - Line 68: Change `if result.boxes:` to `if len(result.boxes) > 0:` to prevent NumPy 2.x ambiguous truthiness error.
6. `tests/backend/test_config.py`:
   - Line 16: Update assertion to `"production_fls_yolov8n"` so baseline config test passes.

VERIFICATION:
- Run all unit tests: `python -m pytest tests/live_sonar/`
- Run all E2E tests: `python -m pytest tests/live_sonar/test_tier1_features.py tests/live_sonar/test_tier2_boundaries.py tests/live_sonar/test_tier3_interactions.py tests/live_sonar/test_tier4_e2e_replay.py`
- Run health check: `python -m pytest tests/backend/test_health.py`
- Verify production model SHA256 has not changed (`e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`).
- Verify `git diff datasets/` is empty.

Write a 5-component `handoff.md` in your working directory and notify the orchestrator when complete.
