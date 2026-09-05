# Phase 12 — Sample-Level Error Analysis & Ground-Truth Matching Report

## 1. Executive Summary
Phase 12 delivers the granular sample-level error analysis and acoustic target matching endpoint:
`GET /api/v1/models/{model_id}/error-analysis`

This endpoint breaks down model performance across physical target dimensions, acoustic sensor ranges, and contrast conditions, isolating acoustic failure modes without synthetic abstractions.

---

## 2. API Specification & Subgroup Breakdowns
- **Route**: `GET /api/v1/models/{model_id}/error-analysis`
- **Response Structure (`ErrorAnalysisResponse`)**:
  - `model_id`: Target model identifier.
  - `total_gt_boxes`: Total ground truth targets evaluated (e.g. 127 boxes).
  - `total_true_positives`: Total verified correct detections.
  - `overall_recall`: Empirical sensitivity.
  - `subgroups`:
    - `small_lt_40px`: Targets under 40 pixels (acoustic attenuation, multipath sensitivity).
    - `medium_40_100px`: Standard debris targets (highest recall, >95%).
    - `large_gt_100px`: Extended targets (>100 pixels).
    - `far_range_gt_3_5m`: Targets at sonar range > 3.5m.
    - `mid_range_2_to_3_5m`: Sweet spot of acoustic beam geometry.
    - `near_range_lt_2m`: Close proximity targets prone to acoustic receiver saturation.
    - `faint_low_contrast`: Low-reflectivity debris submerged in sediment.
    - `normal_contrast`: Distinct acoustic specular reflections.
  - `false_alarm_profile`: Quarry seabed clutter evaluation (84 frames, total FP boxes, FAR).
  - `error_breakdown_notes`: Research commentary identifying physical acoustic failure modes.

---

## 3. Verification & Automated Tests
Automated tests in `tests/backend/test_model_error_analysis_api.py` passed with 100% success in 0.10s:
1. `test_model_error_analysis_production`: Verifies subgroup breakdowns for production baseline.
2. `test_model_error_analysis_candidate`: Verifies error analysis for candidates like `P3_E2_NAIVE_MIX`.
