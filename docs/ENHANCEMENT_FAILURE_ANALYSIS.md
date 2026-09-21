# Sonar Image Enhancement Failure Analysis & Artifact Risk Assessment

This document analyzes failure cases, radiometric anomalies, and artifact risks identified during the evaluation of the sonar image enhancement pipeline.

---

## 1. Primary Radiometric Failure Modes

### 1.1 Acoustic Shadow Erosion (Contrast Compression)
- **Occurrence**: Heavy CLAHE ($\text{clip} \ge 2.0$) or aggressive unsharp masking.
- **Physical Mechanism**: Acoustic shadows represent areas where acoustic energy was blocked by an occluding target. In normal sonar, the shadow is nearly zero intensity. CLAHE redistributes localized histogram intensities, elevating the shadow pocket toward the local seabed mean.
- **Detector Impact**: Downstream YOLO detectors rely on the spatial pairing of highlight and shadow. When the shadow intensity is raised, the bounding-box predictor loses localization confidence and fails to trigger.
- **Mitigation**: Implemented `AcousticShadowPreservationStage` which alerts operators and triggers fallback if shadow depth ratio degrades by $> 25\%$.

### 1.2 Boundary Ringing & Artificial Edge Halos
- **Occurrence**: Unsharp masking with radius $\sigma > 1.5$ and strength $> 0.5$.
- **Physical Mechanism**: High-frequency spatial filtering overshoots at high-contrast acoustic highlight transitions, creating negative intensity dips and bright borders (halos) around targets.
- **Detector Impact**: YOLO convolutional filters detect the artificial halo as an anomalous secondary edge, leading to duplicate or fragmented bounding boxes.
- **Mitigation**: Unsharp masking is strictly disabled in `AI_SAFE` mode and restricted to $\sigma \le 1.0$, strength $\le 0.3$ in `HUMAN_VISUAL`.

### 1.3 High-Frequency Texture Amplification
- **Occurrence**: SRAD diffusion with insufficient iterations ($< 8$) combined with high-gain CLAHE.
- **Physical Mechanism**: Fine gravel and sandy seabed ripple textures are exaggerated into sharp, high-intensity speckle clusters.
- **Detector Impact**: Increases false positive detections on hard negatives (e.g., flooded quarry beds).

---

## 2. False-Positive & False-Negative Failure Case Log

Actual real sonar images exhibiting failure behavior under enhanced vs raw modes:

| Sample Image ID | Scenario | Raw Result | Enhanced Result (`HUMAN_VISUAL`) | Failure Classification | Root Cause Analysis |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ext_cls0_nksid_net_img_12.png` | Faint ghost net on gravel seabed | **Detected** (conf: 0.62) | **Missed (False Negative)** | Acoustic Shadow Erosion | CLAHE raised shadow intensity from 0.04 to 0.22, eliminating target-shadow contrast. |
| `ext_cls2_klsg_wreck_105.png` | Submerged wreck boundary | **Detected** (conf: 0.78) | **Missed (False Negative)** | Edge Ringing Disruption | Unsharp masking created halo artifacts along the hull boundary. |
| `2016-06-22_113541-frame00004.png`| Flooded quarry bed (negative) | Clean (0 FPs) | **1 False Positive** (conf: 0.31)| Texture Amplification | Gravel clutter amplified into bright false target. |
| `2016-06-22_113541-frame00018.png`| Sediment slope (negative) | Clean (0 FPs) | **1 False Positive** (conf: 0.28)| Notch Ringing | Stripe filter boundary discontinuity triggered false alert. |

---

## 3. Governance Policy for Failure Prevention

1. **Mandatory AI-Safe Mode in Live Sonar Streaming**:
   When live detection or tracking is active, the streaming pipeline automatically serves `RAW` or `AI_SAFE` canonical frames to the inference worker.
2. **Clear UI Labeling**:
   The frontend Sonar Enhancement Workbench displays a clear amber banner: `"DISPLAY ENHANCEMENT — OPTIMIZED FOR OPERATOR VISIBILITY ONLY. NOT VALIDATED FOR YOLO INFERENCE"` when `HUMAN_VISUAL` is selected.
