# Handoff Report: Backend Live Sonar Specification Mining

**Agent:** `teamwork_preview_spec_miner_backend_1`  
**Task:** Backend Architecture Specification Mining (R1, R2, R3, R5)  
**Deliverable:** `c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_backend_1\spec_backend.md`  
**Date:** 2026-09-19  

---

## 1. Observation

Direct observations from codebase inspection, specifications, and tool execution:

1. **Safety Constraints Verification:**
   - Command: `Get-FileHash "models\detection\sonar_yolov8_fls_trained.pt" -Algorithm SHA256`
   - Output: `E1215C7E7F6E4F3722398BF93D975EB5013C49F78355D0D5F54CE982D495B3D7` (Matches required checksum byte-identically).
   - Command: `git status --short datasets/`
   - Output: Empty (no changes to frozen datasets or annotations).
   - Test execution: `& "C:\Users\ARYAN - AYUSH\AppData\Local\Python\bin\python.exe" -m pytest tests/backend/test_health.py`
   - Output: `2 passed in 1.34s` (Confirmed operational test suite and database).

2. **Existing Architecture & Ingestion vs. Live Stream:**
   - In `backend/sonar_parser/models.py:41-50`, `SonarFrame` represents a multi-ping chunk of an offline survey (`chunk_index`, `ping_offset`, `pings: list[SonarPing]`).
   - In `ARCHITECTURAL_BLUEPRINT.md:153-193`, survey processing assumes batch files (XTF/PNG) processed via Celery task chunking.
   - In `PRD.md:143`, live sensor feed streaming ingestion was previously marked "Out-of-Scope (batch file upload only)".
   - In `ORIGINAL_REQUEST.md:50-75`, Requirement R1 explicitly introduces the live streaming pipeline with bounded queue, backpressure, and source adapters.

3. **Inference & Preprocessing Reuse:**
   - In `backend/inference/detector.py:35-98`, `detect_tiles(tiles, model, conf_threshold, device)` runs under `torch.inference_mode()`, supporting raw numpy arrays or tile structures with `RawDetection` dataclasses.
   - In `backend/inference/model_loader.py:104-110`, `ModelLoader.get_detection_model()` provides a singleton instance initialized from `settings.DETECTION_MODEL_PATH`.
   - In `backend/preprocessing/pipeline.py:16-73`, `preprocess_frame()` executes a sequential chain (`assess_quality` $\to$ `detect_bottom` $\to$ `remove_water_column` $\to$ `normalize` $\to$ `apply_clahe` $\to$ `denoise` $\to$ `correct_slant_range` $\to$ `generate_tiles`).
   - In `backend/enhancement/profiles.py:16-98`, `PROFILE_REGISTRY` contains enhancement methods (Bilateral CLAHE, Log-Bilateral CLAHE, Unsharp CLAHE, Median CLAHE).

4. **WebSocket & Pub/Sub Pattern:**
   - In `backend/api/routers/ws.py:13-63`, existing WebSocket connects via `redis.asyncio.from_url(settings.celery_broker, protocol=2)`, subscribes to `job_progress:{job_id}`, and forwards text messages to the client.
   - In `backend/tasks.py:15-44`, progress events are published to Redis using `json.dumps(event)` with timestamps and status strings.

5. **Database & Migrations Lineage:**
   - Existing models in `backend/database/models.py`: `Survey`, `SonarMetadata`, `ProcessingJob`, `Detection`, `Report`, `ModelRegistry`.
   - Alembic revisions in `backend/database/migrations/versions/`:
     - `0001_initial_schema.py`
     - `0002_ml_segmentation_classification.py` (down_revision: `0001_initial_schema`)

6. **Test Sonar Data:**
   - `data/test_sonar_images/` contains real ARIS 3000 forward-looking sonar images (`marine-debris-aris3k-*.png`) with YOLO ground-truth annotations and `manifest.json`.

---

## 2. Logic Chain

1. **Need for Modular Live Ingestion Layer:**
   - Since `SonarFrame` in `backend/sonar_parser/models.py` is structured for offline ping batches, a dedicated live `SonarFrame` (representing a single 2D acoustic frame/sweep) is required in `backend/live_sonar/models.py`.
   - By creating `SonarStreamAdapter` as an ABC with concrete implementations (`ReplayStreamAdapter`, `RTSPStreamAdapter`, `USBCameraStreamAdapter`, `NativeSonarStubAdapter`), acquisition is decoupled from inference, allowing any source to drive the pipeline identically.

