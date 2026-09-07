# MarineDebris-Sonar-AI: Master System Audit & Delta Analysis Report

**Auditor / Role:** Senior Lead Staff Engineer & MLOps Auditor  
**Date:** 2026-09-06  
**Audit Scope:** Complete Repository Architecture Delta Analysis (Freeze Baseline vs. Active Codebase)  
**Execution Mode:** STRICTLY READ-ONLY AUDIT  

---

## 1. Baseline vs. Current State Summary

### 1.1 What the Freeze Files Contained

The historical baseline of the repository is captured across five authoritative freeze documents and lock files:

1. **`docs/IMPLEMENTATION_BASELINE.md` (2026-09-01, Commit `662d165c8b0946507ba801592525802896e20717`)**:
   - Initial operational test baseline: **41 passed, 0 failed** in 32.64s.
   - Core stack: FastAPI 0.139.0, SQLAlchemy 2.0.51, Pydantic 2.13.4, Celery 5.6.2.
   - Checkpoint state: `MISSING_WEIGHTS` (0 weights files in `models/detection/`).
   - Ground truth state: 0 real sonar annotation files; truthful zero-detection inference.

2. **`docs/FINAL_ML_BASELINE.md` (2026-09-01, Commit `662d165c8b0946507ba801592525802896e20717`)**:
   - Extended operational test baseline: **50 passed, 0 failed** in 37.50s.
   - Python 3.14.6, PyTorch 2.13.0+cpu, Ultralytics 8.4.125.
   - Model loader verified to return truthful empty detections when weights are absent.

3. **`reports/dataset_expansion/BASELINE_FROZEN` & `reports/model_optimization/PROTECTION_LOCK`**:
   - Formal dataset and model freeze established on 2026-09-04.
   - Enforces `BASELINE_DATASET_FROZEN = TRUE` and `PRODUCTION_MODEL_FROZEN = TRUE`.
   - Frozen dataset: `datasets/sonar_debris_v2_clean` (37 test images, 54 annotations).
   - Frozen production checkpoint: `models/detection/sonar_yolov8_fls_trained.pt`.
   - Expected SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`.

4. **`reports/evaluation_integrity/frozen_baseline_hashes.json` (2026-09-05)**:
   - Cryptographic SHA256 fingerprints for all 37 individual test images and 37 test label text files in the V2 clean dataset.
   - Cryptographic SHA256 verification of the production model weights.

5. **`reports/dataset_expansion/baseline_snapshot.json`**:
   - Manifest snapshot of `v2.0.0-clean`: 238 total real FLS images (train: 166, val: 35, test: 37) and 371 bounding box annotations.
   - Canonical performance targets: Validation mAP50 = 89.87%, Test mAP50 = 89.21%, Recall = 90.15%, Precision = 93.25%.

---

### 1.2 Major Architectural Additions Since the Freeze

Since the baseline freeze was established, the repository has expanded from a basic survey ingestion backend with 41–50 stub/unit tests to a full research-grade, multi-stage acoustic AI platform with **135 passed tests**:

```
+---------------------------------------------------------------------------------------------------+
| Architectural Domain   | Baseline Freeze State (Sept 1)      | Current Active State (Sept 6)      |
+---------------------------------------------------------------------------------------------------+
| Total Unit/Integ Tests | 41 - 50 passing tests               | 135 passing tests (0 failures)     |
| Real Acoustic Weights  | None (MISSING_WEIGHTS)              | Frozen production YOLOv8n (.pt)    |
| Experiment Registry    | None                                | 9 completed runs (E0 through E6)   |
| Dataset Architecture   | Raw synthetic/unstructured          | V2 Clean (238) + V3 Expanded (660) |
| Dataset API            | Stubs only                          | Dataset Explorer 2.0 (4 routes)    |
| Evaluation API         | None                                | Models & Evaluation API (11 routes)|
| Real-time Inference    | Empty zero-weight mock              | Live POST /inference/predict       |
| Frontend               | Basic survey dashboard              | Dataset Explorer + Model Eval UI   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Completion Inventory (What is Done)

### 2.1 Verified Completed & Passing Modules

1. **Phase 2.5: Evaluation Integrity & Benchmark Reconciliation** (**VERIFIED COMPLETE**):
   - Mathematically reconciled the mAP50 delta (89.21% canonical vs 77.72% operational) caused by pre-NMS confidence truncation (`conf=0.001` vs `conf=0.25`).
   - Formalized `backend/ml/evaluation/evaluation_contract.py`.
   - Generated cryptographic baseline ledger `reports/evaluation_integrity/BENCHMARK_MANIFEST.json`.
   - Verified zero metric drift on `datasets/sonar_debris_v2_clean`.

