# Sonar Enhancement Subsystem — Operational Limitations & Risk Boundaries

## 1. Domain-Specific Acoustic Constraints

### 1.1 Acoustic Shadow Erosion
- **Mechanism**: Dynamic range equalization (CLAHE) and aggressive spatial filtering can elevate pixel intensities inside true acoustic shadows, shrinking their apparent down-range footprint.
- **Detector Risk**: YOLOv8 models trained on raw sonar rely on the joint signature of specular highlight and acoustic shadow. Eroding the shadow reduces target confidence or causes missed detections.
- **Mitigation**: The `AcousticShadowPreservationStage` actively tracks shadow area retention ($\text{SRR}$). If $\text{SRR} < 0.75$, the pipeline logs an explicit warning and restricts downstream promotion.

### 1.2 Unsharp Masking & Halo Artifacts
- **Mechanism**: High-pass Laplacian or unsharp masking amplifies acoustic boundaries by introducing high-contrast dark and light borders (overshoot halos).
- **Detector Risk**: While visually crisp for human eyes, artificial halos distort bounding box boundary regressions and introduce phantom linear edges.
- **Policy**: Unsharp masking with amount $> 0.30$ is **strictly prohibited in `AI_SAFE` mode** and is restricted to `HUMAN_DISPLAY` mode only.

### 1.3 Stripe Filter Directionality
- **Mechanism**: The 2D-FFT notch filter assumes acoustic scan stripes are strictly aligned with sensor raster axes (horizontal or vertical scan lines).
- **Limitation**: Tilted linear seafloor features (pipelines, mooring chains, long timbers) can exhibit directional energy near the notch filter axes.
- **Mitigation**: Confidence-gated filtering requires $> 0.40$ spectral prominence before applying notches, preventing attenuation of natural linear seabed targets.

---

## 2. Empirical Detector Utility Limitations

Empirical validation on 15 held-out validation samples with the frozen production YOLOv8n-FLS model yielded the following findings:

| Profile | Precision | Recall | F1 Score | Detection Role |
|---|---|---|---|---|
| **`RAW`** | 89.47% | 89.47% | **89.47%** | Optimal default for YOLO detector trained on raw data |
| **`AI_SAFE`** | **92.31%** | 63.16% | 75.00% | High-confidence filtering; reduces false alarms |
| **`BALANCED`** | 90.00% | 47.37% | 62.07% | General operational display |
| **`HUMAN_VISUAL`**| 88.89% | 42.11% | 57.14% | **Human inspection ONLY**; unacceptable detector recall drop |

### Key Takeaways:
1. **Never substitute `HUMAN_VISUAL` for detector input**: High contrast and edge enhancement designed for human eyes alter the low-level acoustic texture distribution, causing a significant reduction in detector recall.
2. **`AI_SAFE` yields highest precision (92.31%)**: Recommended when operational priorities demand minimizing false alarms in high-clutter environments.
3. **`RAW` remains baseline benchmark**: When the detector was trained on unenhanced data, raw signals provide the most balanced F1 performance.

---

## 3. Sensor Modality Constraints

### 3.1 Forward-Looking Sonar (FLS)
- Evaluated and validated primarily for ARIS Explorer 3000 (3.0 MHz / 1.8 MHz) acoustic cameras.
- Assumes radial acoustic beam geometry spanning $30^\circ$ to $120^\circ$ field-of-view.

### 3.2 Side-Scan Sonar (SSS)
- Support for dual-sided towfish imagery (port and starboard channels) operates via geometric aspect-ratio detection ($H \gg W$ or $W \gg H$).
- Slant-range distortion correction must be applied prior to spatial notch filtering.

---

## 4. Hardware & Real-Time Performance Limits

- **Target CPU Budget**: $< 10.0\text{ ms}$ for real-time edge processing at 15 FPS.
- **Current Latencies on 16-Core Host**:
  - `RAW`: $\sim 1.5\text{ ms}$
  - `AI_SAFE` (Lee + CLAHE): $\sim 60\text{ - }78\text{ ms}$ (acceptable for on-demand inspection, optimization required for 30 FPS video streaming)
  - `Frost Filter`: Vectorized approximation implemented; $O(K^2 \cdot H \cdot W)$ complexity makes $K > 7$ unsuitable for live streaming feeds.