2. **Memory Safety & Backpressure Control:**
   - Live streams can generate 15--30 FPS, while YOLOv8 inference latency varies by device (CPU: ~100ms, GPU: ~15ms).
   - An unbounded queue risks memory exhaustion (OOM). A bounded queue with policy `DROP_OLDEST` ensures memory is bounded ($N \le 60$), latency is minimized, and backpressure metrics (`input_fps`, `processing_fps`, `queue_depth`, `frames_dropped`) are truthfully exposed.

3. **Inference Decoupling & ByteTrack Integration:**
   - Running inference synchronously in the WebSocket or frame acquisition loop would cause frame stutter and blocking. An independent inference worker loop with dynamic frame skipping maintains responsive display framerates while tracking across frames.
   - ByteTrack's two-stage association is mathematically ideal for sonar: Stage 1 associates high-confidence targets, while Stage 2 associates low-confidence detections against active Kalman tracks, preventing track fragmentation during acoustic multipath fading or speckle dropouts.
   - Requiring $N$-of-$M$ (e.g. 3 of 5) observed frames before confirmation suppresses false alarm spikes without missing legitimate debris.

4. **Network & Web Architecture:**
   - Transmitting full $1024\times 1024$ float32 frames ($4\text{ MB}$) over WebSocket would quickly saturate bandwidth at 15 FPS ($60\text{ MB/s}$).
   - Transmitting a compressed JPEG/WebP preview ($< 80\text{ KB}$) together with detection bboxes and track trajectories reduces bandwidth by $>98\%$, fitting well within standard network limits.
   - Using Redis pub/sub on channel `live_sonar:{session_id}` mirrors the battle-tested pattern in `backend/api/routers/ws.py`.

5. **Persistence & Database Lineage:**
   - To avoid modifying existing survey tables, four new models (`LiveSonarSession`, `LiveTrack`, `LiveDetectionEvent`, `LiveEvidence`) must be created in `backend/database/models.py` with clean foreign keys.
   - Alembic migration `0003_live_sonar_subsystem.py` will increment from `0002_ml_segmentation_classification`, maintaining schema integrity and enabling complete rollback.

---

## 3. Caveats

1. **Hardware Dependencies:**
   - Physical ARIS / DIDSON sonar hardware was not connected to the test machine; therefore, `NativeSonarStubAdapter` is specified to report `status="NOT_CONFIGURED"` and raise structured errors rather than fabricating live data.
2. **GPU Availability:**
   - The test environment evaluated on CPU; the specification explicitly mandates dual CUDA and CPU fallback testing to guarantee zero failure modes when deployed without an NVIDIA GPU.
3. **No Code Written Outside Working Directory:**
   - In accordance with the dispatch assignment and Specification Miner role, no implementation code was created outside the `.agents/teamwork_preview_spec_miner_backend_1/` directory.

---

## 4. Conclusion

The specification investigation successfully mapped all backend requirements (R1, R2, R3, R5). The complete architecture, data models, adapter interfaces, preprocessing profiles, tracking algorithms, WebSocket schemas, REST endpoints, database tables, and security controls are comprehensively documented in:
`c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_backend_1\spec_backend.md`

All existing codebase patterns and safety invariants (model SHA256 immutability, frozen dataset protection, no fabricated data, and backward compatibility) have been preserved.

---

## 5. Verification Method

1. **Verify Model Integrity:**
   ```powershell
   Get-FileHash "models\detection\sonar_yolov8_fls_trained.pt" -Algorithm SHA256
   # Must return: E1215C7E7F6E4F3722398BF93D975EB5013C49F78355D0D5F54CE982D495B3D7
   ```
2. **Verify Dataset Cleanliness:**
   ```powershell
   git status --short datasets/
   # Must return empty
   ```
3. **Verify Existing Backend Tests:**
   ```powershell
   & "C:\Users\ARYAN - AYUSH\AppData\Local\Python\bin\python.exe" -m pytest tests/backend/test_health.py
   # Must pass
   ```
4. **Inspect Specification Deliverable:**
   ```powershell
   Get-Content "c:\Users\ARYAN - AYUSH\OneDrive\Desktop\Marine sonar\.agents\teamwork_preview_spec_miner_backend_1\spec_backend.md" -TotalCount 50
   ```
