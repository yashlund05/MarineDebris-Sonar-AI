# Phase 14 — Model Promotion & Rejection Intelligence Report

## 1. Executive Summary
Phase 14 delivers the immutable **Model Promotion & Rejection Intelligence Audit**:
`GET /api/v1/models-promotion/audit`

This endpoint exposes the governance state of the model lifecycle, ensuring that no experimental checkpoint can silently supplant production weights without satisfying every promotion gate and receiving explicit human authorization.

---

## 2. Model Promotion Governance Architecture
- **Active Production Checkpoint**: `models/detection/sonar_yolov8_fls_trained.pt`
- **Enforced Cryptographic SHA256**: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`
- **Promotion Governance Policy**: `STRICT_HUMAN_IN_THE_LOOP_OPT_IN`
- **Gating Rules Enforced**:
  1. $V2\text{ Legacy mAP50 Regression} \le 1.0\text{ percentage points}$
  2. $V2\text{ Legacy Recall Regression} \le 2.0\text{ percentage points}$
  3. $V3\text{ Generalization Retention } (\ge 89.92\%)$
  4. $\text{Negative Image False Alarm Rate (FAR)} \le 21.43\%\text{ (18/84 frames)}$
  5. $\text{Total False Positive Box Count} \le 18\text{ boxes}$
  6. $\text{CPU Inference Latency (P95)} \le 125.0\text{ ms}$
  7. $\text{Multi-Seed Stability (mAP50 Std Dev)} \le 1.5\%$

---

## 3. Verification & Automated Tests
Automated tests in `tests/backend/test_promotion_audit_api.py` passed with 100% success in 0.11s:
- `test_promotion_audit`: Verifies immutable audit records, rejection rationale tracking, allowed actions, and production SHA256 consistency.
