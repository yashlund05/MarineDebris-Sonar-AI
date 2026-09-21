# Sonar Detection Baseline Reproduction & Performance Benchmark Report

**Evaluation Date**: 2026-09-19  
**Model Name**: `sonar_yolov8_fls_trained.pt`  
**Model Checkpoint Path**: `models/detection/sonar_yolov8_fls_trained.pt`  
**Cryptographic SHA-256**: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`  
**Status**: **REPRODUCED & CRYPTOGRAPHICALLY VERIFIED**

---

## 1. Executive Summary

This report establishes the verified performance baseline of the frozen production YOLOv8 detector within `MarineDebris-Sonar-AI`. In strict accordance with the repository's research safeguards:
- The production checkpoint was verified bit-for-bit against its golden SHA-256 digest prior to evaluation.
- The model was benchmarked using the frozen evaluation contract across both canonical benchmark operating points ($\text{conf}=0.001, \text{IoU}=0.70$) and operational deployment points ($\text{conf}=0.25, \text{IoU}=0.45$).
- Evaluations were conducted on genuine real-world forward-looking sonar (FLS) test splits: legacy V2 clean test set, production V3 held-out test set, and the 84-frame hard-negative suite.
- Zero synthetic metrics or fabricated results were used.

---

## 2. Model Architecture & System Environment

| Parameter | Specification |
| :--- | :--- |
| **Model Family** | Ultralytics YOLOv8n (Forward-Looking Sonar) |
| **Layers (Fused)** | 73 layers |
| **Parameter Count** | 3,006,623 parameters |
| **Computational Complexity** | 8.1 GFLOPs |
| **Input Shape** | $640 \times 640 \times 3$ (Canonical normalized acoustic intensity) |
| **Inference Hardware** | Intel(R) Core(TM) i5-13450HX CPU (Multi-threaded) |
| **Torch / Ultralytics Engine** | PyTorch 2.13.0+cpu / Ultralytics 8.4.125 |

---

## 3. Canonical Benchmark Performance Matrix

### 3.1 Benchmark A: Legacy V2 Clean Test Split (Frozen Ground Truth)
*Split details: 37 images, 54 annotated debris instances, zero negative background frames.*

| Operating Point | Confidence | IoU | Precision | Recall | F1 Score | mAP@50 | mAP@50-95 | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Canonical Benchmark** | 0.001 | 0.70 | **0.9325** | **0.9015** | **0.9167** | **0.8921** | **0.6235** | **EXACT MATCH** |
| **Operational Mission** | 0.250 | 0.45 | **0.9559** | **0.7931** | **0.8669** | **0.7766** | **0.5447** | **VERIFIED** |

*Note: The canonical benchmark operating point perfectly replicates the historical benchmark record (mAP@50 = 0.8921, Precision = 0.9325, Recall = 0.9015).*

### 3.2 Benchmark B: Dataset V3 Held-Out Real Test Split
*Split details: 80 images, 127 annotated debris instances, 3 native background frames.*

| Metric | Measured Value | Standard Deviation ($\sigma$) |
| :--- | :--- | :--- |
| **mAP@50** | **0.9192** (91.92%) | $\pm 0.002$ |
| **mAP@50-95** | **0.6402** (64.02%) | $\pm 0.003$ |
| **Precision** | **0.9092** (90.92%) | $\pm 0.004$ |
| **Recall** | **0.9024** (90.24%) | $\pm 0.003$ |
| **F1 Score** | **0.9058** (90.58%) | $\pm 0.003$ |

### 3.3 Benchmark C: Hard-Negative Acoustic Clutter Suite
*Suite details: 84 verified non-debris sonar frames (60 flooded quarry sweeps + 24 tank boundary sweeps).*

| Metric | Measured Value | Operational Implication |
| :--- | :--- | :--- |
| **Total Negative Images Evaluated** | 84 frames | Genuine background clutter |
| **Flagged Images (False Alarms)** | 18 frames | Operator distraction risk |
| **Total False Positive Boxes** | 18 detections | False alerts generated |
| **Image-level False Alarm Rate (FAR)** | **21.43%** | **Primary target for improvement** |
| **Quarry Sediment False Positives** | 18 detections | Seabed reverberation confusion |
| **Acoustic Tank Wall False Positives** | 0 detections | Multipath rejection successful |
| **Mean FP per Negative Frame** | 0.214 | Bounded spurious rate |

---

## 4. Inference Latency & Throughput

Measured over 20 timed evaluation runs on CPU ($640 \times 640$ resolution) following 5 warmup iterations:

| Latency Metric | Measured Runtime | Operational SLA / Budget | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Mean Latency** | 80.77 ms | $\le 125.0\text{ ms}$ | **PASS** |
| **P50 Latency** | 80.47 ms | $\le 120.0\text{ ms}$ | **PASS** |
| **P95 Latency** | 85.57 ms | $\le 125.0\text{ ms}$ | **PASS** |
| **Max Latency** | 85.70 ms | $\le 150.0\text{ ms}$ | **PASS** |
| **Throughput** | **12.38 FPS** | $\ge 8.0\text{ FPS}$ | **PASS** |

---

## 5. Core Failure Modes & Error Analysis

The baseline error audit reveals three specific performance bottlenecks in the production detector:
1. **High False Alarm Rate on Reverberant Seabed (21.43% FAR)**:
   Rough quarry sediments and natural gravel beds trigger false positive alarms under low grazing angles.
2. **Operational Recall Degradation (79.31% at conf=0.25)**:
   While canonical recall is 90.15% at conf=0.001, operational filtering drops faint, low-contrast debris detections.
3. **Small Target Localization Errors**:
   Debris targets under 40 px in acoustic dimension exhibit lower boundary precision due to speckle blur and downsampling.

---

## 6. Target Improvement Thresholds for Candidate Models
To achieve promotion eligibility under the `PromotionGate` policy, any candidate model must satisfy:
1. $\Delta \text{mAP50 (V2 Test)} \ge -1.0\%$ (Zero unacceptable regression on legacy baseline)
2. $\Delta \text{Recall (V2 Test)} \ge -2.0\%$ (Maintain detection sensitivity)
3. $\text{FAR on Hard Negatives} \le 21.43\%$ (Must reduce or match false alarms)
4. $\text{P95 CPU Latency} \le 125.0\text{ ms}$ (Must maintain real-time embedded edge compliance)
