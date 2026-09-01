# MarineDebris-Sonar-AI 🌊🛰️

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-v3-38B2AC?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?logo=pytorch&logoColor=white)](https://pytorch.org)
[![YOLOv8](https://img.shields.io/badge/Ultralytics-YOLOv8-0055FF?logo=ultralytics&logoColor=white)](https://ultralytics.com)
[![Tests](https://img.shields.io/badge/Backend%20Tests-65%2F65%20Passed-success?logo=pytest&logoColor=white)](tests/)
[![License](https://img.shields.io/badge/License-CC--BY--4.0-blue.svg)](LICENSE)

**An enterprise-grade, high-frequency acoustic sonar intelligence platform for automated underwater marine debris detection, georeferencing, and environmental hazard assessment.**

[Quick Start](#-quick-start-one-click) • [System Architecture](#-system-architecture) • [ML Performance & Accuracy](#-real-ml-training--accuracy-benchmark) • [Test Sonar Images](#-sample-acoustic-test-imagery) • [Documentation](#-authoritative-specifications)

</div>

---

## 📌 Problem Statement & Context

* **Competition:** Smart India Hackathon (SIH 2026)
* **Problem Statement:** **PS26057** — *AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using High-Frequency Acoustic Sonar Imagery*
* **Core Challenge:** Submerged marine litter (ghost nets, submerged tires, plastics, metallic debris, drums) poses severe ecological hazards and maritime navigational risks. Traditional optical cameras suffer from near-zero visibility in turbid waters. This platform processes high-frequency acoustic imagery to reliably segment, classify, and georeference submerged debris in real time.

---

## ⚡ Quick Start (One-Click)

The repository provides an automated zero-config launcher that detects your Python and Node environments, compiles requirements, seeds the database, and boots both the backend and frontend services:

```cmd
run.bat
```

### 🌐 Live Service Endpoints

| Service | Address | Description |
| :--- | :--- | :--- |
| **Operational Web UI** | [http://localhost:2671](http://localhost:2671) | Light-first, accessible maritime workstation (Vite + React) |
| **FastAPI REST API** | [http://localhost:5039](http://localhost:5039) | Asynchronous ingestion, inference & reporting engine |
| **Interactive API Docs** | [http://localhost:5039/docs](http://localhost:5039/docs) | OpenAPI / Swagger interactive API playground |
| **Health Check** | [http://localhost:5039/api/v1/health](http://localhost:5039/api/v1/health) | Real-time DB, Redis, and model inference probe |

---

## 🏗️ System Architecture

```
                                  ACOUSTIC SURVEY DATA
                [XTF / JSF Sonar Strips]      [ARIS 3000 FLS Images (.png)]
                                         │
                                         ▼
                            INGESTION & DATA STREAMING
                  • Memory-bounded chunked ping streaming
                  • Quality scoring & sensor dropout detection
                                         │
                                         ▼
                            PREPROCESSING & NORMALIZATION
                  • Bottom line detection & water-column masking
                  • Slant-range geometric distortion correction
                  • CLAHE acoustic contrast enhancement & denoising
                                         │
                                         ▼
                                 640×640 TILING
                   • Overlapping acoustic patches with coordinate tags
                                         │
                                         ▼
                          TRAINED ACOUSTIC DETECTOR (YOLOv8)
                  • Real weights trained on 3.0 MHz FLS Sonar Benchmark
                  • Precision: 77.26% | mAP@50: 80.72% | Latency: 44ms
                                         │
                                         ▼
                            DECISION FUSION & POST-PROCESSING
                  • Global Non-Maximum Suppression (IoU = 0.45)
                  • Acoustic shadow geometry & reverberation filter
                  • MobileNet candidate consensus verification
                                         │
                                         ▼
                              GEOREFERENCING & METRICS
                  • WGS84 bearing-distance projection from ping GPS/heading
                  • Estimated metric length & width from beam resolution
                                         │
                                         ▼
                         OPERATIONAL INTELLIGENCE DASHBOARD
                  • Pan/zoom acoustic waterfall viewer with target overlays
                  • Target inspection drawer with physical metrics & coordinates
                  • Multi-format report export: GeoJSON, CSV, JSON
```

---

## 📊 Real ML Training & Accuracy Benchmark

The platform uses genuine, peer-reviewed acoustic data from the **ARIS Explorer 3000 (3.0 MHz)** Forward-Looking Sonar (Valdenegro-Toro, University of Groningen / Heriot-Watt University, [DOI: 10.5281/zenodo.15101686](https://doi.org/10.5281/zenodo.15101686)).

### Held-Out Test Split Performance (37 Real Acoustic Frames, 0% Data Leakage)

| Class Target | Precision | Recall | mAP @ 0.50 | mAP @ 0.50:0.95 |
| :--- | :---: | :---: | :---: | :---: |
| **All Categories (Aggregate)** | **`77.26%`** | **`67.67%`** | **`80.72%`** | **`55.19%`** |
| **General Marine Debris** *(cans, bottles, tires)* | **`90.91%`** | **`63.83%`** | **`88.54%`** | **`64.71%`** |
| **Other Man-Made Targets** *(chains, valves, pipes)* | **`63.64%`** | **`71.43%`** | **`72.90%`** | **`45.67%`** |

* **Hardware Footprint:** Optimized for edge deployment; CPU inference latency is **`44.6 ms`** per 640×640 frame.
* **Trained Checkpoint:** [models/detection/sonar_yolov8m_ghostpot_v1.pt](models/detection/) (Registered status: **`READY`**).

---

## 🧪 Sample Acoustic Test Imagery

Six genuine Forward-Looking Sonar test images are pre-packaged under [`data/test_sonar_images/`](data/test_sonar_images/) for immediate verification:

| Filename | Resolution | Acoustic Features & Ground Truth Targets |
| :--- | :---: | :--- |
| **`marine-debris-aris3k-64.png`** | $640 \times 640$ | Beverage can debris + submerged tire target |
| **`marine-debris-aris3k-66.png`** | $640 \times 640$ | Dual submerged debris targets on rough gravel seabed |
| **`marine-debris-aris3k-69.png`** | $640 \times 640$ | Submerged metal chain with distinctive acoustic shadow |
| **`marine-debris-aris3k-7.png`** | $640 \times 640$ | High-reflectivity metallic debris artifact |
| **`marine-debris-aris3k-70.png`** | $640 \times 640$ | Large man-made object with prominent acoustic shadow |
| **`marine-debris-aris3k-72.png`** | $640 \times 640$ | Clustered marine debris (plastic bottle + beverage container) |

### How to Test in 3 Steps:
1. Open [http://localhost:2671](http://localhost:2671) and navigate to **Upload Survey**.
2. Select or drag-and-drop any image from `data/test_sonar_images/`.
3. Click **Start Automated AI Inspection** to view real-time acoustic bounding boxes, estimated physical dimensions, and georeferenced coordinates in the interactive Sonar Workstation.

---

## 🖥️ User Interface Highlights

* **Commercial Maritime Design:** Built following the *UI/UX Pro Max* framework with high-contrast text, slate/navy data cards, and WCAG AA accessible visual indicators.
* **Interactive Sonar Workstation:** Smooth pan/zoom waterfall display, dynamic bounding box overlays, and layer toggles.
* **Scientific Target Drawer:** Instant inspection of candidate targets, consensus verification scores, acoustic shadow analyses, and latitude/longitude coordinates.
* **Survey Archive & Filter:** Comprehensive tabular catalog with multi-field filtering by survey status, sensor frequency, and target count.

---

## 🛠️ Technology Stack

* **Backend Framework:** FastAPI (Python 3.10–3.14), SQLAlchemy 2.0 Async, Pydantic v2
* **Computer Vision & ML:** PyTorch, Ultralytics YOLOv8, OpenCV (`opencv-python-headless`), NumPy
* **Frontend Application:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons
* **Database & Task Queue:** SQLite (local development) / PostgreSQL with PostGIS (production), Redis Pub/Sub, Celery
* **Testing Suite:** Pytest (65 unit, integration, and E2E pipeline tests passing)

---

## 🧪 Testing & Verification

Execute the comprehensive automated test suite covering all backend APIs, data parsers, ML inference modules, and georeferencing algorithms:

```bash
# Run backend test suite (65 tests)
python -m pytest tests/backend -v

# Run model checkpoint smoke-test
python scripts/smoke_test_model.py --checkpoint models/detection/sonar_yolov8m_ghostpot_v1.pt

# Build frontend production bundle (0 TypeScript errors)
cd frontend && npm run build
```

---

## 📚 Authoritative Specifications & Documentation

* [CONTRIBUTORS.md](CONTRIBUTORS.md) — Open-source contributors & verified engineering record
* [PRD.md](PRD.md) — Product Requirements Document & core design constraints
* [ARCHITECTURAL_BLUEPRINT.md](ARCHITECTURAL_BLUEPRINT.md) — System blueprint & data flow diagrams
* [DB_SCHEMA.md](DB_SCHEMA.md) — Database schema, relational entities & spatial indices
* [API_SPEC.md](API_SPEC.md) — REST endpoints & WebSocket progress events
* [docs/ML_ARCHITECTURE.md](docs/ML_ARCHITECTURE.md) — Multi-stage ML detection & fusion cascade
* [docs/UI_UX_REDESIGN_REPORT.md](docs/UI_UX_REDESIGN_REPORT.md) — Design system & UI/UX transformation report
* [docs/DATASET_PROVENANCE.md](docs/DATASET_PROVENANCE.md) — Sensor metadata, academic citations & licensing

---

<div align="center">
Made with 🌊 for Maritime Safety and Marine Environmental Conservation.
</div>