2. **Phase 3: Model Optimization & Robustness Lifecycle** (**VERIFIED COMPLETE**):
   - Implemented `SonarAugmentationPolicy` enforcing sonar physics (horizontal flipping only; vertical flipping and optical HSV jitter strictly blocked).
   - Built `HardNegativeSampler` (84 negative quarry/wall frames) and `HardPositiveMiner` (2.0x sampling weight for faint/far acoustic targets).
   - Executed E6 multi-seed training suite (seeds 42, 123, 2026) demonstrating multi-seed stability (std dev = 0.76% <= 1.5%).
   - Built non-regression `PromotionGate` enforcing absolute tolerances ($\Delta\text{mAP50} \le 1.0\%$, $\Delta\text{Recall} \le 2.0\%$, $\text{FAR} \le 21.43\%$, $\text{Latency} \le 125\text{ ms}$).
   - Automated test suite `tests/backend/test_phase3_optimization.py`: **20/20 passed**.

3. **Phase 6: Dataset Explorer 2.0 & V3 Integration** (**VERIFIED COMPLETE**):
   - Backend `DatasetService` (`backend/services/dataset_service.py`) and API router (`backend/api/routers/datasets.py`) delivering 4 endpoints with full confidence state tags (`VERIFIED`, `DERIVED`, `DECLARED`).
   - Frontend orchestrator `frontend/src/pages/DatasetPage.tsx` with 16 modular components in `frontend/src/components/dataset/`.
   - Zero hardcoded dataset metrics in UI; dynamic API-driven loading with strict fallback handling.
   - Automated test suite `tests/backend/test_dataset_api.py`: **5/5 passed**.

4. **Phase 9: CPU Latency Optimization** (**VERIFIED COMPLETE**):
   - Integrated `torch.inference_mode()` inside `backend/ml/optimization/latency_benchmark.py` and `backend/inference/detector.py`.
   - Pure model forward pass on standard CPU verified at ~80.18 ms.

5. **Phase 10: Real Production Inference API** (**VERIFIED COMPLETE**):
   - Live endpoint `POST /api/v1/inference/predict` in `backend/api/routers/inference.py`.
   - Executes image decoding, normalization, YOLO detection, physical dimension estimation, and georeferencing.
   - Interactive UI test tool `frontend/src/components/inference/InferenceTester.tsx`.
   - Automated test suite `tests/backend/test_inference_api.py`: **4/4 passed**.

6. **Phases 11–14: Traceability, Error Analysis, Model Comparison, Promotion Audit** (**VERIFIED COMPLETE**):
   - `backend/services/model_evaluation_service.py` provides sample-level error analysis, lineage traceability, and Pareto candidate ranking.
   - API endpoints in `backend/api/routers/models.py` tested across `test_model_evaluation_api.py`, `test_model_comparison_api.py`, `test_model_error_analysis_api.py`, `test_model_traceability_api.py`, and `test_promotion_audit_api.py` (**13/13 passed**).

7. **Full-Stack Build Integrity**:
   - Backend: **135 passed, 0 failed in 114.49s** (`pytest tests/ -v`).
   - Frontend Typecheck: `npx tsc --noEmit` exits 0 (0 errors).
   - Frontend Production Build: `npm run build` succeeds (2,512 modules transformed).

---

## 3. Work-in-Progress (What is Partially Done & Dependency Blocker Analysis)

### 3.1 Analysis of Phase 7: Model Evaluation API & `get_model_evaluation_service`

In the master architecture design, FastAPI route dependencies are intended to follow a clean inversion-of-control pattern centered in `backend/api/dependencies.py`.

#### Current Codebase Inspection:
1. **Definition Location**:
   - `ModelEvaluationService` and its provider function `get_model_evaluation_service` are defined in `backend/services/model_evaluation_service.py` (lines 447–448):
     ```python
     def get_model_evaluation_service() -> ModelEvaluationService:
         return ModelEvaluationService()
     ```
2. **Router Usage**:
   - In `backend/api/routers/models.py` (lines 14–17):
     ```python
     from backend.services.model_evaluation_service import (
         ModelEvaluationService,
         get_model_evaluation_service,
     )
     ```
   - Injected into route signatures:
     ```python
     @router.get("/models")
     async def list_models(
         ...,
         eval_service: ModelEvaluationService = Depends(get_model_evaluation_service),
     ):
     ```
