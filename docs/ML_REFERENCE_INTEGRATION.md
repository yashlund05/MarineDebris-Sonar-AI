# MarineDebris-Sonar-AI: Reference ML Repository Integration & Attribution

**Document Date:** 2026-09-01  
**Authority:** MLOps & Scientific Software Engineering Lead  
**Audit Purpose:** Document external ML models, architectures, licensing, and integration boundaries for Forward-Looking Sonar (FLS) marine debris detection.

---

## 1. Reference Repository Overview

| Property | Value |
| :--- | :--- |
| **Repository Name** | `mvaldenegro/marine-debris-fls-datasets` |
| **Originating Institutions**| Department of AI, Bernoulli Institute, University of Groningen (NL)<br>Ocean Systems Laboratory, Heriot-Watt University (UK) |
| **Principal Researcher** | Dr. Matias Valdenegro-Toro |
| **Permanent DOI** | `10.5281/zenodo.15101686` |
| **License** | Creative Commons Attribution 4.0 International (CC-BY 4.0) |
| **Dataset Modality** | Forward-Looking Sonar (FLS) acoustic imagery captured by an ARIS Explorer 3000 (3.0 MHz) acoustic camera |

---

## 2. Discovered Models & Components Audit

| Component | Source File in Reference Repo | Original Purpose | Reusability in MarineDebris-Sonar-AI | Integration Status |
| :--- | :--- | :--- | :--- | :--- |
| **MobileNet** | `md_fls_dataset/models/mobilenet.py` | 12-class debris crop classification | Adapted as secondary verification classifier | ⚠️ `MISSING_WEIGHTS` (Requires task-specific weights) |
| **ResNet** | `md_fls_dataset/models/resnet.py` | Sonar material/object classification baseline | Supported as secondary classifier backend | ⚠️ `MISSING_WEIGHTS` (Requires task-specific weights) |
| **DenseNet** | `md_fls_dataset/models/densenet.py` | Sonar classification benchmark | Supported as secondary classifier backend | ⚠️ `MISSING_WEIGHTS` (Requires task-specific weights) |
| **SqueezeNet** | `md_fls_dataset/models/squeezenet.py` | Lightweight acoustic crop classifier | Supported as secondary classifier backend | ⚠️ `MISSING_WEIGHTS` (Requires task-specific weights) |
| **MiniXception** | `md_fls_dataset/models/minixception.py` | Fast sonar feature extractor | Experimental classifier backend | ⚠️ `MISSING_WEIGHTS` (Requires task-specific weights) |
| **Segmentation Masks** | `data/watertank-segmentation/Masks/` | 1,000 real ground-truth acoustic masks | Direct training target for U-Net/SegFormer | ✅ Acquired & mapped to canonical debris classes |
| **YOLOv8m Detector** | Native to MarineDebris-Sonar-AI | Primary multi-target 640x640 detector | Primary detection engine | ⚠️ `MISSING_WEIGHTS` (Task checkpoint pending training) |

---

## 3. Truthful Architectural Role Definitions

> [!IMPORTANT]
> **Anti-Fabrication & Weight Status Transparency:**
> 1. **Primary Detector (YOLOv8m):** Remains the primary object detector. It is **NOT** represented as pre-trained on this exact dataset. Until a task-specific checkpoint is produced and validated, its runtime status is strictly reported as `MISSING_WEIGHTS`.
> 2. **Semantic Segmenter (U-Net / SegFormer):** Designed to produce refined pixel-accurate masks for detected candidate bounding boxes. Until verified task weights are supplied, it reports `status: "unavailable"`.
> 3. **Secondary Classifier (MobileNet / ResNet):** An optional verification stage for candidate crops. Until task weights are verified, it reports `status: "unavailable"`. Under no circumstances will an unverified classifier override YOLO predictions.

---

## 4. Adaptation Strategy

- **PyTorch / OpenCV Standardization:** The reference repository wrote standalone Keras models. In MarineDebris-Sonar-AI, we define clean, framework-agnostic interfaces (`BaseDetector`, `BaseSegmenter`, `ClassifierBackend`) under `backend/ml/`.
- **Graceful Unavailability:** When weights are missing, the pipeline logs clear warnings and continues survey ingestion without fabricating predictions, masks, or classifications.
- **Licensing Compliance:** Full academic attribution is preserved in all derivative configurations, manifests, and documentation under CC-BY 4.0.
