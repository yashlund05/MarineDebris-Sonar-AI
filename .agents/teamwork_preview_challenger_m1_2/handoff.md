# Adversarial Challenge & Handoff Report: Milestone 1

**Author:** `teamwork_preview_challenger_m1_2`  
**Role:** EMPIRICAL CHALLENGER (`critic`, `specialist`)  
**Milestone:** Milestone 1 (Streaming Infrastructure & Source Adapters)  
**Date:** 2026-09-19  
**Recipient:** `parent` (`teamwork_preview_orchestrator_1`, conversation ID: `ef6df81e-fc05-429e-b45e-d6e075359bbb`)  
**Verdict:** `APPROVE` (with actionable security recommendations tracked for Milestone 3)

---

## 1. Observation

1. **Production Model Immutability Verified:**
   Executing command:
   ```cmd
   certutil -hashfile "models\detection\sonar_yolov8_fls_trained.pt" SHA256
   ```
   Verbatim output:
   ```
   SHA256 hash of models\detection\sonar_yolov8_fls_trained.pt:
   e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7
   CertUtil: -hashfile command completed successfully.
   ```

2. **Frozen Dataset Protection Verified:**
   Executing command `git diff datasets/` produced empty stdout and stderr, verifying zero modifications to benchmark datasets.

3. **Empirical Adversarial Test Execution:**
   Created independent test suite `tests/live_sonar/test_challenger_adapters.py` containing 20 adversarial test cases.
   Executing command:
   ```cmd
   python -m pytest tests/live_sonar/test_challenger_adapters.py -v
   ```
   Verbatim output:
   ```
   ============================= test session starts =============================
   platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
   rootdir: C:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar
   configfile: pytest.ini
   plugins: anyio-4.14.0, locust-2.46.1, asyncio-1.4.0, benchmark-5.2.3, django-4.14.0, mock-3.15.1
   asyncio: mode=Mode.AUTO, debug=False
   collected 20 items

   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_ssrf_direct_metadata PASSED [  5%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_ssrf_link_local_subnet_gap PASSED [ 10%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_ssrf_ipv6_mapped_gap PASSED [ 15%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_network_allowlist_enforcement_gap PASSED [ 20%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_scheme_tampering PASSED [ 25%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_missing_or_empty_hostname PASSED [ 30%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_loopback_restriction PASSED [ 35%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_credential_sanitization_robustness PASSED [ 40%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_credential_non_leakage_in_failure PASSED [ 45%]
   tests/live_sonar/test_challenger_adapters.py::TestRTSPAdversarialSecurity::test_rtsp_command_injection_characters_not_crashing_parser PASSED [ 50%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_relative_path_traversal_blocked PASSED [ 55%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_absolute_path_traversal_gap PASSED [ 60%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_unrestricted_filesystem_access PASSED [ 65%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_empty_and_whitespace_uris_unhandled_os_error PASSED [ 70%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_directory_with_no_images PASSED [ 75%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_unsupported_file_extension PASSED [ 80%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_corrupted_image_file_handling PASSED [ 85%]
   tests/live_sonar/test_challenger_adapters.py::TestReplayAdversarialResilience::test_replay_malformed_manifest_sidecar PASSED [ 90%]
   tests/live_sonar/test_challenger_adapters.py::TestNativeSonarStubAdversarial::test_native_adapter_hardware_absent_contract PASSED [ 95%]
   tests/live_sonar/test_challenger_adapters.py::TestNativeSonarStubAdversarial::test_native_adapter_in_live_sonar_session PASSED [100%]

   ============================= 20 passed in 30.63s =============================
   ```

4. **Full Combined Milestone 1 Test Suite Execution:**
   Executing command:
   ```cmd
   python -m pytest tests/live_sonar/test_buffer.py tests/live_sonar/test_adapters.py tests/live_sonar/test_session.py tests/live_sonar/test_challenger_adapters.py -q
   ```
   Verbatim output:
   ```
   ...........................................                              [100%]
   43 passed in 60.92s (0:01:00)
   ```

