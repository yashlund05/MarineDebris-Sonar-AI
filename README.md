# MarineDebris-Sonar-AI

**Competition / Problem Statement:** SIH 2026 — PS26057  
**Topic:** AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using High-Frequency Acoustic Sonar Imagery  
**Status:** **FLS Dataset & ML Architecture Integrated (65/65 Backend Tests Passing, Frontend Verified)**

---

## 1. Quick Start (One-Click Launch)

To start both the Backend and Frontend with automated environment detection:

```cmd
run.bat
```

The script will automatically:
1. Detect Python (3.10+) and Node.js (18+).
2. Set up Python virtual environment (`.venv`) and install dependencies.
3. Install frontend dependencies (`npm install`).
4. Initialize local storage directories and database tables.
5. Launch the **FastAPI Backend on port 5039**: `http://localhost:5039`
6. Launch the **React Frontend on port 2671**: `http://localhost:2671`
7. Automatically open your browser to `http://localhost:2671`.

---

## 2. Service Endpoints
- **Web Application UI:** [http://localhost:2671](http://localhost:2671)
- **FastAPI REST API:** [http://localhost:5039](http://localhost:5039)
- **Interactive Swagger Docs:** [http://localhost:5039/docs](http://localhost:5039/docs)

---

## 3. Real Acoustic Sonar Dataset (FLS Benchmark)

The project incorporates real, peer-reviewed acoustic imagery captured using an **ARIS Explorer 3000 (3.0 MHz)** acoustic camera (University of Groningen / Heriot-Watt University, DOI `10.5281/zenodo.15101686`, licensed under CC-BY 4.0).

- **Location:** `datasets/sonar_debris/`
- **Total Images:** 238 validated acoustic sonar frames (640×640 standardized canvas)
- **Total Bounding Boxes:** 371 ground-truth debris targets
- **Splits:** Train (166 images, 258 boxes), Val (35 images, 55 boxes), Test (37 images, 58 boxes)
- **Supported Trained Classes:**
  - `general_marine_debris` (bottles, cans, drink cartons, tires — 267 annotations)
  - `other_man_made_target` (chains, propellers, valves, hooks — 104 annotations)
- **Untrained Canonical Classes:** `derelict_fishing_gear`, `shipwreck`, `pipe_or_cylinder` (0 samples in current dataset; explicitly tracked to prevent false claims)

---

## 4. Machine Learning System Architecture

The inference engine executes a multi-stage acoustic processing pipeline:
1. **Primary Detector:** **YOLOv8m** on $640 \times 640$ acoustic tiles.
2. **Post-Processing:** Global coordinate restoration, Global NMS ($IoU = 0.45$), acoustic shadow filter, and size constraint filtering.
3. **Semantic Segmentation:** **U-Net / SegFormer** for candidate object boundary and mask extraction.
4. **Secondary Classifier:** **MobileNet / ResNet** for candidate crop verification.
5. **Decision Fusion:** Consensus agreement scoring without silent detection overrides.
6. **Georeferencing & Dimensions:** WGS84 bearing-distance projection and physical metric estimation.

---

## 5. Model Readiness & Truthfulness Certification

| Checkpoint | Status | Details |
| :--- | :---: | :--- |
| **Acoustic Dataset** | ✅ VALIDATED | 238 real FLS images, 371 annotations, 0 leakage |
| **YOLOv8m Checkpoint** | ⚠️ `MISSING_WEIGHTS` | Baseline training pipeline configured; checkpoint pending training |
| **U-Net Segmentation** | ⚠️ `UNAVAILABLE` | Gracefully falls back to bounding boxes without failing survey |
| **MobileNet Classifier** | ⚠️ `UNAVAILABLE` | Gracefully degrades; YOLO detection retained as source of truth |
| **Production Gate** | **EXPERIMENTAL** | Truthfully gated until verified task weights are trained |

---

## 6. Authoritative Specifications

* [PRD.md](PRD.md) — Product Requirements Document
* [ARCHITECTURAL_BLUEPRINT.md](ARCHITECTURAL_BLUEPRINT.md) — System Architecture & Processing Pipelines
* [DB_SCHEMA.md](DB_SCHEMA.md) — Relational Schema & Indices
* [API_SPEC.md](API_SPEC.md) — REST & WebSocket Specifications
* [docs/ML_ARCHITECTURE.md](docs/ML_ARCHITECTURE.md) — Detailed ML Architecture & Cascades
* [docs/ML_REFERENCE_INTEGRATION.md](docs/ML_REFERENCE_INTEGRATION.md) — Reference Repo Attribution & Model Discovery
* [docs/DATASET_PROVENANCE.md](docs/DATASET_PROVENANCE.md) — Legal Licensing & Academic Citations
* [docs/BLOCKER_1_DATASET_FINAL_REPORT.md](docs/BLOCKER_1_DATASET_FINAL_REPORT.md) — Dataset Acceptance Audit Report
