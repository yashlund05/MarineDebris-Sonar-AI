# API_SPEC.md
## MarineDebris-Sonar-AI — API Specification

**Base URL:** `http://localhost:8000/api/v1`  
**Framework:** FastAPI (OpenAPI docs auto-generated at `/docs`)  
**Auth:** None in V1 (internal deployment). JWT bearer in V2.  
**Content-Type:** `application/json` unless noted (file uploads use `multipart/form-data`)  
**Version:** 1.0 — August 2026  

---

## 1. Global Response Envelope

All JSON responses follow a consistent envelope:

**Success:**
```json
{
  "success": true,
  "data": { ... },
  "meta": { "request_id": "uuid", "timestamp": "ISO8601" }
}
```

**Error:**
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable description",
    "details": { ... }
  },
  "meta": { "request_id": "uuid", "timestamp": "ISO8601" }
}
```

---

## 2. Standard Error Codes

| HTTP Status | Error Code | Meaning |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Request payload failed validation |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Resource already exists or state conflict |
| 413 | `FILE_TOO_LARGE` | Upload exceeds 2 GB limit |
| 415 | `UNSUPPORTED_FILE_TYPE` | File type not accepted |
| 422 | `UNPROCESSABLE_ENTITY` | Semantically invalid input |
| 500 | `INTERNAL_ERROR` | Unhandled server error |
| 503 | `WORKER_UNAVAILABLE` | Celery worker is not reachable |

---

## 3. Surveys

### `POST /api/v1/surveys/upload`

Upload a raw sonar file and enqueue processing.

**Request:** `multipart/form-data`
```
file         : binary (required) — XTF, JSF, PNG, or TIFF sonar file
nav_csv      : binary (optional) — Navigation CSV for PNG uploads lacking embedded nav
channel      : string (optional) — "port" | "starboard" | "both" — default: "starboard"
```

**Validation:**
- `file` must be present.
- MIME type must be one of: `application/octet-stream` (XTF/JSF), `image/png`, `image/tiff`.
- File extension must be `.xtf`, `.jsf`, `.png`, `.tif`, or `.tiff`.
- File size must not exceed `MAX_UPLOAD_SIZE_MB` (default 2048 MB).
- **Format support tier (see `PRD.md` §4.1):** `.xtf` and `.png` have full parser support at MVP. `.jsf`, `.tif`, and `.tiff` are accepted by this endpoint and stored (so the API/DB contract does not need to change later), but parsing for these formats is deferred to V1 — an upload of a currently-unparsed format is accepted (HTTP 201) with `status: "queued"`, then the pipeline surfaces an explicit `job_failed` event (§5) with a clear "format not yet supported" error rather than silently producing empty results.

**Response 201:**
```json
{
  "success": true,
  "data": {
    "survey_id": "uuid",
    "job_id": "uuid",
    "status": "queued",
    "source_filename": "survey_01.xtf",
    "file_size_bytes": 52428800,
    "created_at": "2026-08-31T10:00:00Z"
  }
}
```

**Response 413:**
```json
{
  "success": false,
  "error": {
    "code": "FILE_TOO_LARGE",
    "message": "File size 2.5 GB exceeds the 2 GB limit."
  }
}
```

---

### `GET /api/v1/surveys`

List all surveys, newest first.

**Query Parameters:**
```
status   : string (optional) — Filter by status value
limit    : integer (optional, default 20, max 100)
offset   : integer (optional, default 0)
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "surveys": [
      {
        "survey_id": "uuid",
        "source_filename": "survey_01.xtf",
        "status": "complete",
        "channel": "starboard",
        "created_at": "2026-08-31T10:00:00Z",
        "processing_completed_at": "2026-08-31T10:04:22Z",
        "detection_count": 14
      }
    ],
    "total": 1,
    "limit": 20,
    "offset": 0
  }
}
```

---

### `GET /api/v1/surveys/{survey_id}`

Get full detail for one survey including metadata and latest job.

**Path Parameters:** `survey_id` — UUID

**Response 200:**
```json
{
  "success": true,
  "data": {
    "survey_id": "uuid",
    "source_filename": "survey_01.xtf",
    "file_type": "xtf",
    "status": "complete",
    "channel": "starboard",
    "created_at": "...",
    "processing_started_at": "...",
    "processing_completed_at": "...",
    "sonar_metadata": {
      "frequency_hz": 600000,
      "samples_per_ping": 1024,
      "total_pings": 3200,
      "range_resolution_m": 0.07,
      "along_track_resolution_m": 0.15,
      "min_latitude": 38.80,
      "max_latitude": 38.85,
      "min_longitude": -75.14,
      "max_longitude": -75.10,
      "sonar_system": "Klein 3500"
    },
    "latest_job": { ... }
  }
}
```

**Response 404:** Survey not found.

---

### `DELETE /api/v1/surveys/{survey_id}`

Delete a survey and all associated jobs, detections, and report files.

**Response 200:**
```json
{ "success": true, "data": { "deleted": true } }
```

---

## 4. Processing Jobs

### `GET /api/v1/jobs/{job_id}`

Get job status and progress.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "job_id": "uuid",
    "survey_id": "uuid",
    "celery_task_id": "celery-uuid",
    "status": "inferring",
    "progress_pct": 62,
    "current_stage": "Running YOLOv8 detection on tiles 400/648",
    "detection_model": "sonar_yolov8m_ghostpot_v1",
    "detection_model_version": "1.0.0",
    "detection_conf_threshold": 0.35,
    "created_at": "...",
    "updated_at": "..."
  }
}
```

