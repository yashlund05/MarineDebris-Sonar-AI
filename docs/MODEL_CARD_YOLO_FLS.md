# Model Card — MarineDebris YOLOv8 FLS Detector

## 1. Model Details
- **Model Name:** `sonar_yolov8_fls_trained.pt`
- **Architecture:** Ultralytics YOLOv8 (Anchor-Free Detection with TaskAlignedAssigner, 73 layers, 3,006,623 parameters)
- **Model Version:** `v2.0.0-fls-optimized`
- **Model Type:** 2D Bounding Box Acoustic Object Detector
- **Input Resolution:** $640 \times 640 \times 3$ (Letterboxed single-channel acoustic backscatter mapped to 3-channel input)
- **Framework:** PyTorch 2.13.0, Ultralytics 8.4.125
- **License:** Apache 2.0 / Creative Commons Attribution 4.0 International

---

## 2. Intended Use
- **Primary Task:** Automated detection, classification, and bounding-box localization of underwater marine debris and anthropogenic targets in Forward-Looking Sonar (FLS) acoustic imagery.
- **Supported Classes:**
  - `0`: `derelict_fishing_gear`
  - `1`: `general_marine_debris`
  - `2`: `shipwreck`
  - `3`: `pipe_or_cylinder`
  - `4`: `other_man_made_target`
- **Target Sensor Modality:** High-frequency acoustic sonar (e.g. ARIS Explorer 3000, 3.0 MHz / 1.8 MHz) and side-scan sonar image strips.

---

## 3. Training & Dataset Provenance
- **Dataset:** Marine Debris Forward-Looking Sonar Dataset (Dr. Matias Valdenegro-Toro, Heriot-Watt University / University of Groningen).
- **Permanent DOI:** `10.5281/zenodo.15101686`
- **Image Count:** 238 acoustic frames (Train: 166, Validation: 35, Test: 37).
- **Annotation Count:** 371 ground-truth bounding boxes (Train: 266, Validation: 51, Test: 54).
- **Sequence Splitting:** Group-based sequence block partitioning with verified 0% cross-split leakage.
- **Optimizer:** AdamW ($\text{lr}_0 = 0.001$, $\text{lr}_f = 0.01$, $\text{weight\_decay} = 0.0005$, $\text{momentum} = 0.937$).
- **Acoustic Augmentation Policy:** Gain jitter ($\pm 15\%$), horizontal swath flip ($50\%$), rotation ($\pm 5^\circ$), translation ($\pm 5\%$), and mosaic closure for the final 10 epochs. All RGB hue/saturation jitter disabled.

---

## 4. Evaluation Metrics (Real Executed Benchmarks)

### Validation Split (35 images, 51 instances)
- **Precision:** `0.8955` (89.55%)
- **Recall:** `0.8338` (83.38%)
- **F1 Score:** `0.8635`
- **mAP@50:** `0.8987` (89.87%)
- **mAP@50-95:** `0.6089` (60.89%)

### Held-Out Test Split (37 images, 54 instances)
- **Precision:** `0.9325` (93.25%)
- **Recall:** `0.9015` (90.15%)
- **F1 Score:** `0.9167`
- **mAP@50:** `0.8921` (89.21%)
- **mAP@50-95:** `0.6235` (62.35%)

---

## 5. Latency & Resource Requirements
- **Inference Latency (CPU, Intel i5-13450HX):** Mean **105.33 ms** / Median **100.26 ms** / P95 **143.55 ms**.
- **Preprocessing Latency:** **3.45 ms** (CLAHE + Normalization).
- **End-to-End Pipeline Turnaround:** **108.81 ms** (~9.2 FPS on CPU).
- **Model Checkpoint Size:** **6.25 MB** (weights only).

---

## 6. Known Limitations & Failure Modes
- **Far-Range Low-Contrast Targets:** Targets in distant sonar swaths with diffuse acoustic returns and low signal-to-noise ratio (SNR) may require confidence thresholds $\le 0.25$ for complete discovery.
- **Modal Differences:** Model is specialized for high-frequency acoustic backscatter (1.8–3.0 MHz); performance on optical RGB or low-frequency sub-bottom profiling will degrade.