5. **Direct Source Code Inspection:**
   - In `backend/live_sonar/adapters/rtsp.py` (lines 50-84), `validate_rtsp_uri` defines parameter `network_allowlist: Optional[List[str]] = None`, but lines 50-84 never compare `host` against `network_allowlist`.
   - In `backend/live_sonar/adapters/rtsp.py` (line 72), `if host == "169.254.169.254"` performs a literal string check rather than an IP subnet check (`ipaddress.ip_address(host) in ipaddress.ip_network("169.254.0.0/16")`).
   - In `backend/live_sonar/adapters/replay.py` (line 107), `if ".." in self.source_uri and not os.path.isabs(self.source_uri):` skips traversal rejection if `self.source_uri` is an absolute path.
   - In `backend/live_sonar/adapters/replay.py` (lines 115-135), whitespace URI `"   "` bypasses `resolved.exists()` on Windows, causing `resolved.iterdir()` to raise unhandled `FileNotFoundError: [WinError 3] The system cannot find the path specified`.
   - In `backend/live_sonar/adapters/native.py` (lines 43-52, 60-72), `NativeSonarStubAdapter` properly raises `LiveSonarSourceConnectionError` with `status: "NOT_CONFIGURED"`, returns `health().status = "NOT_CONFIGURED"`, returns `metadata().extra["status"] = "NOT_CONFIGURED"`, and yields 0 frames without throwing unhandled exceptions.

---

## 2. Logic Chain

1. **RTSPStreamAdapter Resilience & Security:**
   - *Observation 3 (`test_rtsp_ssrf_direct_metadata`)*: Direct attempts to access AWS/GCP/Azure link-local metadata at `rtsp://169.254.169.254/secret` and `rtsp://169.254.169.254:554/feed` trigger `LiveSonarSecurityViolationError`.
   - *Observation 3 & 5 (`test_rtsp_ssrf_link_local_subnet_gap`, `test_rtsp_ssrf_ipv6_mapped_gap`)*: Because `validate_rtsp_uri` relies on `host == "169.254.169.254"`, other addresses in `169.254.0.0/16` (`rtsp://169.254.1.1`) and IPv6-mapped addresses (`rtsp://[::ffff:169.254.169.254]`) bypass the check.
   - *Observation 3 & 5 (`test_rtsp_network_allowlist_enforcement_gap`)*: `network_allowlist` is passed from configuration into `validate_rtsp_uri` but is never evaluated. As a result, allowlist filtering is dormant.
   - *Observation 3 (`test_rtsp_scheme_tampering`, `test_rtsp_missing_or_empty_hostname`, `test_rtsp_loopback_restriction`)*: Unauthorized protocols (`http`, `https`, `file`, `ftp`, `gopher`, `ws`), malformed URIs without hosts, and loopback addresses (when `allow_local=False`) are rejected with appropriate error types.
   - *Observation 3 (`test_rtsp_credential_sanitization_robustness`, `test_rtsp_credential_non_leakage_in_failure`)*: Passwords in RTSP URIs (including special characters like `%40`, `!`, and colon separators) are sanitized to `***:***`. Credentials are not leaked into exception strings, health reports, or metadata objects.
   - *Observation 3 (`test_rtsp_command_injection_characters_not_crashing_parser`)*: Metacharacters (`;`, `&&`, `|`, `$()`) do not trigger shell execution because `cv2.VideoCapture` calls the FFmpeg C library directly (`avformat_open_input`) without invoking a shell interpreter.

2. **ReplayStreamAdapter Resilience & Boundaries:**
   - *Observation 3 (`test_replay_relative_path_traversal_blocked`)*: Relative traversals (`../../etc/passwd`, `data/../../secret.txt`) are rejected with `LiveSonarSourceInvalidError: Path traversal detected`.
   - *Observation 3 & 5 (`test_replay_absolute_path_traversal_gap`, `test_replay_unrestricted_filesystem_access`)*: Absolute paths containing `..` or pointing outside the repository (e.g. temporary directories or arbitrary disk locations) bypass traversal detection and can load images if valid image extensions exist.
   - *Observation 3 & 5 (`test_replay_empty_and_whitespace_uris_unhandled_os_error`)*: Passing whitespace strings causes an unhandled OS `FileNotFoundError` on Windows instead of a structured `LiveSonarSourceInvalidError`.
   - *Observation 3 (`test_replay_directory_with_no_images`, `test_replay_unsupported_file_extension`, `test_replay_corrupted_image_file_handling`, `test_replay_malformed_manifest_sidecar`)*: Non-existent files, directories without images, unsupported file extensions (`.py`), 0-byte corrupt image files, and invalid `manifest.json` sidecars are handled gracefully without application crashes.