---

### `POST /api/v1/surveys/{survey_id}/reprocess`

Reprocess a completed survey with different model settings.

**Request Body:**
```json
{
  "detection_conf_threshold": 0.45,
  "nms_iou_threshold": 0.50,
  "run_segmentation": true
}
```

**Validation:**
- `detection_conf_threshold`: float, 0.1–0.95
- `nms_iou_threshold`: float, 0.1–0.95
- `run_segmentation`: boolean, optional (default false)

**Response 201:**
```json
{
  "success": true,
  "data": { "job_id": "uuid", "status": "queued" }
}
```

---

## 5. WebSocket — Job Progress

### `WS /api/v1/ws/jobs/{job_id}`

Real-time job progress updates. The server pushes JSON frames on every pipeline stage change. Internally, the Celery worker publishes progress to a Redis pub/sub channel and this FastAPI WebSocket route subscribes and relays matching events to the connected client — the Celery worker never holds a WebSocket connection itself (see `ARCHITECTURAL_BLUEPRINT.md` §2). The database row (`processing_jobs.status`/`progress_pct`) remains authoritative if a client misses a WS frame; `GET /api/v1/jobs/{job_id}` can always be polled as a fallback.

**Message Schema (server → client):**
```json
{
  "event": "job_progress",
  "job_id": "uuid",
  "status": "preprocessing",
  "progress_pct": 18,
  "current_stage": "Applying CLAHE and denoising",
  "timestamp": "2026-08-31T10:01:05Z"
}
```

**Terminal events:**
```json
{ "event": "job_complete", "job_id": "uuid", "detection_count": 14 }
{ "event": "job_failed", "job_id": "uuid", "error": "Sonar file corrupt at ping 1042" }
```

---

## 6. Detections

### `GET /api/v1/surveys/{survey_id}/detections`

Retrieve all detections for a survey (from the latest completed job by default).

**Query Parameters:**
```
job_id         : uuid (optional) — Override to fetch detections from a specific job
class_name     : string (optional) — Filter by class
min_confidence : float (optional, 0.0–1.0) — Minimum calibrated confidence
include_filtered : boolean (optional, default false) — Include suppressed detections
limit          : integer (optional, default 100, max 1000)
offset         : integer (optional, default 0)
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "survey_id": "uuid",
    "job_id": "uuid",
    "detections": [
      {
        "detection_id": "uuid",
        "detection_code": "D000001",
        "class_name": "derelict_fishing_gear",
        "confidence": 0.87,
        "confidence_calibrated": 0.83,
        "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
        "mask_rle": null,
        "estimated_length_m": 3.2,
        "estimated_width_m": 1.1,
        "geotagging_available": true,
        "latitude": 38.812345,
        "longitude": -75.134567,
        "ping_number": 1042,
        "ping_timestamp": 1722412815.4,
        "is_filtered": false,
        "filtered_reason": null,
        "processing": {
          "preprocessing_version": "v1.0",
          "detection_model": "sonar_yolov8m_ghostpot_v1",
          "detection_model_version": "1.0.0"
        }
      }
    ],
    "total": 14,
    "filtered_count": 3
  }
}
```

All model names, confidence values, and coordinates in this document are illustrative/mock example data unless stated otherwise.

---

### `GET /api/v1/detections/{detection_id}`

Get full detail for one detection including tile image path.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "detection_id": "uuid",
    "detection_code": "D000001",
    "class_name": "derelict_fishing_gear",
    "confidence": 0.87,
    "confidence_calibrated": 0.83,
    "bbox": {"x": 314, "y": 220, "w": 68, "h": 44},
    "mask_rle": null,
    "estimated_length_m": 3.2,
    "estimated_width_m": 1.1,
    "geotagging_available": true,
    "latitude": 38.812345,
    "longitude": -75.134567,
    "ping_number": 1042,
    "ping_timestamp": 1722412815.4,
    "is_filtered": false,
    "filtered_reason": null,
    "source_tile_url": "/api/v1/tiles/survey-uuid/tile_row4_col2.png",
    "processing": { ... }
  }
}
```

---

## 7. Sonar Image Viewer

### `GET /api/v1/surveys/{survey_id}/sonar-image`

Returns the processed sonar image (post-preprocessing) as PNG for the sonar viewer. For large surveys, returns a downsampled preview.

**Query Parameters:**
```
channel     : string — "port" | "starboard"
mode        : string — "raw" | "processed" (default: "processed")
max_height  : integer (optional, default 4096) — Max pixel height for preview
```

**Response 200:** `Content-Type: image/png` — Binary PNG stream.

---

### `GET /api/v1/tiles/{survey_id}/{tile_filename}`

Serve a specific sonar tile PNG for detection detail view.

**Response 200:** `Content-Type: image/png`

---

## 8. Reports

### `GET /api/v1/surveys/{survey_id}/reports`

List all exported reports for a survey.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "reports": [
      {
        "report_id": "uuid",
        "format": "geojson",
        "detection_count": 14,
        "file_size_bytes": 8192,
        "created_at": "...",
        "download_url": "/api/v1/reports/uuid/download"
      }
    ]
  }
}
```

