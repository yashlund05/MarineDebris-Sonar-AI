# MarineDebris-Sonar-AI: Model Acceptance Criteria & Quality Gate

**Date:** 2026-09-01  
**Authority:** Architectural Blueprint §9, Production QA Standards  
**Status:** **ACTIVE QUALITY GATE SPECIFICATION**

---

## 1. Objective Quality Gate Criteria

Before any trained model checkpoint (`.pt`, `.onnx`) can be promoted from `EXPERIMENTAL` to `PRODUCTION_READY` in `models/detection/`, it must satisfy all 10 criteria of the Quality Gate:

| Check # | Criterion | Acceptance Threshold | Verification Method |
| :---: | :--- | :--- | :--- |
| **Q1** | **Weight Integrity** | Non-corrupt PyTorch/TorchScript/ONNX file structure | `ModelLoader.load_detection_model()` returns model object without exceptions |
| **Q2** | **Device Agnosticism** | Operates on CUDA when present and falls back to CPU cleanly | Validated via `torch.cuda.is_available()` device routing |
| **Q3** | **Input Resolution Conformance** | Accepts $640 \times 640$ acoustic normalized tiles | Forward pass on synthetic zeros/ones array of shape `(1, 3, 640, 640)` |
| **Q4** | **Class Taxonomy Mapping** | Class indices strictly in $\{0, 1, 2, 3, 4\}$ | Predicted class IDs match canonical taxonomy table without out-of-range IDs |
| **Q5** | **Probability Bounds** | All raw confidence scores $c \in [0.0, 1.0]$ | `assert 0.0 <= conf <= 1.0` across all predicted bounding boxes |
| **Q6** | **Spatial Coordinate Bounds** | Bounding boxes $x \ge 0, y \ge 0, x+w \le 640, y+h \le 640$ | Clamping validation; no negative dimensions ($w > 0, h > 0$) |
| **Q7** | **Numerical Stability** | Zero `NaN`, `Inf`, or `-Inf` values in logits or coordinates | `assert not math.isnan(val) and not math.isinf(val)` |
| **Q8** | **Validation mAP50** | $mAP_{50} \ge 0.65$ on held-out sidescan sonar test set | Evaluated via `training/evaluation/evaluate_model.py` |
| **Q9** | **Latency Ceiling** | GPU inference $< 25 \text{ ms/tile}$; CPU inference $< 350 \text{ ms/tile}$ | Measured via 50-iteration benchmark |
| **Q10** | **Failure Transparency** | When model file is missing or invalid, fail truthfully | Log error and return empty detections without fabricating predictions |

---

## 2. Model Classification States in Model Registry

1. **`PRODUCTION_READY`:** Passed all criteria Q1–Q10 with genuine Sidescan Sonar validation data.
2. **`EXPERIMENTAL`:** Trained checkpoint available and passes Q1–Q7, but validation mAP50 is below 0.65 or dataset size was limited.
3. **`MISSING_WEIGHTS` (Current State):** Architecture and loader are fully implemented, but no weight file exists at `models/detection/sonar_yolov8m_ghostpot_v1.pt`.
4. **`INVALID_WEIGHTS`:** Checkpoint file exists but fails deserialization or forward-pass checks.
