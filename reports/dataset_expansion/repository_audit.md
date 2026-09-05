# Repository Audit — MarineDebris-Sonar-AI Dataset Pipeline & Architecture

**Date:** 2026-09-04  
**Auditor:** Senior ML Dataset Engineer / Anti-Fabrication Quality System  
**Status:** Completed  

---

## 1. Executive Summary

This repository audit inspects all dataset, machine learning, API, test, and frontend components of **MarineDebris-Sonar-AI** prior to initiating the Dataset V3 expansion. The objective is to identify existing reusable modules, document current dataset formats and flows, and define clean integration points without creating parallel or redundant infrastructure.

---

## 2. Current Dataset Architecture & Data Flow

The current data pipeline operates in a structured sequence:

```
[Raw Sources: Pascal VOC XML / ARIS 3000 PNGs]
                     │
                     ▼
  [Standardization & Padding: 640x640 Canvas]
                     │
                     ▼
  [Zero-Leakage Sequence Partitioning: Train / Val / Test]
                     │
                     ▼
  [YOLO Normalized Format: datasets/sonar_debris_v2_clean/]
                     │
                     ▼
  [Reproducible Dataset Manifest & SHA256 Checksums]
                     │
                     ▼
  [YOLOv8 Acoustic-Augmented Training: train_yolo.py]
                     │
                     ▼
  [Standardized Evaluation & Error Categorization]
                     │
                     ▼
  [Production Model Promotion: models/detection/sonar_yolov8_fls_trained.pt]
```

### Existing Datasets
1. `datasets/sonar_debris_v2_clean/`:
   - 238 images, 371 bounding box annotations.
   - Splits: Train (166 imgs, 266 boxes), Val (35 imgs, 51 boxes), Test (37 imgs, 54 boxes).
   - Bounding boxes: Normalized center coordinates $[x_c, y_c, w, h] \in [0, 1]$.
   - Image format: $640 \times 640 \times 3$ (3-channel replicated grayscale).
   - Provenance: ARIS Explorer 3000 (3.0 MHz) Forward-Looking Sonar, Dr. Matias Valdenegro-Toro (Zenodo DOI: `10.5281/zenodo.15101686`).
2. `datasets/raw/marine-debris-fls/`:
   - 250 raw PNG images ($480 \times 320$) and 250 Pascal VOC XML annotations.
   - 12 images contain only acoustic tank wall returns (pure negative / background examples).

---

## 3. Inventory of Reusable Codebase Modules

The repository already contains high-grade ML and dataset utilities that will be directly reused and extended:

| Existing Module | Path | Reusable Capabilities |
| :--- | :--- | :--- |
| **Bbox Geometry & Audit** | `backend/ml/training/dataset_audit.py` | Aspect ratio, scale categorizer (tiny/small/med/large), coordinate bounds validation, IoU computation. |
| **Manifest & Versioning** | `backend/ml/training/dataset_version.py` | SHA256 file hashing, data YAML generation, manifest assembly. |
| **Training Engine** | `backend/ml/training/train_yolo.py` | Acoustic augmentations (zero hue/saturation jitter, gain scaling, horizontal flip), CPU threading. |
| **Evaluation Suite** | `backend/ml/training/evaluate_yolo.py` | Confidence threshold sweeps, per-class P/R/F1/mAP metrics, latency timing. |
| **Error Diagnostics** | `backend/ml/training/error_analysis.py` | FP/FN categorization (reverberation clutter, shadow, low-contrast debris). |
| **Latency Profiling** | `backend/ml/training/benchmark.py` | Mean, median, P95 latency breakdown across preprocessing, inference, and postprocessing. |
| **Model Promotion** | `backend/ml/training/model_promotion.py` | Automated weight promotion and metadata synchronization. |

---

## 4. Proposed Modular Expansion Architecture (`backend/ml/datasets/`)

To support Dataset V3 without duplicating existing training/evaluation code, a dedicated dataset engineering package is structured under `backend/ml/datasets/`:

1. `acquire.py` — Verifiable dataset acquisition engine with resumable HTTP downloads, SSL checks, and error logging.
2. `provenance.py` — Generates and validates immutable JSONL provenance records per sample.
3. `normalize.py` — Canvas padding and 3-channel grayscale replication without synthetic color distortion.
4. `audit.py` — Geometry integrity, bbox range checks, and annotation anomaly flags.
5. `deduplicate.py` — Exact SHA256 deduplication and perceptual hashing (pHash / dHash) for near-duplicate and sequence neighbor detection.
6. `split.py` — Group-aware stratified splitting guaranteeing zero cross-split sequence overlap.
7. `build_v3.py` — Unified CLI and orchestrator building V3-A, V3-B, and V3-C variants with manifest integrity checks.

---

## 5. Non-Destructive Protection Guarantee

- Baseline directory `datasets/sonar_debris_v2_clean/` is marked **READ-ONLY / FROZEN**.
- Production weights `models/detection/sonar_yolov8_fls_trained.pt` will remain untouched.
- The 37 held-out test frames from V2 are designated **`LEGACY_CONTROL_BENCHMARK`** and will be preserved as an immutable evaluation anchor.
- All existing 69 backend pytest test cases remain fully supported.
