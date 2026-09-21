# Sonar Image Enhancement & Visibility Engine — System Architecture

## 1. System Overview & Invariants

The **Intelligent Sonar Image Enhancement Engine** provides deterministic, scientific acoustic visibility enhancement for Forward-Looking Sonar (FLS) streams from the Sound Metrics ARIS Explorer 3000 (3.0 MHz / 1.8 MHz).

### Core Invariants
1. **Canonical Output Guarantee**: The primary output of every enhancement algorithm is a 2D single-channel matrix of type `float32` bounded in $[0.0, 1.0]$.
2. **Display-Only Pseudocolor**: Pseudocolor transformations (ARIS Copper/Amber, Monotonic Thermal, Inferno) are non-canonical, 8-bit RGB presentation layers designed strictly for human operator visibility. Pseudocolor is programmatically prohibited from being ingested by object detectors or acoustic metric routines.
3. **Zero Metric Fabrication**: Acoustic evaluation metrics (ENL, CNR, EPI) must never fabricate values or return arbitrary scores upon failure. Invalid or out-of-spec samples return `MetricStatus.NOT_MEASURABLE` with explicit forensic failure rationales.
4. **Frozen Production Model**: The trained YOLOv8 FLS detector checkpoint (`models/detection/sonar_yolov8_fls_trained.pt`, SHA256: `e1215c7e...`) is never overwritten, fine-tuned, or modified without passing full promotion gates.

---

## 2. Benchmark Data Policy & Sequence Isolation

The dataset file `datasets/sonar_debris/sample_annotation_viz.png` is strictly a UI/API smoke-test asset and is **never** used for scientific evaluation or algorithm selection.

```
┌─────────────────────────────────────────────────────────────┐
│                    ARIS 3000 ACOUSTIC DATA                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    DEVELOPMENT & SELECTION          FROZEN HELD-OUT EVAL
    - V2 Train + Validation          - V2 Test (Held-Out)
    - V3 Train + Validation          - V3 Test (Held-Out)
    - Sequence-Isolated Groups       - 84 Hard Negatives (Quarry/Wall)
               │                               │
               ▼                               ▼
    - Algorithm Comparison           - Final Gate Evaluation
    - Parameter Optimization         - Detector Utility Audit
    - Profile Formulation            - Release Sign-Off
```

Frames from the same continuous acquisition sequence are strictly isolated into identical partitions, preventing temporal leakages across train, validation, and test splits.

---

## 3. Acoustic Metrics & Deterministic ROI Derivation

### 3.1 Equivalent Number of Looks (ENL)
$$\text{ENL} = \frac{\mu_{\text{ROI}}^2}{\sigma_{\text{ROI}}^2}$$
- **Evaluation Region**: Strictly evaluated on homogeneous background ROIs (seabed clutter or water column devoid of targets/shadow boundaries).
- **Rule**: Full-image ENL is prohibited as target edges artificially inflate variance $\sigma^2$.
- **Validity Gate**: $\text{area}(\text{ROI}) \ge 64\text{ px}$, $\sigma_{\text{ROI}} > 10^{-7}$, $\mu_{\text{ROI}} > 10^{-7}$.

### 3.2 Contrast-to-Noise Ratio (CNR)
$$\text{CNR} = \frac{|\mu_{\text{target}} - \mu_{\text{background}}|}{\sqrt{\sigma_{\text{target}}^2 + \sigma_{\text{background}}^2}}$$
- **ROI Derivation**:
  1. **Target ROI**: Centroid-eroded interior of the ground-truth annotation bounding box ($\ge 30\%$ margin shrinkage).
  2. **Background ROI**: Morphologically expanded annular ring surrounding the target ($d \in [5, 20]\text{ px}$ buffer), excluding the target box.
- **Validity Gate**: Target and background regions must each contain $\ge 16\text{ px}$. If invalid, returns `NOT MEASURABLE`.

### 3.3 Edge Preservation Index (EPI)
$$\text{EPI} = \frac{\sum_{(x,y)} |\nabla^2 I_{\text{enhanced}}(x,y)|}{\sum_{(x,y)} |\nabla^2 I_{\text{original}}(x,y)|}$$
- **Mathematical Invariant**: $\text{EPI}(I_{\text{original}}, I_{\text{original}}) \equiv 1.00000$.

---

## 4. Pipeline Insertion Points & Controlled Ablation

