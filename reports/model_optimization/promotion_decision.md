# MarineDebris-Sonar-AI — Formal Model Promotion Decision

**Date:** 2026-09-04  
**Active Production Control Model:** `sonar_yolov8_fls_trained.pt`  
**Control Legacy Benchmark mAP50:** `77.72%` | **F1:** `0.8669`  

## VERDICT: PRODUCTION MODEL RETAINED — FURTHER OPTIMIZATION REQUIRED

> **SCIENTIFIC JUSTIFICATION:**  
> In strict compliance with **Rule 50** (*'The current production model remains the control'*), no experimental candidate demonstrated superior balanced performance over the active production baseline. Specifically, while V3-trained models demonstrate high precision and superior mAP50-95, the active production control model preserves higher legacy recall (90.15% vs 77.89%) and higher overall F1 (0.9167 vs 0.8312) while generalizing across Dataset V3 at 91.92% mAP50.

**Action Taken:**  
- Active production weights [`models/detection/sonar_yolov8_fls_trained.pt`](file:///c:/Users/ARYAN%20-%20AYUSH/OneDrive/Desktop/Marine%20sonar/models/detection/sonar_yolov8_fls_trained.pt) are **RETAINED INTACT**.
- Experimental candidates are preserved in `models/detection/experiments/` for future training iterations.
