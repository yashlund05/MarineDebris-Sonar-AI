# Handoff Report: Milestone 1 Independent Review & Adversarial Audit

**Author:** `teamwork_preview_reviewer_m1_2`  
**Role:** Reviewer & Adversarial Critic  
**Milestone:** Milestone 1 (Streaming Infrastructure & Source Adapters)  
**Date:** 2026-09-19  
**Recipient:** `parent` (`teamwork_preview_orchestrator_1`, conversation ID: `ef6df81e-fc05-429e-b45e-d6e075359bbb`)  
**Verdict:** `REQUEST_CHANGES`

---

## 1. Observation

### Observation 1: Model & Dataset Non-Negotiables Verified
1. **Production Model Immutability:**  
   Command executed:
   ```cmd
   certutil -hashfile models\detection\sonar_yolov8_fls_trained.pt SHA256
   ```
   Verbatim output:
   ```
   SHA256 hash of models\detection\sonar_yolov8_fls_trained.pt:
   e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7
   CertUtil: -hashfile command completed successfully.
   ```
   Confirmed identical to specified requirement.

2. **Dataset Untouched:**  
   Command executed:
   ```cmd
   git diff --name-only datasets/
   ```
   Output: Empty. No dataset files modified.

3. **No Fake Telemetry / No Hardcoded Detections:**  
   Grep scan for fake/mock data in `backend/live_sonar/` confirmed zero fabricated detections, fake GPS, or fake confidence values. Missing values cleanly default to `None`.

### Observation 2: M1 Test Suite Execution
Command executed:
```cmd
python -m pytest tests/live_sonar/test_buffer.py tests/live_sonar/test_adapters.py tests/live_sonar/test_session.py -v
```
Verbatim result: `23 passed in 30.66s`.  
Tier 1 & Tier 2 test suites (`test_tier1_features.py`, `test_tier2_boundaries.py`) passed `33 passed in 9.36s`.

### Observation 3: Critical Flaw — Unenforced SSRF Network Allowlist
Inspecting `backend/live_sonar/adapters/rtsp.py:50-84`:
```python
def validate_rtsp_uri(
    uri: str,
    allow_local: bool = True,
    network_allowlist: Optional[List[str]] = None,
) -> None:
    ...
    # Block AWS/GCP/Azure link-local cloud metadata IP
    if host == "169.254.169.254":
        raise LiveSonarSecurityViolationError(...)
    # Check loopback
    if host.lower() in ("localhost", "127.0.0.1", "::1"):
        ...
```
`network_allowlist` is received as an argument and passed from `backend/config.py` (`LIVE_SONAR_NETWORK_ALLOWLIST`), but `network_allowlist` is NEVER evaluated inside `validate_rtsp_uri()`.  
Executing adversarial test:
```python
validate_rtsp_uri('rtsp://8.8.8.8/live', network_allowlist=['192.168.1.0/24'])
```
Exited with code 0 without raising any error.  
Furthermore, testing alternate metadata endpoints (`rtsp://2852039166/feed`, `rtsp://0251.0376.0251.0376/feed`, `rtsp://[::ffff:169.254.169.254]/feed`, `rtsp://metadata.google.internal/feed`) all bypassed validation because only literal string `"169.254.169.254"` is filtered.

### Observation 4: Major Flaw — Natural Stream EOF Causes Downstream Consumer Hang
Inspecting `backend/live_sonar/session.py:167-173`:
```python
    # Stream finished naturally (e.g. EOF in replay without loop)
    if self._status not in (SessionStatus.STOPPING, SessionStatus.STOPPED):
        async with self._status_lock:
            self._status = SessionStatus.STOPPED
            self._stopped_at = datetime.now(timezone.utc)
        await self.adapter.disconnect()
        # Missing: await self.buffer.close()
```
Executing adversarial test with a finite 6-frame image sequence:
```python
session = LiveSonarSession(cfg)
await session.start()
await asyncio.sleep(0.2)
# Drained 6 frames
await asyncio.wait_for(session.buffer.get(), timeout=0.2)
```
Produced verbatim output:
```
HANG: Consumer hangs indefinitely on buffer.get() after stream ended!
```
Because `self.buffer.close()` is never called when ingestion hits EOF, downstream consumers waiting on `await session.buffer.get()` hang forever.