3. **The Architectural Blocker / Gap**:
   - In `backend/api/dependencies.py`, only the following symbols are exported:
     ```python
     __all__ = ["get_db", "get_settings", "Settings", "AsyncSession", "Depends"]
     ```
   - `get_model_evaluation_service` is **absent** from `backend/api/dependencies.py`.
   - Any external router, test fixture, or module that follows standard FastAPI convention and attempts:
     ```python
     from backend.api.dependencies import get_model_evaluation_service
     ```
     will immediately raise:
     ```
     ImportError: cannot import name 'get_model_evaluation_service' from 'backend.api.dependencies'
     ```
   - **Per-Request Instantiation (Lifecycle Risk)**:
     `get_model_evaluation_service()` returns `ModelEvaluationService()` on every invocation without memoization (`@lru_cache`) or singleton lifecycle management. Each instantiation initializes file path objects and reads JSON manifests from disk on disk-bound routes.

---

## 4. Gap Analysis (What is Left across All Roadmaps)

### 4.1 FLS Dataset ML Integration Plan (Phases 1–20)

| Phase Area | Planned Scope | Current Status | Remaining Gap / Blocker |
| :--- | :--- | :--- | :--- |
| **Primary Detection** | YOLOv8m/n real-time detection | **OPERATIONAL** | Active weights trained on 2 classes only (`general_marine_debris`, `other_man_made_target`). |
| **Secondary Segmentation** | U-Net / SegFormer pixel masks | **INTERFACE-ONLY** | `UNetSegmenter` runs in graceful degradation (`status: "unavailable"`). Ground-truth masks exist (`data/watertank-segmentation/Masks/`), but weights file `models/segmentation/unet_sonar_v1.pt` is not trained. |
| **Secondary Classification** | MobileNet / ResNet crop verification | **INTERFACE-ONLY** | `MobileNetClassifier` runs in fallback mode (`status: "unavailable"`). Weight file `models/classification/mobilenet_debris_v1.pt` is not trained. |
| **Untrained Canonical Classes**| 3 classes (`derelict_fishing_gear`, `shipwreck`, `pipe_or_cylinder`) | **BLOCKED ON DATA** | 0 real acoustic annotations exist in FLS dataset for these 3 classes. Correctly labeled as *Performance Not Established*. |
| **Database Migrations** | Alembic migration scripts | **PARTIAL** | Table auto-creation runs via SQLAlchemy `Base.metadata.create_all`. Production deployment requires strictly gated `alembic upgrade head`. |

### 4.2 Model Performance Intelligence Roadmap (Phases 7–15)

| Roadmap Phase | Implementation State | Test Status | UI Status | Remaining Gap |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 7: Model Eval API** | Functional in router | 7/7 passing | N/A | Dependency injection location mismatch (`backend/api/dependencies.py`). |
| **Phase 8: Model Eval UI** | Complete in page | Clean build | Live | Needs route linking in navigation bar. |
| **Phase 9: Latency Tuning** | Sub-85ms forward pass | 20/20 passing | N/A | Heavy full-suite validation runs still take ~2 mins under test load. |
| **Phase 10: Inference API** | Active on CPU | 4/4 passing | Live tester | GPU acceleration (`torch.cuda`) disabled due to host CPU runtime. |
| **Phases 11-14: Audit/Comp** | Active in backend | 6/6 passing | Live tables | No automated database logging of historical inference requests. |
| **Phase 15: Release Audit** | Complete | All pass | Audit doc | Final promotion authorization required before replacing production weights. |

---

## 5. Immediate Next Steps (Prioritized Action Plan)

To unblock and streamline the codebase, execute the following prioritized steps:

### Step 1: Re-export & Memoize Dependency Injection (High Priority)
1. In `backend/api/dependencies.py`:
   - Import `ModelEvaluationService` and `get_model_evaluation_service` from `backend.services.model_evaluation_service`.
   - Add `@functools.lru_cache()` to `get_model_evaluation_service` to avoid redundant JSON manifest reads on every API call.
   - Update `__all__` in `backend/api/dependencies.py` to include `get_model_evaluation_service` and `ModelEvaluationService`.
2. In `backend/api/routers/models.py`:
   - Update import to pull `get_model_evaluation_service` from `backend.api.dependencies`.

### Step 2: Consolidate Navigation & UI Linkage (Medium Priority)
1. Add an explicit navigation link for the Model Evaluation Dashboard (`/models/evaluation`) into `frontend/src/components/layout/Navbar.tsx` and `frontend/src/components/layout/Sidebar.tsx`.

### Step 3: Production Database Migration Guarding (Medium Priority)
1. Ensure `AUTO_CREATE_TABLES` environment variable defaults to `False` in production deployments to enforce Alembic version migrations rather than runtime DDL creation.

### Step 4: Multi-Task Model Training (Future Milestone)
1. Train the secondary U-Net segmentation model using the 1,000 real watertank masks in `data/watertank-segmentation/Masks/` to transition the segmentation stage from graceful degradation (`unavailable`) to active pixel masking.
2. Acquire acoustic sonar training data for the 3 missing classes (`derelict_fishing_gear`, `shipwreck`, `pipe_or_cylinder`).
