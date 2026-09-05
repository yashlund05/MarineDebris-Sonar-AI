# Phase 8 — Model Evaluation Dashboard Report

## 1. Executive Summary
Phase 8 delivers the research-grade **Model Evaluation Dashboard** (`/models/evaluation`), establishing complete empirical visualization and model governance transparency across both production baselines and experimental candidates (`P3_E2_NAIVE_MIX`, multi-seed suite `E6`).

The dashboard is completely API-driven (`GET /api/v1/models/*`), contains zero hardcoded numbers, and strictly distinguishes between canonical research benchmarks and operational deployment points.

---

## 2. Implemented Components
The following modular components were implemented under `frontend/src/components/model/` and integrated into `ModelEvaluationPage.tsx`:

1. `ExperimentSelector.tsx`: Checkpoint and experiment model selector allowing real-time switching between registered models, baseline benchmarks, and candidates.
2. `ModelOverviewCard.tsx`: Displays active model metadata, architecture (`YOLOv8 Nano`), framework (`PyTorch / Ultralytics`), checkpoint file path, runtime readiness, hardware device, and target class coverage. Untrained canonical classes are rendered with struck-through badges to prevent misattribution.
3. `MetricSummary.tsx`: Dual-regime detection metric dashboard:
   - **Canonical Research Benchmark**: Confidence threshold 0.001, IoU 0.70 (mAP50, mAP50-95, precision, recall).
   - **Operational In-Water Point**: Confidence threshold 0.25, IoU 0.45 (precision, recall, F1, mAP50).
4. `PromotionGateCard.tsx`: Automated visual audit card evaluating the 4 mandatory promotion gates (mAP50 gain, FAR reduction, V2 retention, CPU P95 latency). Highlights rejection status clearly with root cause rationale.
5. `LatencyAndFalseAlarm.tsx`: Dual telemetry cards covering:
   - Hard-negative false alarm rate (FAR) and false positive count on 84 quarry seabed frames.
   - CPU latency profiles (Mean, P50, P95, Throughput) with budget pass/fail indicators (Budget: <= 125.0 ms P95).
6. `MultiSeedStability.tsx`: Tabulates variance across seeds 42, 123, 2026 for V3 mAP50, V3 recall, V2 mAP50, and FAR, complete with 95% confidence intervals and small-sample Student-t disclosures (N=3, df=2).
7. `ExplainabilityAndArtifacts.tsx`: Diagnostic panels presenting operational strengths, weaknesses/constraints, and physical artifact integrity verification (SHA256 verification, existence check, file paths).

---

## 3. Integration & Build Verification
- **Routing**: Added `/models/evaluation` in `frontend/src/App.tsx`.
- **Navigation**: Added "Model Evaluation" link under the Intelligence section in `frontend/src/components/layout/Sidebar.tsx`.
- **TypeScript**: `npx tsc --noEmit` passed with 0 errors.
- **Production Build**: `npm run build` completed successfully (2,510 modules transformed, dist/ generated).
