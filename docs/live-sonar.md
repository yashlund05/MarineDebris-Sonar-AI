# MarineDebris-Sonar-AI: Live Sonar AI Detection & Tracking Guide

## Overview
The **Live Sonar AI** subsystem adds continuous real-time acoustic frame streaming, preprocessing, YOLOv8 debris detection, ByteTrack temporal identity tracking, and forensic evidence generation to `MarineDebris-Sonar-AI`.

---

## Key Features

1. **Pluggable Source Adapters**:
   - `ReplayAdapter`: Deterministic file replay (`.mp4`, `.mkv`, `.avi`, XTF, PNG sequences). Replay shares the exact same inference and tracking code path as live streams.
   - `RtspAdapter`: Robust RTSP H.264/H.265 network stream consumer with auto-reconnection.
   - `UsbAdapter`: Direct UVC video capture device consumer.
   - `NativeSonarStub`: Vendor-specific interface placeholder (e.g. ARIS/DIDSON) with `NOT_CONFIGURED` status when SDK is absent.

2. **Bounded Asynchronous Frame Buffer**:
   - Backpressure management with configurable drop policies (`DROP_OLDEST`, `FIFO`, `DROP_NEWEST`, `LATEST`).
   - Prevents memory leaks and latency buildup.

3. **Temporal Tracking & Confirmation**:
   - Two-stage association ByteTrack algorithm maintaining consistent `track_id` over time.
   - $N$-of-$M$ confirmation filter eliminates single-frame false positives.
   - Class majority voting prevents label flickering.

4. **Acoustic Shadow Reasoning & Georeferencing**:
   - Evaluates down-range acoustic shadow backscatter behind confirmed targets.
   - Associates navigation telemetry with detection coordinates adhering to the strict Zero-Fabrication Contract (`NOT_AVAILABLE` when sensor lock is missing).

5. **Multi-View Decoupled Canvas Viewport**:
   - View modes: `RAW`, `ENHANCED`, `AI`, `SPLIT`.
   - Trajectory polyline rendering, track ID badges, confidence percentages.
   - High-contrast `LIVE` vs `REPLAY` stream status.

6. **Forensic Evidence Capture & Recording**:
   - Automatically saves 4-layer crop artifacts (`raw_crop`, `processed_crop`, `annotated_crop`, `metadata.json`) upon target confirmation.
   - Supports manual snapshot capture and full session video/JSONL telemetry recording.

---

## API Reference

### REST Endpoints
- `POST /api/v1/live-sonar/sessions`: Create new session
- `GET /api/v1/live-sonar/sessions`: List active sessions
- `GET /api/v1/live-sonar/sessions/{id}`: Get session details and metrics
- `POST /api/v1/live-sonar/sessions/{id}/start`: Start stream acquisition
- `POST /api/v1/live-sonar/sessions/{id}/stop`: Stop stream acquisition
- `GET /api/v1/live-sonar/sessions/{id}/metrics`: Real-time FPS, queue depth, drop rate
- `GET /api/v1/live-sonar/sessions/{id}/tracks`: Active temporal tracks
- `GET /api/v1/live-sonar/sessions/{id}/detections`: Latest frame detections
- `GET /api/v1/live-sonar/sessions/{id}/evidence`: Captured forensic evidence items
- `POST /api/v1/live-sonar/sessions/{id}/snapshot`: Manually capture evidence snapshot
- `GET /api/v1/live-sonar/health`: System health, device status, model load status

### WebSocket Endpoint
- `ws://localhost:8000/api/v1/ws/live-sonar/{session_id}` (or `/ws/live-sonar/{session_id}`)
  - Client actions: `{"action": "pause"}`, `{"action": "resume"}`, `{"action": "speed", "value": 2.0}`, `{"action": "snapshot", "track_id": 1}`
  - Server events: `frame_result` (with JPEG preview and telemetry), `session_connected`, `command_ack`, `error`
