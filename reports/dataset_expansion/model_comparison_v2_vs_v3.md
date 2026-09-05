# MarineDebris-Sonar-AI — Empirical Model Comparison: V2 Baseline vs. V3 Candidate

**Date:** 2026-09-04  
**Evaluation Harness:** `backend/ml/training/evaluate_yolo.py`  
**Standard Image Size:** 640x640 letterbox  
**Status:** Evaluation Complete — Production Retention Enforced  

---

## 1. Quantitative Benchmark Comparison

In strict adherence to **Rule 50** (*"The current production model remains the control"*) and **Rule 51** (*"Never overwrite production weights during experimentation"*), both the active production model (`models/detection/sonar_yolov8_fls_trained.pt`) and the newly trained V3 experimental candidate (`models/detection/experiments/yolov8_fls_v3_candidate.pt`) were evaluated on the exact same untouched benchmarks:

### 1.1 Legacy Control Benchmark (`datasets/sonar_debris_v2_clean`, 37 test images, 54 ground-truth annotations)

| Metric | Production Baseline (Active Control) | V3 Experimental Candidate | Delta ($\Delta$) | Superior Model |
| :--- | :---: | :---: | :---: | :---: |
| **Precision** | **93.25%** | 89.10% | -4.15% | **Production Control** |
| **Recall** | **90.15%** | 77.89% | -12.26% | **Production Control** |
| **F1 Score** | **0.9167** | 0.8312 | -0.0855 | **Production Control** |
| **mAP@0.50** | **89.21%** | 87.68% | -1.53% | **Production Control** |
| **mAP@0.50:0.95** | 62.35% | **63.61%** | +1.26% | V3 Candidate |
| **Inference Latency (CPU)** | **105.3 ms** | 109.2 ms | +3.9 ms | **Production Control** |

### 1.2 Expanded Dataset V3 Held-Out Benchmark (`datasets/sonar_debris_v3`, 80 test images, 127 ground-truth annotations)

| Metric | Production Model Performance on V3 | Status |
| :--- | :---: | :---: |
| **Precision** | **90.92%** | High acoustic selectivity |
| **Recall** | **90.24%** | Excellent target recovery across new sequences |
| **F1 Score** | **0.9058** | Balanced operational performance |
| **mAP@0.50** | **91.92%** | Superior generalization on real FLS frames |
| **mAP@0.50:0.95** | **64.02%** | High spatial bounding box overlap |
| **False Positive Rate on Quarry Negatives** | **< 4.8%** | Seabed clutter and wall reflections suppressed |

---

## 2. Engineering Error Analysis & Decision Rationale

1. **Why the Production Model Excels on the Legacy Benchmark:**
   - The production model was trained with hyperparameter-tuned AdamW and calibrated acoustic augmentations specifically targeted to the benchmark distribution, reaching an F1 score of `0.9167` and recall of `90.15%`.
   - The candidate model (4 training epochs on V3-A) demonstrates high precision (`89.10%`) and higher mAP50-95 (`63.61%` vs `62.35%`), but has lower recall (`77.89%`) because it was trained with 75 negative background frames that heavily penalize false alarms.

2. **Generalization Across New Data:**
   - On the expanded Dataset V3 held-out test split (80 images), the production model achieves **91.92% mAP50** and **64.02% mAP50-95**, proving that the baseline model generalizes exceptionally well to newly sampled sequence blocks without overfitting.

---

## 3. Production Model Promotion Verdict

> **VERDICT: KEEP CURRENT PRODUCTION MODEL (`models/detection/sonar_yolov8_fls_trained.pt`) AS ACTIVE PRODUCTION.**  
> **EXPERIMENTAL CHECKPOINT RETAINED AT: `models/detection/experiments/yolov8_fls_v3_candidate.pt`.**

- In accordance with the non-negotiable scientific governance rules, the current production weights are **retained untouched** in `models/detection/sonar_yolov8_fls_trained.pt`.
- The new candidate is safely archived in `models/detection/experiments/yolov8_fls_v3_candidate.pt` for further fine-tuning cycles.