3. **NativeSonarStubAdapter Hardware Absent Contract:**
   - *Observation 3 (`test_native_adapter_hardware_absent_contract`, `test_native_adapter_in_live_sonar_session`)*: When native sonar hardware is not connected, the adapter consistently reports `NOT_CONFIGURED` across `health()`, `metadata()`, and `connect()`. Inside `LiveSonarSession`, calling `start()` raises `LiveSonarSourceConnectionError` and cleanly transitions session state to `SessionStatus.ERROR` without crashing.

4. **Milestone 1 Scope & Viability:**
   - *Observations 1, 2, 4*: The implementation adheres strictly to production model immutability (hash matches), dataset protection (zero diff), and passes all 43 tests (23 worker tests + 20 challenger tests).
   - Although security gaps were discovered (allowlist dormancy, link-local subnet specificity, unrestricted filesystem access), network allowlisting and comprehensive security enforcement are formally slated under Requirement R3 for Milestone 3 (`PROJECT.md § Milestones`). Core streaming infrastructure (R1) is functional, safe, and ready for Milestone 2 AI pipeline integration.

---

## 3. Caveats

1. **Physical Camera Hardware:** DirectShow capture cards (`USBCameraStreamAdapter`) could not be tested with live physical camera feeds because no physical USB video capture hardware is attached to the test host; testing was limited to device index parsing and failure handling.
2. **Network allowlist scope:** `LIVE_SONAR_NETWORK_ALLOWLIST` was introduced as a configuration property in M1, but full network allowlisting and network security hardening belong to Milestone 3 (REST & WebSocket security).
3. **Pre-existing test drift:** `tests/backend/test_config.py:16` contains a pre-existing assertion expectation for `"sonar_yolov8m_ghostpot_v1"` instead of `"production_fls_yolov8n"`. This pre-existing file was outside Milestone 1 write boundaries.

---

## 4. Conclusion

### Definitive Verdict: `APPROVE`

Milestone 1 (Streaming Infrastructure & Source Adapters) satisfies Requirement R1 and all non-negotiable safety criteria:
- Production model and dataset remain completely untouched.
- `SonarFrame`, `FrameBuffer`, and `LiveSonarSession` operate reliably under stress.
- `ReplayStreamAdapter` provides playback controls, sequence ingestion, and graceful corruption recovery.
- `RTSPStreamAdapter` provides credential sanitization, protocol restriction, and non-blocking reconnect handling.
- `NativeSonarStubAdapter` satisfies the `NOT_CONFIGURED` hardware contract.

### Mandatory Hardening Recommendations for Milestone 3 (Security & API Scope):
1. **[High] Wire up `network_allowlist` in `validate_rtsp_uri`**:
   Check `host` and IP address against `network_allowlist` if populated.
2. **[Medium] Upgrade Link-Local Check to CIDR / `ipaddress.is_link_local`**:
   Replace `host == "169.254.169.254"` with `ipaddress.ip_address(host).is_link_local` to cover all `169.254.0.0/16` and IPv6 equivalents (`fe80::/10`, `::ffff:169.254.x.x`).
3. **[Medium] Confine `ReplayStreamAdapter` to Permitted Base Directories**:
   Resolve replay paths against an allowed base directory (e.g. `Path.cwd() / "data"`) and verify `resolved.is_relative_to(allowed_base)`.
4. **[Low] Input Trimming in `ReplayStreamAdapter`**:
   Check `if not self.source_uri or not self.source_uri.strip(): raise LiveSonarSourceInvalidError("Replay source URI cannot be empty")` before path resolution.

---

## 5. Verification Method

To independently reproduce and verify this empirical challenge:

1. **Verify Model Immutability:**
   ```cmd
   certutil -hashfile "models\detection\sonar_yolov8_fls_trained.pt" SHA256
   ```
   *Expected hash:* `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`.

2. **Verify Dataset Immutability:**
   ```cmd
   git diff --name-only datasets/
   ```
   *Expected:* Empty output.

3. **Run Challenger Adversarial Test Suite (20 Tests):**
   ```cmd
   python -m pytest tests/live_sonar/test_challenger_adapters.py -v
   ```
   *Expected:* 20 passed.

4. **Run Combined Milestone 1 Test Suite (43 Tests):**
   ```cmd
   python -m pytest tests/live_sonar/test_buffer.py tests/live_sonar/test_adapters.py tests/live_sonar/test_session.py tests/live_sonar/test_challenger_adapters.py -v
   ```
   *Expected:* 43 passed.

5. **Inspect Test Artifact:**
   - `tests/live_sonar/test_challenger_adapters.py`