### Observation 5: Major Flaw — Latent Deadlock in `FrameBuffer.clear()`
Inspecting `backend/live_sonar/buffer.py:244-250`:
```python
    def clear(self) -> None:
        """Clear all queued frames without closing the buffer."""
        self._queue.clear()
        try:
            self._has_space.notify_all()
        except RuntimeError:
            pass
```
Because `clear()` is synchronous and does not hold `self._lock`, calling `self._has_space.notify_all()` raises `RuntimeError("cannot notify on un-acquired lock")`, which is silently swallowed by `except RuntimeError: pass`.  
Executing adversarial test with a producer blocked in `await buf.put()` (under `FIFO` policy):
Calling `buf.clear()` failed to wake the producer, producing verbatim output:
```
DEADLOCK: Producer remained blocked after buf.clear()!
```
Similarly, `put_nowait()` does not notify `_has_items`, leaving `await buf.get()` consumers blocked even after an item is pushed.

### Observation 6: Major Flaw — Timestamp History Memory Leak Under Load
Inspecting `backend/live_sonar/buffer.py:89-127, 198-210`:  
`self._received_timestamps.append(now)` and `self._dropped_timestamps.append(now)` run on every `put()`, but `_prune_windows()` is ONLY called inside `get_metrics()`.  
Executing adversarial test: Pushing 50,000 frames into `FrameBuffer(maxsize=10, policy=DropPolicy.DROP_OLDEST)` without polling `get_metrics()` resulted in:
```
Queue size: 10
Frames received: 50000
Frames dropped: 49990
len(_received_timestamps): 50000
len(_dropped_timestamps): 49990
```
Deallocated frames dropped from the queue, but timestamps leaked unbounded memory.

### Observation 7: Minor Flaws — Startup FPS Deflation and Query Parameter Credential Exposure
1. **Initial FPS Calculation:** In `backend/live_sonar/buffer.py:212`, `window_duration = max(0.1, min(self._window_sec, now))` evaluates `min(5.0, now)` where `now = time.monotonic()`. Because `time.monotonic()` reflects system uptime (> 1000s), `window_duration` is always 5.0 from the first millisecond. Streaming 15 frames over 0.71s reported `3.0 FPS` instead of `~21.0 FPS`.
2. **RTSP Query Scrubbing:** In `backend/live_sonar/adapters/rtsp.py:33-48`, `sanitize_rtsp_uri()` only sanitizes `netloc`. Supplying `rtsp://192.168.1.50/live?token=secret123` left the token unredacted in `parsed.query`.

---

## 2. Logic Chain

1. **Security Policy Non-Conformance (Observation 3):**
   - Requirement R3 explicitly mandates: *"implement allowlist for external network sources"*.
   - Worker implemented `LIVE_SONAR_NETWORK_ALLOWLIST` in `backend/config.py` and passed it to `validate_rtsp_uri()`.
   - However, the validation logic in `validate_rtsp_uri()` completely ignores the allowlist parameter, allowing connections to any arbitrary external IP address. Additionally, cloud metadata checks are easily bypassed via alternative IP representations and DNS names. This constitutes a Critical finding.

2. **Pipeline Termination Failure (Observation 4):**
   - Requirement R1 and M1 ↔ M2 interface contract expect clean streaming lifecycle.
   - When replay streams finish at EOF, `_ingestion_loop()` marks the session stopped but fails to call `await self.buffer.close()`.
   - When Milestone 2 AI worker or WebSocket stream worker drains the buffer via `await session.buffer.get()`, it will block indefinitely instead of receiving an EOF signal (`asyncio.QueueEmpty`). This will break replay processing in subsequent milestones.

3. **Concurrency & Deadlock Hazards (Observation 5):**
   - In `backend/live_sonar/buffer.py`, `Condition.notify_all()` requires the Condition lock to be acquired.
   - Synchronous `clear()` attempts to notify `_has_space` without holding the lock and silences `RuntimeError`. Any producer awaiting buffer capacity on a full FIFO queue deadlocks permanently even though the buffer was cleared.

