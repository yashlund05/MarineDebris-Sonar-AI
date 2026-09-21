# Sonar Enhancement Profile Detector Utility Report

**Date**: 2026-09-19 13:03:12 UTC
**Model Checkpoint**: `sonar_yolov8_fls_trained.pt` (`e1215c7e7f6e...`)
**Validation Frames**: 15 from `datasets/sonar_debris_v3/val`

## Quantitative Performance Summary

| Profile | Mode | Precision | Recall | F1 Score | Δ F1 vs Raw | Mean Latency |
|---|---|---|---|---|---|---|
| **RAW** | `AI_SAFE` | 0.8947 | 0.8947 | **0.8947** | baseline | 1.46 ms |
| **AI_SAFE** | `AI_SAFE` | 0.9231 | 0.6316 | **0.7500** | -0.1447 | 78.37 ms |
| **BALANCED** | `AI_SAFE` | 0.9000 | 0.4737 | **0.6207** | -0.2740 | 63.57 ms |
| **HUMAN_VISUAL** | `HUMAN_DISPLAY` | 0.8889 | 0.4211 | **0.5714** | -0.3233 | 61.98 ms |

## Architectural Findings & Recommendations
- **AI_SAFE Profile**: Calibrated with conservative speckle reduction and strict shadow preservation.
- **HUMAN_VISUAL Profile**: Optimized for operator clarity with controlled CLAHE and edge definition.
- **Frozen Invariant**: Production YOLOv8 weights remain unaltered; SHA-256 integrity verified.
