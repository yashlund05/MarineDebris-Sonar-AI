# Model Card: YOLOv8 FLS Marine Debris Detector (V3 Candidate Series)

## 1. Model Details
- **Model Name:** YOLOv8n-FLS-V3
- **Model Type:** Acoustic Object Detector (Ultralytics YOLOv8 Nano)
- **Parameters:** 3,006,623 (3.01M)
- **GFLOPs:** 8.1 GFLOPs @ 640x640
- **Input Modality:** Single-channel acoustic Forward-Looking Sonar (FLS) image (ARIS Explorer 3000 / BlueView M900), converted to 3-channel grayscale/colormap.
- **Input Dimensions:** 640x640 pixels, letterboxed with gray padding.
- **Weights Location:** `models/detection/experiments/yolov8_fls_v3_candidate.pt`
- **Active Production Baseline:** `models/detection/sonar_yolov8_fls_trained.pt` (SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`)
- **License:** Apache 2.0 / Academic Research Use

---

## 2. Intended Use & Target Deployments
- **Primary Use:** Real-time forward-looking sonar perception for Autonomous Underwater Vehicles (AUVs) and Remotely Operated Vehicles (ROVs).
- **Target Applications:**
  - Automated benthic litter surveying and density mapping.
  - Derelict fishing gear ("ghost net") identification and localization.
  - Subsea hazard warning and collision avoidance during low-altitude acoustic sweeps.
- **Out-of-Scope Use:**
  - Optical RGB underwater cameras (requires color/light attenuation models).
  - Bathymetric multibeam echo-sounders (MBES) point cloud processing.
  - Surface navigation or radar detection.

---

## 3. Training & Validation Datasets
- **Dataset:** Dataset V3 (Expanded Real Sonar)
- **Data Manifest SHA256:** `datasets/sonar_debris_v3/DATASET_MANIFEST.json`
- **Total Real Images:** 660 (576 positive, 84 verified negative)
- **Total Bounding Boxes:** 899 across 5 classes
- **Splits:**
  - **Train:** 480 images (636 bounding boxes, 26 sequences)
  - **Val:** 100 images (136 bounding boxes, 5 sequences)
  - **Test:** 80 images (127 bounding boxes, 5 sequences)
- **Sequence Isolation:** Zero sequence leakage between train, val, and test splits.

---

## 4. Evaluated Performance Benchmarks

| Evaluation Benchmark | Test Set Scale | Production Control (`trained.pt`) | V3 Candidate (`v3_candidate.pt`) | Delta ($\Delta$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Benchmark 1: Legacy V2 Control** | 37 images / 54 boxes | **77.72% mAP50** (F1: 0.8669) | 68.98% mAP50 (F1: 0.7969) | -8.74% mAP50 | Regression |
| **Benchmark 2: Dataset V3 Held-out** | 80 images / 127 boxes | **85.88% mAP50** (F1: 0.9016) | 65.13% mAP50 (F1: 0.7760) | -20.75% mAP50 | Regression |
| **Benchmark 3: Hard Negatives FAR** | 84 clutter frames | 21.43% FAR (18 FPs) | **14.29% FAR** (13 FPs) | -7.14% FAR | Improved |
| **Benchmark 4: Cross-Domain** | 82 images / 136 boxes | **33.80% mAP50** | 25.50% mAP50 | -8.30% mAP50 | Baseline higher |
| **Inference Latency (CPU)** | 640x640 batch 1 | 41.97 ms (23.8 FPS) | 41.50 ms (24.1 FPS) | -0.47 ms | Equivalent |

---

## 5. Calibrated Operating Modes

Based on validation split sweeps with the production control model:

| Operating Mode | Confidence Threshold | NMS IoU | Precision | Recall | F1 Score | Mission Profile |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Balanced** | **0.25** | **0.45** | 93.39% | 84.05% | **0.8848** | Routine AUV mapping and survey logging |
| **High Recall** | **0.05** | **0.45** | 92.51% | 84.05% | 0.8808 | Search & rescue, navigation safety alerts |
| **High Precision** | **0.45** | **0.45** | 94.79% | 78.56% | 0.8591 | ROV manipulator arm grasping, recovery |

---

## 6. Hardware & Deployment Recommendations
- **Edge Deployment (NVIDIA Jetson Orin Nano / Xavier NX):**
  - TensorRT FP16: Expected latency ~8.5 ms (115+ FPS).
  - VRAM Footprint: ~450 MB.
- **CPU Deployment (Industrial PC / AUV Core i5/i7):**
  - PyTorch CPU / ONNX Runtime: Measured latency 41.97 ms (23.8 FPS).
  - Memory Footprint: ~220 MB RAM.
- **Acoustic Preprocessing Requirement:**
  - Forward-looking sonar polar fan-beam reconstruction to Cartesian coordinates.
  - CLAHE (Contrast-Limited Adaptive Histogram Equalization) with clip limit 2.0.
  - Bilateral noise filtering (diameter 5, $\sigma_{color}=50$, $\sigma_{space}=50$).

---

## 7. Governance & Promotion Decision
- **Promotion Status:** **REJECTED (PRODUCTION CONTROL RETAINED)**
- **Audit Date:** 2026-09-04
- **Justification:** While the candidate model improved false alarm rejection on acoustic wall clutter (-7.14% FAR), it suffered significant recall regression across both the legacy benchmark (-8.74% mAP50) and the held-out V3 test benchmark (-20.75% mAP50).
- In accordance with production governance rules, `sonar_yolov8_fls_trained.pt` remains the active production checkpoint.