4. **Bounded Memory Violation (Observation 6):**
   - Requirement R1 mandates: *"Never allow unbounded memory growth"*.
   - Because timestamp pruning is deferred exclusively to `get_metrics()`, any usage pattern where metrics are polled infrequently or decoupled from frame consumption leaks timestamps linearly with stream volume.

---

## 3. Caveats

1. **CPU Inference Latency in Tier 4:** In `tests/live_sonar/test_tier4_e2e_replay.py`, `test_e2e_sustained_workload_throughput_and_latency` failed because CPU inference took 2462ms against an unyielding 500ms assertion. This is an environment/test assertion calibration issue in Tier 4 (E2E track), not an M1 adapter/buffer defect.
2. **Physical Hardware Limitations:** Physical RTSP cameras and USB DirectShow capture devices were not attached; adapter tests appropriately used loopback, synthetic, and mocked connection failures.

---

## 4. Conclusion

While Milestone 1 establishes clean architectural abstractions, passes all its designated unit tests (23/23), preserves production model weights, and avoids hardcoded fake data, it contains **1 Critical security vulnerability** (unenforced network allowlist) and **3 Major concurrency/lifecycle bugs** (EOF consumer hang, clear() deadlock, timestamp memory leak).

**Definitive Verdict:** `REQUEST_CHANGES`

### Required Remediations Before Approval:
1. **Enforce `network_allowlist` and harden SSRF in `backend/live_sonar/adapters/rtsp.py`:**
   - Parse and match `host` against IP subnets using `ipaddress` module and allowed hostnames.
   - Reject decimal/octal/IPv6-mapped metadata IPs and known metadata hostnames (`metadata.google.internal`).
   - Redact sensitive query parameters (`token`, `pwd`, `password`, `key`) in `sanitize_rtsp_uri()`.
2. **Close Buffer on Natural Stream EOF in `backend/live_sonar/session.py`:**
   - In `_ingestion_loop()`, when stream finishes naturally, call `await self.buffer.close()` so awaiting consumers receive `asyncio.QueueEmpty` and exit cleanly.
3. **Fix `FrameBuffer` Deadlock & Memory Leak in `backend/live_sonar/buffer.py`:**
   - Either make `clear()` async (`async def clear(self)`) acquiring `self._lock` before notifying, or document `aclear()` and remove the broken silent-fail notify in `clear()`.
   - Prune timestamps periodically during `put()` / `get()` or assign `maxlen` to history deques.
   - Fix initial FPS calculation by measuring against elapsed time since buffer start (`now - self._start_time`).

---

## 5. Verification Method

To independently verify these findings:

1. **Verify SSRF Allowlist Bypass:**
   ```bash
   python -c "from backend.live_sonar.adapters.rtsp import validate_rtsp_uri; validate_rtsp_uri('rtsp://8.8.8.8/live', network_allowlist=['192.168.1.0/24']); print('VULNERABLE: Allowlist ignored')"
   ```
   *Expected if broken:* Prints VULNERABLE without exception.

2. **Verify Consumer Hang on Stream EOF:**
   ```bash
   python -c "import asyncio; from backend.live_sonar.session import LiveSonarSession; from backend.live_sonar.models import LiveSonarSessionConfig; cfg = LiveSonarSessionConfig(session_id='t', source_type='replay', source_uri='data/test_sonar_images', target_fps=200.0); s = LiveSonarSession(cfg); asyncio.run(s.start()); import time; time.sleep(0.3); asyncio.run(asyncio.wait_for(s.buffer.get(), 0.5))"
   ```
   *Expected if broken:* Raises `TimeoutError` after exhausting the 6 frames.

3. **Verify Deadlock in `FrameBuffer.clear()`:**
   ```bash
   python -c "import asyncio; from backend.live_sonar.buffer import FrameBuffer; from backend.live_sonar.models import DropPolicy, SonarFrame; buf = FrameBuffer(maxsize=1, policy=DropPolicy.FIFO); asyncio.run(buf.put(SonarFrame(1))); p = asyncio.create_task(buf.put(SonarFrame(2))); buf.clear()"
   ```
   *Expected if broken:* Producer task remains hung.
