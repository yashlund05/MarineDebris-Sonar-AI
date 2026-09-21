# Sonar Image Enhancement Subsystem — Implementation Plan & Delivery Record

## Executive Summary

This document records the design, engineering execution, mathematical specifications, and empirical validation of the **Modular Sonar Image Enhancement Subsystem** implemented inside the `MarineDebris-Sonar-AI` repository.

The subsystem addresses the core challenges of Forward-Looking Sonar (FLS) and Side-Scan Sonar (SSS) imaging:
- Multiplicative speckle clutter
- Radiometric attenuation and low contrast
- Sensor stripe artifacts
- Down-range acoustic shadow attenuation

Critically, the subsystem establishes an **AI-Safe guarantee**: visual enhancements intended for human operators are decoupled and mathematically prevented from introducing false positives, hallucinations, or edge deformations that degrade downstream YOLOv8 object detection accuracy.

---

## 1. Architectural Blueprint & Subsystem Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       INGESTION & INSPECTION STAGE                       │
│  - inspect_sonar_input(): FLS vs SSS, saturation, dead columns, dB      │
│  - safe_percentile_normalization() & double-log conversion guard        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     MODULAR MULTI-STAGE PIPELINE                        │
│                                                                         │
│  Stage 1: StripeNoiseNotchStage                                          │
│           - 2D-FFT directional spectrum analysis                        │
│           - Confidence-gated notch filtering (>0.40 threshold)          │
│                                                                         │
│  Stage 2: SpeckleDenoisingStage                                          │
│           - Lee multiplicative speckle filter (k=3, 5)                  │
│           - Frost exponentially-damped filter                           │
│           - SRAD (Speckle Reducing Anisotropic Diffusion PDE)          │
│                                                                         │
│  Stage 3: AdaptiveContrastStage                                         │
│           - Contrast Limited Adaptive Histogram Equalization (CLAHE)    │
│           - Controlled unsharp masking with halo clipping               │
│           - AI-Safe Gate: skips oversharpening in AI_SAFE mode          │
│                                                                         │
│  Stage 4: AcousticShadowPreservationStage                               │
│           - Down-range shadow void detection via morphology             │
│           - Area retention & boundary gradient preservation check       │
│           - Forensic safety alerting if shadow eroded > 25%             │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    DECOUPLED OUTPUT PRESENTATION                        │
│                                                                         │
│   CANONICAL GREYSCALE [0.0, 1.0]          DISPLAY PSEUDOCOLOR           │
│   - Immutable single-channel float32     - 8-bit RGB color LUTs         │
│   - Consumed by YOLOv8 detector          - ARIS Amber, Thermal, Inferno │
│   - Zero false color artifacts           - Human operator workstation   │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Standard Operational Profiles (Hypotheses & Target Conditions)

| Profile ID | Processing Mode | Pipeline Stages | Target Operational Scenario | AI-Safe Status |
|---|---|---|---|---|
| **`RAW`** | `AI_SAFE` | Identity pass-through | Baseline scientific control, pure sensor audit | **Guaranteed AI-Safe** |
| **`MINIMAL`** | `AI_SAFE` | Lee filter ($k=3$), Gentle CLAHE ($\text{clip}=1.2$) | Calm waters, low turbidity, conservative debris boundaries | **Guaranteed AI-Safe** |
| **`BALANCED`** | `AI_SAFE` | Stripe notch, Lee filter ($k=5$), CLAHE ($\text{clip}=1.8$), Shadow check | Standard coastal and estuary patrol | **Guaranteed AI-Safe** |
| **`HUMAN_VISUAL`** | `HUMAN_DISPLAY` | Stripe notch, Bilateral denoise, CLAHE ($\text{clip}=2.2$), Unsharp boost, Shadow check | Human operator workstation inspection of faint targets | **Operator Display Only** |
| **`AI_SAFE`** | `AI_SAFE` | Conservative Lee, CLAHE ($\text{clip}=1.5$), Zero unsharp, Strict shadow audit | Direct input to downstream YOLOv8 detector | **Guaranteed AI-Safe** |
| **`RESEARCH_CUSTOM`** | Configurable | Parametric stage activation | Algorithmic research, ablation benchmarks | Dependent on config |

---

## 3. Mathematical Metric Formulations & Ground Truth Integrity

### 3.1 Equivalent Number of Looks (ENL)
$$\text{ENL} = \frac{\mu_{\text{ROI}}^2}{\sigma_{\text{ROI}}^2}$$
- **Constraint**: Evaluated strictly on non-target homogeneous seabed or water column patches ($\ge 64\text{ px}$). Full-frame ENL is mathematically invalid.

### 3.2 Contrast-to-Noise Ratio (CNR)
$$\text{CNR} = \frac{|\mu_{\text{target}} - \mu_{\text{background}}|}{\sqrt{\sigma_{\text{target}}^2 + \sigma_{\text{background}}^2}}$$
- **Constraint**: Target interior is derived by eroding the ground-truth annotation by $30\%$; background is an annular ring expanded around the target by $60\%$.

### 3.3 Edge Preservation Index (EPI)
$$\text{EPI} = \frac{\sum |\nabla^2 I_{\text{enhanced}}|}{\sum |\nabla^2 I_{\text{original}}|}$$
- **Mathematical Invariant**: $\text{EPI}(I, I) = 1.0000$. Values $> 1.15$ indicate high-frequency noise amplification; $< 0.85$ indicate boundary blurring.

### 3.4 Acoustic Shadow Retention Ratio (SRR)
$$\text{SRR} = \frac{\text{Area}(S_{\text{enhanced}})}{\text{Area}(S_{\text{original}})}$$
- Where $S$ is the binary mask of acoustic voids ($I \le \text{percentile}_{12}$). A warning is flagged if $\text{SRR} < 0.75$.

---

## 4. Verification & Testing Matrix

1. **Unit & Mathematical Tests** (`tests/backend/test_sonar_enhancement.py`):
   - 24 tests covering 8 classical methods, LUT monotonicity, ENL/CNR/EPI mathematical invariants, and zero-metric-fabrication error handling.
2. **Modular Pipeline Tests** (`tests/backend/test_sonar_enhancement_pipeline.py`):
   - 18 tests covering input inspection, signal domain conversions, FFT notch filtering, Lee/Frost/SRAD speckle denoising, shadow preservation diagnostics, adaptive contrast gating, learned denoiser adapters, and standard profile factory.
3. **Integration & Production Contract Tests** (`tests/backend/test_sonar_enhancement_integration.py`):
   - 9 tests validating model SHA-256 immutability, canonical float32 contract, pseudocolor presentation decoupling, caching, and path security.
4. **Detector Utility Benchmark** (`scripts/evaluate_profiles_detector_utility.py`):
   - Automated validation of detection precision, recall, and F1 across operational profiles using the frozen production detector.
