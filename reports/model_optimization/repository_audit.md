# MarineDebris-Sonar-AI — Phase 2 Repository Audit

**Date:** 2026-09-04  
**Auditor:** AntiGravity ML Optimization Engineer  
**Scope:** Machine Learning Training, Evaluation, Model Architecture, Dataset, and Deployment Configuration  
**Status:** Audit Complete & Verified  

---

## 1. System & ML Architecture Overview

| Component | Audit Observation / Value | Verification Source |
| :--- | :--- | :--- |
| **YOLO Framework** | `Ultralytics 8.4.125` | `pip show ultralytics` |
| **Model Architecture** | `YOLOv8n` (Anchor-free detection head, decoupled regression/classification) | `backend/ml/training/train_yolo.py` |
| **Parameter Count** | `3,006,623` parameters (73 fused layers) | `model.val()` summary |
| **Computational Complexity** | `8.1 GFLOPs` at 640x640 resolution | Model profile |
| **Pretrained Initialization** | ImageNet-pretrained `yolov8n.pt` backbone | `train_yolo_experiment()` |
| **Input Spatial Dimensions** | `640 x 640 x 3` letterbox padded canvas | `ImageNormalizer`, `data.yaml` |
| **Acoustic Channels** | 3-channel replicated grayscale ($G \to G, G, G$) | `backend/ml/datasets/normalize.py` |
| **Execution Hardware** | 13th Gen Intel Core i5-13450HX (16 vCPUs, 8 active PyTorch threads) | `torch.get_num_threads()` |
| **Inference Accelerator** | CPU (AVX2 / OpenMP parallelized) | PyTorch CPU runtime |

---

## 2. Training Hyperparameters & Loss Configuration

| Hyperparameter | Value | Scientific Rationale |
| :--- | :---: | :--- |
| **Optimizer** | `AdamW` | Decoupled weight decay prevents gradient explosion on sparse acoustic targets. |
| **Initial Learning Rate (`lr0`)** | `0.001` | Conservative baseline rate for fine-tuning acoustic representations. |
| **Final Learning Rate Ratio (`lrf`)** | `0.01` | Cosine annealing decay to `1e-5`. |
| **Weight Decay** | `0.0005` | $L_2$ regularization for model generalization. |
| **Warmup Epochs** | `3.0` | Stabilizes optimizer momentum before full learning rate is engaged. |
| **Warmup Momentum** | `0.80` | Smooth transition into standard momentum (`0.937`). |
| **Box Loss Weight (`box`)** | `7.5` | Elevated bounding box regression penalty for precise sonar target localization. |
| **Class Loss Weight (`cls`)** | `0.5` | Standard binary cross-entropy classification weight. |
| **Distribution Focal Loss (`dfl`)** | `1.5` | Fine-grained bounding box corner regression. |
| **Early Stopping Patience** | `15 epochs` | Monitored against validation fitness metric ($0.1 \times \text{mAP50} + 0.9 \times \text{mAP50-95}$). |

---

## 3. Acoustic Domain Data Augmentations

Acoustic imagery differs fundamentally from natural RGB photography. The audit verified that arbitrary color transformations are strictly disabled:

| Augmentation Parameter | Value | Physical Sonar Rationale |
| :--- | :---: | :--- |
| **Hue Jitter (`hsv_h`)** | `0.0` | **Disabled.** Acoustic sonar contains no hue; false color destroys physical fidelity. |
| **Saturation Jitter (`hsv_s`)** | `0.0` | **Disabled.** Grayscale acoustic returns have zero saturation. |
| **Value / Intensity Jitter (`hsv_v`)** | `0.15` | Models acoustic transmission loss and sonar receiver gain adjustments. |
| **Rotation (`degrees`)** | `5.0` | Simulates minor vehicle yaw/pitch perturbation without inverting seabed geometry. |
| **Translation (`translate`)** | `0.05` | Small sensor translation across acoustic swathes. |
| **Scaling (`scale`)** | `0.10` | Simulates small range variations without aliasing sonar speckle patterns. |
| **Horizontal Flip (`fliplr`)** | `0.50` | Models left/right acoustic swath symmetry. |
| **Vertical Flip (`flipud`)** | `0.0` | **Disabled.** Range axis is directional (transducer near-range to far-range attenuation). |
| **Mosaic (`mosaic`)** | `0.20` | Controlled low-probability mosaic to present varied acoustic clutter context. |

---

## 4. Inference, Thresholding & Non-Maximum Suppression (NMS)

| Evaluation Parameter | Value | Operational Context |
| :--- | :---: | :--- |
| **Default Detection Confidence** | `0.25` / `0.30` | Balanced operational threshold for ROV/AUV live feed. |
| **Confidence Sweep Range** | `0.05` to `0.80` | Multi-threshold calibration to map High Recall vs High Precision operating curves. |
| **NMS IoU Threshold** | `0.45` | Standard overlap suppression for acoustic bounding boxes. |
| **Tested NMS Sweep Range** | `0.40` to `0.70` | Evaluates duplicate suppression vs overlapping debris detection. |
| **Max Detections per Image** | `300` | Standard YOLO upper bound. |

---

## 5. Dataset Architecture & Split Partitioning

### 5.1 Legacy Control Baseline (`datasets/sonar_debris_v2_clean`) — FROZEN
- **Train Split:** 161 images (254 annotations)
- **Validation Split:** 40 images (63 annotations)
- **Held-Out Test Split:** 37 images (54 annotations)
- **Status:** `BASELINE_DATASET_FROZEN = TRUE` (Immutable control benchmark).

### 5.2 Expanded Dataset V3 (`datasets/sonar_debris_v3`) — FROZEN
- **Total Real Images:** 660
- **Total Annotations:** 899
- **Total Negative Background Images:** 84 (60 flooded quarry seabed + 24 acoustic wall returns)
- **Acoustic Sequences:** 36 continuous sequence blocks
- **Train Split:** 480 images (636 annotations, 75 negatives)
- **Validation Split:** 100 images (136 annotations, 6 negatives)
- **Test Split:** 80 images (127 annotations, 3 negatives)
- **Cross-Split Sequence Leakage:** **0% (100% PASS)**

---

## 6. Active Production Model Baseline

| Metric | Production Baseline (`models/detection/sonar_yolov8_fls_trained.pt`) |
| :--- | :---: |
| **Model SHA256** | `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7` |
| **Status** | `PRODUCTION_MODEL_FROZEN = TRUE` |
| **Legacy Test Precision** | `93.25%` |
| **Legacy Test Recall** | `90.15%` |
| **Legacy Test F1** | `0.9167` |
| **Legacy Test mAP50** | `89.21%` |
| **Legacy Test mAP50-95** | `62.35%` |
| **CPU Preprocessing Latency** | `3.45 ms` |
| **CPU Inference Latency** | `105.33 ms` |
| **CPU Total Pipeline Latency** | `108.81 ms (~9.2 FPS)` |

---

## 7. Protection Guard Confirmation

The protection flag has been verified in [`reports/model_optimization/PROTECTION_LOCK`](file:///c:/Users/ARYAN%20-%20AYUSH/OneDrive/Desktop/Marine%20sonar/reports/model_optimization/PROTECTION_LOCK):
```
BASELINE_DATASET_FROZEN = TRUE
PRODUCTION_MODEL_FROZEN = TRUE
```
Any attempt to overwrite production assets or mutate legacy test benchmarks will terminate execution immediately.