```
                  ┌───────────────────────────────────┐
                  │         RAW ACOUSTIC FRAME        │
                  └─────────┬───────────────┬─────────┘
                            │               │
                            │ [P0/P2]       │ [Production / P1]
                            ▼               ▼
                   ┌────────────────┐   ┌───────────────────────────┐
                   │  ENHANCEMENT   │   │  PRODUCTION PREPROCESSING │
                   │     ENGINE     │   │  - Quality Assessment     │
                   └────────┬───────┘   │  - Bottom Line Tracking   │
                            │           │  - Water Column Removal   │
                 ┌──────────┴────────┐  │  - Min-Max Normalization  │
                 ▼                   ▼  │  - CLAHE (clip=2.0)       │
          [P0: Display]       [P2: ML]  │  - Median Filter (k=3)    │
                 │                   │  │  - Slant Range Correction │
                 ▼                   │  │  - 640x640 Tiler          │
          ┌─────────────┐            │  └─────────────┬─────────────┘
          │ DISPLAY LUT │            │                │
          │ ARIS Amber  │            ▼                ▼
          └─────────────┘       ┌────────────────────────┐
                                │       ENHANCED P1      │
                                └─────────────┬──────────┘
                                              │
                                              ▼
                                   ┌─────────────────────┐
                                   │  YOLOv8 FLS DETECT  │
                                   └─────────────────────┘
```

- **P0**: Raw $\rightarrow$ Enhancement $\rightarrow$ Display LUT (Human Workstation View)
- **P1**: Production Preprocessing $\rightarrow$ Enhancement $\rightarrow$ YOLOv8
- **P2**: Raw $\rightarrow$ Enhancement $\rightarrow$ Production Preprocessing $\rightarrow$ YOLOv8
- **P3**: Production Preprocessing without CLAHE $\rightarrow$ Enhancement $\rightarrow$ YOLOv8

---

## 5. Promotion Gate & Final Classification Matrix

Every enhancement candidate is evaluated through multi-dimensional gates and classified into exactly one status:

| Promotion Status | Criteria | Action |
|---|---|---|
| **PRODUCTION DISPLAY ENHANCER** | Operator clarity score $>90\%$, no false contour artifacts, latency $<10\text{ ms}$. | Default display in workstation. |
| **DETECTION PREPROCESSOR CANDIDATE** | $\Delta\text{mAP@50} > +2.0\%$ without regression on hard negatives; latency budget compliant. | Evaluated for detector preprocessing. |
| **HUMAN-INSPECTION ONLY** | Improves contrast for human inspection but alters YOLO feature distributions. | Restricted to operator GUI. |
| **EXPERIMENTAL** | Incomplete benchmark or mixed acoustic fidelity metrics. | Research sandbox only. |
| **REJECTED** | Introduces false contours, edge blurring ($\text{EPI} < 0.5$), or increases false alarms on hard negatives. | Quarantined. |

---

## 6. Modular Multi-Stage Pipeline & Operational Profiles

### 6.1 Architectural Decoupling & Context Propagation
The modular subsystem models sonar processing as an ordered chain of `SonarEnhancementStage` instances managed by `SonarEnhancementPipeline`. State, provenance, and diagnostic masks are propagated through a `SonarEnhancementContext`:

- `validity_mask`: Boolean mask isolating sensor-dead columns, extreme acoustic saturation, or water column mute regions.
- `modified_mask`: Boolean mask indicating which pixels were materially altered by the pipeline.
- `provenance`: Immutable record tracing input artifact ID, modality (FLS vs SSS), signal representation, applied/skipped stages, timestamp, and host device.

### 6.2 Pipeline Stages
1. **`StripeNoiseNotchStage`**: 2D-FFT directional spectrum analysis with confidence-gated notch attenuation.
2. **`SpeckleDenoisingStage`**: Adaptive spatial filtering (Lee multiplicative filter, Frost damped filter, or SRAD PDE).
3. **`AdaptiveContrastStage`**: Parameterized CLAHE with optional gamma correction and controlled unsharp masking.
4. **`AcousticShadowPreservationStage`**: Non-modifying diagnostic stage measuring shadow area retention and contrast ratios.
5. **Learned Adapters (`SEGSIDDenoiserAdapter`, `WFCBSNDenoiserAdapter`, `LBDEnhanceAdapter`)**: Standardized adapters with analytical surrogate fallbacks when deep model checkpoints are unavailable.

### 6.3 Standard Operational Profiles
- **`RAW`**: Identity pass-through baseline.
- **`MINIMAL`**: Gentle Lee filter ($k=3$), minimal CLAHE ($\text{clip}=1.2$).
- **`BALANCED`**: Stripe notch, Lee filter ($k=5$), CLAHE ($\text{clip}=1.8$), shadow preservation.
- **`HUMAN_VISUAL`**: Aggressive CLAHE ($\text{clip}=2.2$), unsharp boost, gamma $0.9$ (restricted to human operators).
- **`AI_SAFE`**: Conservative speckle reduction, strict shadow validation, zero unsharp masking (guaranteed AI-safe).
- **`RESEARCH_CUSTOM`**: Fully parametric configuration for controlled ablation studies.

### 6.4 REST API Endpoints
- `POST /api/v1/enhancement/inspect`: Forensic acoustic inspection of input frames.
- `POST /api/v1/enhancement/pipeline/process`: Modular pipeline execution with profile selection, mask propagation, and optional YOLO detection.
- `GET /api/v1/enhancement/metrics/definitions`: Documentation of acoustic formulas, units, and validity conditions.

