# MarineDebris-Sonar-AI — Evaluation Implementation Audit

**Audit Date:** 2026-09-05  
**Auditors:** ML Evaluation Engineer & Statistical Validation Team  
**Scope:** `backend/ml/training/evaluate_yolo.py`, `backend/ml/experiments/evaluator.py`, `backend/ml/experiments/calibration.py`, `backend/ml/training/benchmark.py`, `backend/ml/experiments/seeds.py`

---

## 1. Executive Summary

This audit establishes the precise technical root cause for the metric discrepancies observed between the original frozen production benchmarks and the Phase 2 experiment evaluator:

1. **The Discrepancy is Entirely Methodological, NOT Data or Model Drift:**
   The production checkpoint `models/detection/sonar_yolov8_fls_trained.pt` (SHA256: `e1215c7e...`) and the legacy dataset `datasets/sonar_debris_v2_clean` (37 images, 54 annotations) are **100% byte-for-byte identical** to the baseline snapshot.
2. **Root Cause: Pre-NMS Confidence Filtering in Ultralytics `model.val()`:**
   - **Original Baseline (`evaluate_yolo.py`):** Invoked `model.val()` with no explicit `conf` parameter. Ultralytics defaults to `conf=0.001` and `iou=0.60`. This evaluates the complete Precision-Recall (PR) curve down to 0.1% confidence, calculating true Mean Average Precision (mAP50 = **89.21%**, Recall = **90.15%**, F1 = **0.9167**).
   - **Phase 2 Evaluator (`evaluator.py`):** Invoked `model.val(..., conf=0.25, iou=0.45)`. Passing `conf=0.25` truncates candidate detections with confidence $< 0.25$ *prior* to PR curve construction. This artificial truncation dropped Recall to **79.33%** and mAP50 to **77.72%**.
   - **Empirical Proof:** Rerunning evaluation on the exact same model and test set with `conf=0.001` reproduces **exactly 89.21% mAP50, 93.25% Precision, 90.15% Recall, 0.9167 F1, and 62.35% mAP50-95** (an exact 100.000% match).

---

## 2. Code-by-Code Inspection

### 2.1 `backend/ml/training/evaluate_yolo.py` (Original Benchmark Engine)
```python
val_results = model.val(
    data=str(data_yaml_path),
    split=split,
    imgsz=imgsz,
    batch=batch,
    device=device,
    verbose=False,
    save_json=False,
    plots=False,
)
```
- **Confidence Setting:** Not passed. Ultralytics assigns default `conf=0.001`.
- **IoU Setting:** Not passed. Ultralytics assigns default `iou=0.60` (or `0.70` depending on model YAML).
- **Resulting Metric:** Complete area-under-curve mAP (ranking metric) + optimal point on the curve.
- **Legacy V2 Test Split Output:**
  - Precision: `0.9325` (93.25%)
  - Recall: `0.9015` (90.15%)
  - F1: `0.9167`
  - mAP50: `0.8921` (89.21%)
  - mAP50-95: `0.6235` (62.35%)

### 2.2 `backend/ml/experiments/evaluator.py` (Phase 2 Evaluator)
```python
results = model.val(
    data=str(data_yaml),
    split=split,
    imgsz=imgsz,
    batch=batch,
    conf=conf,  # default in class signature was conf=0.25!
    iou=iou,    # default in class signature was iou=0.45!
    device="cpu",
    verbose=False,
    plots=False,
)
```
- **Confidence Setting:** Hardcoded default `conf=0.25`.
- **IoU Setting:** Hardcoded default `iou=0.45`.
- **Flaw in Logic:** In Ultralytics YOLO, `conf` in `model.val()` is not just an operating-point threshold for post-evaluation display; it drops all detections with score $< 0.25$ before constructing the 101-point PR curve.
- **Impact on mAP:** Detections that would have contributed to the recall tail at lower confidence are eliminated, artificially truncating the PR curve at $R=0.7933$ instead of allowing it to reach $R=0.9015$.
- **Legacy V2 Test Split Output under `conf=0.25`:**
  - Precision: `0.9556` (Higher because low-confidence true positives and false positives are dropped)
  - Recall: `0.7933` (-10.82% drop due to truncation)
  - F1: `0.8669`
  - mAP50: `0.7772` (-11.49% drop)
  - mAP50-95: `0.5451` (-7.84% drop)

### 2.3 `backend/ml/experiments/calibration.py` (Calibration Sweep Engine)
- Swept `conf` from 0.05 to 0.80 and `iou` from 0.40 to 0.70.
- Correctly identified operational trade-offs for production deployment (e.g., Balanced `conf=0.25`, High Recall `conf=0.05`, High Precision `conf=0.45`).
- **Required Distinction:** The report must clearly separate **Ranking-Based Benchmark Metrics** (calculated with standard `conf=0.001` across the full PR curve) from **Operational Point Metrics** (calculated at specific thresholds like `conf=0.25` for AUV mission deployment).

### 2.4 `backend/ml/experiments/seeds.py` (Seed Evaluator)
- Evaluated the same model weights (`models/detection/sonar_yolov8_fls_trained.pt`) with `seed=42`, `seed=123`, `seed=2026` passed to `model.val()`.
- Since PyTorch CPU forward inference is completely deterministic and requires no random sampling, all evaluations produced identical metrics (std = 0.0000).
- **Classification Correction:** This must be classified as **"Deterministic Inference Repetition"**, NOT "Multi-Seed Training Reproducibility". Genuine multi-seed training requires running the entire training loop from random initialization or different augmentation seeds.

---

## 3. Comprehensive Metric Drift Summary Table

| Parameter / Factor | Original Baseline | Phase 2 Evaluator | Impact on Metric |
| :--- | :---: | :---: | :--- |
| **Dataset Files** | 37 images / 54 boxes | 37 images / 54 boxes | None (SHA256 identical) |
| **Model Weights** | `e1215c7e...` | `e1215c7e...` | None (SHA256 identical) |
| **Ultralytics Version** | 8.4.125 | 8.4.125 | None |
| **Image Resolution** | 640x640 | 640x640 | None |
| **Channel Format** | 3-ch grayscale | 3-ch grayscale | None |
| **Evaluation `conf`** | **0.001 (default)** | **0.25 (truncated)** | **Severe (-11.49% mAP50, -10.82% Recall)** |
| **Evaluation `iou`** | **0.60 (default)** | **0.45** | Minor shift in duplicate suppression |

---

## 4. Standardization Mandate

To permanently eliminate evaluation ambiguity:
1. All official ranking benchmark evaluations (mAP50, mAP50-95) must strictly use **`conf=0.001`** and **`iou=0.60`** per standard computer vision benchmarking protocols (COCO, VOC, Ultralytics).
2. Operational performance metrics (Precision, Recall, F1 at a fixed mission threshold) must be explicitly designated as **Operational Point Metrics** (e.g., at `conf=0.25`).
3. Single canonical evaluation contract: `backend/ml/evaluation/evaluation_contract.py`.
