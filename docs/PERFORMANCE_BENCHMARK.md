# MarineDebris-Sonar-AI: Performance Benchmark

**Benchmark Date:** 2026-09-01  
**Auditor:** Principal Backend & ML Infrastructure Engineer  
**Hardware Environment:** Windows 11 (win32), Python 3.14.6  
**Execution Command:** `python -m scripts.benchmark_pipeline`  

---

## 1. Empirical Algorithmic Micro-Benchmarks

Measured on a standard acoustic sonar waterfall strip of **2,000 pings × 1,024 samples** (7.81 MB float32 array):

| Pipeline Stage | Measured Latency | Throughput / Operational Details |
| :--- | :--- | :--- |
| **Quality Assessment** | `0.93 ms` | Per-ping dropout analysis & motion attitude check |
| **Bottom Line Detection** | `28.23 ms` | Intensity thresholding with gradient fallback |
| **Water Column Removal** | `2.12 ms` | Geometric nadir column masking |
| **Intensity Normalization** | `9.43 ms` | Min-max dynamic range scaling (0.0 to 1.0) |
| **CLAHE Enhancement** | `36.23 ms` | Tile grid (8x8) contrast-limited adaptive equalization |
| **Median Denoising** | `6.41 ms` | $3 \times 3$ kernel noise suppression |
| **Tile Grid Slicing (640×640)** | `8.86 ms` | 8 overlapping acoustic tiles generated |
| **Total Preprocessing Turnaround** | **`92.21 ms`** | **~21,690 pings/sec throughput** |

---

## 2. Post-Processing & Geodesy Benchmarks

Measured across 100 raw candidates:

| Post-Processing Stage | Measured Latency | Notes |
| :--- | :--- | :--- |
| **Global Coordinate NMS** | `0.45 ms` | Cross-tile IoU deduplication ($IoU \ge 0.45$) |
| **Bounding Box Area Filter** | `0.01 ms` | Min/max pixel area constraint validation |
| **Temperature Calibration** | `0.03 ms` | Sigmoid logit scaling ($T = 1.4$) |
| **WGS84 Geodesy (100 points)** | `0.10 ms` | Great-circle bearing and distance projection |

---

## 3. Reporting Export Benchmarks

Measured on a 50-detection survey session:

| Export Format | Measured Latency | Output Payload Characteristics |
| :--- | :--- | :--- |
| **JSON Report Generation** | `1.43 ms` | Structured envelope with survey metadata |
| **CSV Report Generation** | `0.72 ms` | RFC 4180 tabular rows with bounding boxes |
| **GeoJSON FeatureCollection** | `2.10 ms` | WGS84 Point geometry (`[lon, lat]` ordering) |

---

## 4. Full End-to-End System Turnaround (E2E)

Measured via automated test `test_full_backend_e2e_pipeline`:
- **Total Pipeline Execution Time:** `5.64 s` for a 1,000-ping survey.
- **Scope:** HTTP upload -> File validation -> Storage disk write -> Database session creation -> Celery task dispatch -> 11-stage processing pipeline -> Detections persistence -> Report exports -> Cascade cleanup.

---

## 5. ML Inference Projection (Real vs. Synthetic Separation)
- **Synthetic/Test Execution:** In the absence of trained YOLOv8 weights, the detector returns 0 detections in `~0.01 ms`, allowing full pipeline execution without fabricating predictions.
- **Projected YOLOv8m Inference (Real Weights):**
  - **CUDA (NVIDIA RTX 3060+):** ~12–18 ms per 640×640 tile (Batch size 8: ~120 ms per chunk).
  - **CPU (Intel/AMD 8-Core):** ~140–220 ms per 640×640 tile.
