# MarineDebris-Sonar-AI: Live Sonar Operations Manual

## 1. Prerequisites and Setup

### 1.1 Hardware and Dependencies
- **Inference Engine**: CUDA 11.8+ with PyTorch or standard CPU fallback
- **Video Decoders**: OpenCV with FFmpeg bindings for RTSP and replay decoders
- **Database**: PostgreSQL with Alembic migrations applied
- **WebSocket Broker**: Redis (optional pub/sub) or in-process decoupled broadcast queue

---

## 2. Configuration Parameters

The Live Sonar subsystem is configured via environment variables or Pydantic settings:

| Variable | Default | Allowed Values | Description |
| :--- | :--- | :--- | :--- |
| `LIVE_SONAR_ENABLED` | `true` | `true`, `false` | Global feature flag for Live Sonar subsystem |
| `LIVE_SONAR_SOURCE_TYPE` | `replay` | `replay`, `rtsp`, `usb`, `native_stub` | Default input source adapter |
| `LIVE_SONAR_SOURCE_URI` | `""` | URI string | File path, RTSP URL, device index, or stub address |
| `LIVE_SONAR_TARGET_FPS` | `15.0` | `1.0` - `60.0` | Target acquisition frame rate |
| `LIVE_SONAR_INFERENCE_FPS` | `10.0` | `1.0` - `30.0` | Maximum AI detection inference frame rate |
| `LIVE_SONAR_BUFFER_SIZE` | `60` | `4` - `1000` | Maximum frames in async FIFO queue |
| `LIVE_SONAR_DROP_POLICY` | `DROP_OLDEST` | `DROP_OLDEST`, `FIFO`, `DROP_NEWEST`, `LATEST` | Backpressure queue overflow policy |
| `LIVE_SONAR_PREPROCESSING_PROFILE` | `BALANCED` | `REALTIME`, `BALANCED`, `QUALITY` | Sonar image enhancement profile |
| `LIVE_SONAR_CONFIDENCE_THRESHOLD` | `0.35` | `0.05` - `0.99` | Minimum model confidence score |
| `LIVE_SONAR_MIN_CONFIRMED_FRAMES` | `3` | `1` - `20` | $N$-of-$M$ temporal confirmation requirement |

---

## 3. Operational Workflows

### 3.1 Replay Testing (Deterministic Development Workflow)
```bash
# Start backend API service
uvicorn backend.api.main:app --host 0.0.0.0 --port 8000

# Create a deterministic replay session via cURL
curl -X POST http://localhost:8000/api/v1/live-sonar/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Replay Benchmark",
    "source_type": "replay",
    "source_uri": "datasets/benchmarks/synthetic_acoustic_test.mp4",
    "target_fps": 15.0,
    "inference_fps": 10.0
  }'

# Start processing
curl -X POST http://localhost:8000/api/v1/live-sonar/sessions/session_live_demo/start
```

### 3.2 Network RTSP Acoustic Camera Deployment
For topside sonar units streaming over RTSP:
```json
{
  "name": "ROV Forward Looker",
  "source_type": "rtsp",
  "source_uri": "rtsp://192.168.1.100:554/sonar",
  "target_fps": 20.0,
  "inference_fps": 10.0,
  "preprocessing_profile": "BALANCED"
}
```

### 3.3 Target Inspection & Evidence Recovery
Forensic evidence captured by the subsystem is organized under:
`artifacts/evidence/{session_id}/track_{track_id}/`
- `raw_crop.png`
- `processed_crop.png`
- `annotated_crop.png`
- `metadata.json`

---

## 4. Monitoring & Troubleshooting

### 4.1 Backpressure and Dropped Frames
- If `input_fps > inference_fps`, frames in the buffer will drop according to `drop_policy`.
- The operator UI shows an amber `BACKPRESSURE: ADAPTING` badge.
- Mitigate by reducing `target_fps`, reducing preprocessing profile (`REALTIME`), or enabling GPU inference.

### 4.2 Stream Disconnections
- When the acoustic stream fails (network drop, EOF), the subsystem transitions to `CONNECTION_LOST`.
- The UI halts inference, displays `CONNECTION LOST`, shows the timestamp of the last valid frame, and begins automatic reconnection with exponential backoff.
