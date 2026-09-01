# MarineDebris-Sonar-AI: Machine Learning Architecture & Pipeline Specification

**Document Date:** 2026-09-01  
**Architecture Version:** v1.1.0  
**Authority:** Principal ML & Acoustic Systems Architect  
**Status:** **ACTIVE ML SPECIFICATION**

---

## 1. High-Level Architectural Pipeline

The MarineDebris-Sonar-AI processing engine follows a modular, fail-safe cascade designed for high-resolution acoustic sonar data:

```
                    REAL FLS SONAR (ARIS 3000)
                                │
                                ▼
                         1. INGESTION
                                │
                                ▼
                       2. PREPROCESSING
                                │
                                ▼
                         3. 640×640 TILING
                                │
                                ▼
                      4. YOLOv8m DETECTOR
                                │
                                ▼
                         RAW DETECTIONS
                                │
                                ▼
                  5. GLOBAL COORDINATE RESTORATION
                                │
                                ▼
                         6. GLOBAL NMS
                                │
                                ▼
                      7. ACOUSTIC FILTERING
                   (Shadow / Size Constraints)
                                │
                                ▼
                     8. SEMANTIC SEGMENTATION
                    (U-Net / SegFormer Mask)
                                │
                                ▼
                     9. SECONDARY CLASSIFIER
                    (Optional MobileNet Crop)
                                │
                                ▼
                  10. CONFIDENCE CALIBRATION &
                     DIMENSION ESTIMATION
                                │
                                ▼
                    11. WGS84 GEOREFERENCING
                                │
                                ▼
                     12. POSTGIS PERSISTENCE
                                │
                                ▼
                     13. REPORT GENERATION
```

---

## 2. Component Specifications

### 2.1 Primary Object Detector: YOLOv8m
- **Role:** Primary multi-target 2D object detection.
- **Input:** $640 \times 640 \times 3$ normalized acoustic sonar patches.
- **Anchor Strategy:** Anchor-free TaskAlignedAssigner.
- **Canonical Class Support:** Configured for canonical 5-class debris taxonomy (0: `derelict_fishing_gear`, 1: `general_marine_debris`, 2: `shipwreck`, 3: `pipe_or_cylinder`, 4: `other_man_made_target`).
- **Truthful Status Gate:** Reported as `MISSING_WEIGHTS` until task-specific weights (`sonar_yolov8m_ghostpot_v1.pt`) are trained and verified.

### 2.2 Semantic Segmentation: U-Net / SegFormer
- **Role:** Refines candidate bounding boxes into precise pixel-level object masks to calculate accurate physical area and contours.
- **Interface:** `BaseSegmenter.predict(tile, bbox) -> SegmentationResult`.
- **Outputs:**
  - `status`: `"available"`, `"unavailable"`, or `"failed"`
  - `mask_area`: Pixel area of segmented boundary
  - `mask_rle`: Run-Length Encoded binary mask
  - `contour`: Polygon vertices for visualization
- **Graceful Degradation:** If weights are uninstalled, `status: "unavailable"` is returned. Under no circumstance does segmentation failure abort the survey pipeline.

### 2.3 Secondary Classifier: MobileNet / ResNet
- **Role:** Optional candidate verification stage running on isolated object crops.
- **Interface:** `ClassifierBackend.predict(crop) -> ClassificationResult`.
- **Consensus Policy:** Evaluates classification agreement (`✓ AGREED` vs `⚠ REVIEW`). By design, unverified secondary classifiers **do not override** YOLO detector predictions unless an explicit re-ranking rule is triggered.

### 2.4 Model Registry & Anti-Fabrication Gates
- Exposes truthful runtime statuses:
  - `MISSING_WEIGHTS`: Checkpoint file absent from disk.
  - `INVALID_WEIGHTS`: Checkpoint corrupt or unreadable.
  - `EXPERIMENTAL`: Model initialized for evaluation but uncertified for production.
  - `PRODUCTION_READY`: Formally certified on held-out test splits.
- Explicitly tracks **Supported Trained Classes** (currently 2 classes for FLS) versus **Configured Canonical Classes** (5 classes).

---

## 3. Failure Handling & Observability

| Failure Condition | Pipeline Behavior | API Output |
| :--- | :--- | :--- |
| **Missing Detector Weights** | Logs warning; returns empty detection list | `detections: []`, `status: "complete"` |
| **Segmentation Unavailable** | Continues with bounding box only | `segmentation.status: "unavailable"`, `mask: null` |
| **Classifier Unavailable** | Continues with YOLO class | `classification.status: "unavailable"`, `agreement: null` |
| **Missing Nav Data** | Projects local swath coordinates; omits lat/lon | `geotagging_available: false`, `latitude: null` |
