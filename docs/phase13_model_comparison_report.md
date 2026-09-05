# Phase 13 — Model Comparison Engine Report

## 1. Executive Summary
Phase 13 establishes the research-grade **Model Comparison Engine**:
`GET /api/v1/models-comparison`

This endpoint ranks candidate models and production baselines using transparent multi-objective composite scoring, aligning detection sensitivity, false-alarm rejection, legacy retention, small-target resolution, and latency compliance.

---

## 2. Multi-Objective Weighting Schema
Candidates are ranked based on the following mathematically disclosed weights:
- **V3 Held-out Generalization ($w_{v3} = 35\%$)**: Evaluates generalization against new acoustic survey deployments.
- **Legacy V2 Preservation ($w_{v2} = 25\%$)**: Enforces retention on historical debris targets.
- **Hard-Negative FAR Rejection ($w_{far} = 20\%$)**: Penalizes seabed clutter and acoustic reverberation hallucinations.
- **Small-Target (<40px) Sensitivity ($w_{small} = 10\%$)**: Prioritizes detection of faint acoustic targets.
- **Edge Latency Adherence ($w_{lat} = 10\%$)**: Rewards models satisfying embedded CPU throughput ($\le 50\text{ ms} \to 1.0$, linearly scaling to $0.0$ at $\ge 150\text{ ms}$).

---

## 3. Verification & Automated Tests
Automated tests in `tests/backend/test_model_comparison_api.py` passed with 100% success in 0.07s:
- `test_models_comparison`: Validates composite score computation, relative ranking, and metadata integrity across all registered Phase 3 models.
