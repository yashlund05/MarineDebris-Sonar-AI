# Phase 11 — Dataset -> Model -> Prediction Traceability Report

## 1. Executive Summary
Phase 11 establishes full scientific traceability across the acoustic ML lifecycle:
`GET /api/v1/models/{model_id}/traceability`

This endpoint connects dataset version manifests, training split integrity, checkpoint file cryptographic hashes, benchmark evaluation manifests, and live inference dispatch into a single unified provenance graph.

---

## 2. Traceability Schema & Features
- **Route**: `GET /api/v1/models/{model_id}/traceability`
- **Output Schema (`ModelTraceabilityResponse`)**:
  - `model_id`: Target model identifier.
  - `display_name`: Human-readable research label.
  - `dataset_version`: Originating dataset split (`v2` or `v3`).
  - `dataset_manifest_path`: Absolute path to `DATASET_MANIFEST.json`.
  - `training_split`: Verified image & box accounting (`train`, `val`, `test`).
  - `checkpoint_path`: Verified physical model weights.
  - `checkpoint_sha256`: Cryptographic fingerprint (`e1215c7e...` for production).
  - `evaluation_manifest`: Path to authoritative `BENCHMARK_MANIFEST.json`.
  - `lineage_graph`: Chronological provenance ledger:
    1. `dataset_curation`: Dataset split reconciliation & audit verification.
    2. `training`: Supervised YOLOv8 acoustic training run with seed tracking.
    3. `benchmark_eval`: Canonical and operational benchmark evaluation.
    4. `inference`: Production deployment dispatch readiness.

---

## 3. Verification & Automated Tests
Automated tests in `tests/backend/test_model_traceability_api.py` passed with 100% success in 0.12s:
1. `test_model_traceability_production`: Validates full 4-stage provenance for the production baseline.
2. `test_model_traceability_candidate`: Validates lineage resolution for experimental candidates.
