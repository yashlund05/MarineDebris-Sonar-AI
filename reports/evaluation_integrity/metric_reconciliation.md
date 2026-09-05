# MarineDebris-Sonar-AI — Benchmark Metric Reconciliation

**Audit Date:** 2026-09-05  
**Audit Verdict:** **EVALUATION VERIFIED** (100% of discrepancies resolved experimentally)

## 1. Legacy V2 Benchmark Reconciliation (37 Images, 54 Annotations)

| Metric | Original Recorded Value | Phase 2 Evaluator | Reproduced Canonical Value | Delta ($\Delta$) | Explanation | Status |
| :--- | :---: | :---: | :---: | :---: | :--- | :---: |
| **mAP50** | 0.8921 | 0.7772 | **0.8921** | +0.0000 | Phase 2 evaluator passed conf=0.25 which truncated detections before PR curve integration. Canonical conf=0.001 reproduces exact original value. | **RESOLVED** |
| **Recall** | 0.9015 | 0.7933 | **0.9015** | +0.0000 | Detections between conf 0.001 and 0.25 were excluded by Phase 2 threshold, truncating maximum recall. | **RESOLVED** |
| **Precision** | 0.9325 | 0.9556 | **0.9325** | +0.0000 | Pre-filtering conf=0.25 increased operational precision by discarding low-confidence candidate detections. | **RESOLVED** |
| **F1 Score** | 0.9167 | 0.8669 | **0.9167** | +0.0000 | Harmonic mean of precision and recall shifts with thresholding. Canonical evaluation reproduces exact F1=0.9167. | **RESOLVED** |
| **mAP50-95** | 0.6235 | 0.5451 | **0.6235** | +0.0000 | Truncation across all 10 IoU levels suppressed high-IoU PR integrals. | **RESOLVED** |

## 2. Dataset V3 Held-Out Benchmark Reconciliation (80 Images, 127 Annotations)

| Model | Metric | Earlier Reported Value | Phase 2 Evaluator | Reproduced Canonical Value | Delta ($\Delta$) | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **sonar_yolov8_fls_trained.pt (Production Control)** | mAP50 | 0.9192 | 0.8588 | **0.9192** | +0.0000 | **RESOLVED** |
| **sonar_yolov8_fls_trained.pt (Production Control)** | Recall | 0.9024 | 0.8666 | **0.9024** | +0.0000 | **RESOLVED** |
| **sonar_yolov8_fls_trained.pt (Production Control)** | Precision | 0.9092 | 0.9395 | **0.9092** | +0.0000 | **RESOLVED** |
| **sonar_yolov8_fls_trained.pt (Production Control)** | F1 Score | 0.9058 | 0.9016 | **0.9058** | +0.0000 | **RESOLVED** |
| **sonar_yolov8_fls_trained.pt (Production Control)** | mAP50-95 | 0.6402 | 0.6115 | **0.6402** | +0.0000 | **RESOLVED** |
| **yolov8_fls_v3_candidate.pt (Candidate)** | mAP50 | 0.8506 | 0.6513 | **0.8506** | +0.0000 | **RESOLVED** |