---

### `POST /api/v1/surveys/{survey_id}/reports/generate`

Trigger report generation for a specific format.

**Request Body:**
```json
{
  "format": "geojson",
  "job_id": "uuid",
  "min_confidence": 0.4,
  "include_filtered": false
}
```

**Validation:**
- `format`: one of `"json"`, `"csv"`, `"geojson"` (required)
- `min_confidence`: float 0.0–1.0 (optional, default 0.0)
- `include_filtered`: boolean (optional, default false)

**Response 201:**
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "format": "geojson",
    "download_url": "/api/v1/reports/uuid/download"
  }
}
```

---

### `GET /api/v1/reports/{report_id}/download`

Download the report file.

**Response 200:**  
- For JSON: `Content-Type: application/json`  
- For CSV: `Content-Type: text/csv`  
- For GeoJSON: `Content-Type: application/geo+json`  

`Content-Disposition: attachment; filename="survey_detections.geojson"`

---

## 9. Model Registry

Model names, versions, and metric values throughout this section are illustrative/mock placeholders (see `DB_SCHEMA.md` §4) until a real model has been trained and registered.

### `GET /api/v1/models`

List all registered models.

**Query Parameters:**
```
task : string (optional) — "detection" | "segmentation" | "edge_detection"
```

**Response 200:**
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model_id": "uuid",
        "model_name": "sonar_yolov8m_ghostpot_v1",
        "version": "1.0.0",
        "task": "detection",
        "architecture": "yolov8m",
        "training_dataset": "ghost_pot_sss,subpipe",
        "map50": 0.724,
        "map50_95": 0.481,
        "inference_latency_ms": 42.3,
        "is_active": true
      }
    ]
  }
}
```

---

## 10. System / Health

### `GET /api/v1/health`

Basic health check.

**Response 200:**
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "worker": "running",
  "active_detection_model": "sonar_yolov8m_ghostpot_v1 v1.0.0",
  "device": "cuda"
}
```

---

### `GET /api/v1/demo/surveys`

Returns a list of pre-loaded demo surveys for demo mode. No upload required.

**Response 200:**
```json
{
  "success": true,
  "data": {
    "demo_surveys": [
      {
        "survey_id": "00000000-0000-0000-0000-000000000001",
        "label": "Delaware Bay — Derelict Fishing Gear Survey (sample)",
        "description": "6 derelict_fishing_gear detections from the PING Ecosystem (Ghost Pot) dataset.",
        "detection_count": 6
      }
    ]
  }
}
```

---

## 11. Report JSON Schema (full)

Field names match `class_name`, `confidence`, `confidence_calibrated` exactly as used in the `GET /surveys/{id}/detections` and `GET /detections/{id}` responses (§6) and the `detections` table in `DB_SCHEMA.md` — this is the one canonical detection representation used everywhere in the system. `confidence` is **Model Confidence** (raw); `confidence_calibrated` is **Final Anomaly Confidence** (after calibration + sonar-aware verification) — see `PRD.md` §1.1. All example values below are illustrative/mock, not a validated result.

```json
{
  "detection_id": "D000123",
  "source_file": "survey_01.xtf",
  "timestamp": "2026-08-31T10:04:11Z",
  "class_name": "derelict_fishing_gear",
  "confidence": 0.94,
  "confidence_calibrated": 0.89,
  "bbox": {"x": 120, "y": 88, "w": 74, "h": 42},
  "estimated_dimensions_m": {"length": 3.4, "width": 1.2},
  "geotagging_available": true,
  "latitude": 38.812345,
  "longitude": -75.134567,
  "processing": {
    "preprocessing": "v1.2",
    "model": "sonar_yolov8m_ghostpot_v1",
    "model_version": "1.0.0"
  }
}
```

Note: `geotagging_available: false` is explicitly set when navigation metadata was absent from the source file, with `latitude`/`longitude` left `null` — coordinates are never fabricated. This same `geotagging_available` field is present on every detection object returned by §6/§7, matching the `detections.geotagging_available` column in `DB_SCHEMA.md`.

---

*End of API_SPEC.md*
