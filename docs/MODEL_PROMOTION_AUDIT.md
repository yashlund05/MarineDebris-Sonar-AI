# Model Promotion Audit & Production Readiness Report

**Audit Date**: 2026-09-19  
**Subsystem**: Machine Learning Detection Registry & Gatekeeper  
**Auditor**: Senior Computer Vision Engineer & MLOps Architect  
**Status**: **AUDITED & GOVERNED**

---

## 1. Golden Invariant Verification

Before auditing candidate checkpoints, the active production model was cryptographically verified:
- **Production Path**: `models/detection/sonar_yolov8_fls_trained.pt`
- **Expected SHA-256**: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
- **Observed SHA-256**: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
- **Verification Result**: **BYTE-IDENTICAL & INTACT**

---

## 2. Standard Promotion Criteria (The Six Mandatory Gates)

In compliance with `MODEL_PROMOTION_POLICY.md`, a candidate checkpoint is granted `ELIGIBLE_FOR_PROMOTION` if and only if it passes all six criteria:

| Gate | Requirement | Required Threshold | Baseline Reference |
| :--- | :--- | :--- | :--- |
| **Gate 1** | Legacy V2 mAP@50 Absolute Non-Regression | $\ge 88.21\%$ (Max $-1.0\%$ abs) | $89.21\%$ |
| **Gate 2** | Legacy V2 Recall Absolute Non-Regression | $\ge 88.15\%$ (Max $-2.0\%$ abs) | $90.15\%$ |
| **Gate 3** | Dataset V3 Real Generalization mAP@50 | $\ge 89.92\%$ | $91.92\%$ |
| **Gate 4** | Negative Image False Alarm Rate (FAR) | $\le 21.43\%$ (Max $18/84$ frames) | $21.43\%$ |
| **Gate 5** | Total False Positive Boxes on Negatives | $\le 18$ boxes | $18$ boxes |
| **Gate 6** | CPU Inference Latency (P95) | $\le 125.0\text{ ms}$ ($\ge 8.0\text{ FPS}$) | $85.57\text{ ms}$ |

---

## 3. Comprehensive Candidate Evaluation Audit Matrix

All candidates were evaluated using the frozen evaluation contract across real held-out test splits:

| Model Checkpoint | Gate 1 (V2 mAP50) | Gate 2 (V2 Recall) | Gate 3 (V3 mAP50) | Gate 4 (FAR) | Gate 5 (FP Boxes) | Gate 6 (P95 Latency) | Audit Outcome |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Production Baseline** | 89.21% (Ref) | 90.15% (Ref) | 91.92% (Ref) | 21.43% (Ref) | 18 (Ref) | 85.57 ms (Pass) | **ACTIVE_PRODUCTION** |
| **`P3_E0_V2_CONTROL`** | 84.77% (FAIL) | 68.32% (FAIL) | 90.55% (Pass)| 17.86% (Pass)| 15 (Pass) | 44.41 ms (Pass) | `REJECTED` |
| **`P3_E1_V3_REAL`** | 93.49% (Pass) | 84.32% (FAIL) | 94.82% (Pass)| 4.76% (Pass) | 4 (Pass) | 48.35 ms (Pass) | `REJECTED` |
| **`P3_E2_NAIVE_MIX`** | **93.43% (Pass)** | **90.16% (Pass)** | **94.60% (Pass)**| **10.71% (Pass)**| **9 (Pass)** | **49.46 ms (Pass)** | **`ELIGIBLE_FOR_PROMOTION`** |
| **`P3_E3_BALANCED`** | 89.63% (Pass) | 83.43% (FAIL) | 90.93% (Pass)| 3.57% (Pass) | 3 (Pass) | 45.53 ms (Pass) | `REJECTED` |
| **`P3_E4_HARD_NEG`** | 89.18% (Pass) | 82.56% (FAIL) | 91.00% (Pass)| 4.76% (Pass) | 4 (Pass) | 48.11 ms (Pass) | `REJECTED` |
| **`P3_E5_HARD_POS`** | 91.87% (Pass) | 90.01% (Pass) | 93.05% (Pass)| 26.19% (FAIL)| 22 (FAIL) | 45.61 ms (Pass) | `REJECTED` |
| **`E6_SEED_42`** | **99.11% (Pass)** | **98.99% (Pass)** | **95.10% (Pass)**| **14.29% (Pass)**| **13 (Pass)** | **101.50 ms (Pass)** | **`ELIGIBLE_FOR_PROMOTION`** |
| **`E6_SEED_123`** | **97.07% (Pass)** | **89.67% (Pass)** | **95.31% (Pass)**| **15.48% (Pass)**| **13 (Pass)** | **51.33 ms (Pass)** | **`ELIGIBLE_FOR_PROMOTION`** |
| **`E6_SEED_2026`** | 98.27% (Pass) | 100.0% (Pass) | 97.42% (Pass)| 11.90% (Pass)| 10 (Pass) | 195.13 ms (FAIL) | `REJECTED` (Latency) |
| **`yolov8_fls_v3_candidate`** | 87.68% (FAIL) | 77.89% (FAIL) | 85.06% (FAIL)| 14.29% (Pass)| 13 (Pass) | 112.63 ms (Pass) | `REJECTED` |

---

## 4. Multi-Seed Stability Assessment (E6 Family)

Evaluated across seeds $\{42, 123, 2026\}$:
- **V2 mAP@50**: $98.15\% \pm 1.03\%$ ($\sigma \le 1.50\%$ limit satisfied).
- **V3 mAP@50**: $95.94\% \pm 1.28\%$ ($\sigma \le 1.50\%$ limit satisfied).
- **Hard-Negative FAR**: $13.89\% \pm 1.82\%$ (Consistent improvement over baseline $21.43\%$).

---

## 5. Promotion Recommendation & Staging Decision

1. **Top Candidate for Operational Edge Deployment**:
   `models/detection/experiments/phase3/P3_E2_NAIVE_MIX/weights/best.pt`
   - **SHA-256**: `8dd5150337576f6c8537c28ab0cc08c13fa190ce9c788efa61429d73530bcbf9`
   - **Characteristics**: $49.46\text{ ms}$ latency ($23.65\text{ FPS}$), $+4.22\%$ V2 mAP gain, $50\%$ fewer false alarms ($10.71\%$ vs $21.43\%$).
2. **Top Candidate for High-Accuracy Precision Survey**:
   `models/detection/experiments/phase3/E6_MULTISEED/seed_42/weights/best.pt`
   - **SHA-256**: `4726399b336d997bc7e0ed129c5edf89e4d3dd2eceadc754284ff4b7ca73a5f3`
   - **Characteristics**: Highest mAP ($99.11\%$ on V2, $95.10\%$ on V3), $98.99\%$ recall.
3. **Rollback & Immutability Governance**:
   - In accordance with non-negotiable policy, **neither candidate has been deployed automatically to `models/detection/sonar_yolov8_fls_trained.pt`**.
   - The production weights file remains frozen. Promotion is staged via `PROMOTION_CANDIDATE.json` awaiting human operator sign-off.
