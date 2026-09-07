# Sonar Image Improvement System — Architectural Specification

**System**: MarineDebris-Sonar-AI  
**Sensor**: ARIS Explorer 3000 / 3.0 MHz High-Frequency Identification Sonar  
**Status**: PRODUCTION-READY (Classical Validated, Non-Destructive)  
**Primary Detector**: YOLOv8n-FLS (`sonar_yolov8_fls_trained.pt`, SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`)  
**Secondary Classifier**: MobileNetV3-CropConsensus  

---

## 1. Executive Architecture Overview

Forward-Looking Sonar (FLS) acoustic images are governed by complex physical wave propagation phenomena: multiplicative speckle noise (Rayleigh/K-distributed), acoustic acoustic attenuation, beam spreading, multipath surface reverberation, and non-uniform illumination.

The **Intelligent Sonar Image Improvement System** provides a scientifically governed, project-wide subsystem to transform raw, speckled acoustic backscatter into high-contrast, edge-preserved, noise-reduced imagery while guaranteeing **100% Raw Signal Immutability**.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        RAW FLS ACOUSTIC FEED                           │
│             (Unmodified 16-bit / 8-bit Sensor Backscatter)             │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│              CANONICAL ENHANCEMENT SUBSYSTEM (CPU Real-Time)           │
│  - Percentile Range Stretch (P2 - P98 outlier suppression)             │
│  - Bilateral Filtering (Radiometric & Spatial Domain Denoising)        │
│  - Adaptive CLAHE (Localized Acoustic Histogram Equalization)          │
│  - High-Boost Unsharp Masking (Debris Boundary Enhancement)            │
│  ────────────────────────────────────────────────────────────────────  │
│  CANONICAL OUTPUT: float32 [0.0, 1.0] Grayscale Matrix (Single-Channel)│
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   │ (Decoupled Presentation)        │ (Strictly Controlled)
                   ▼                                 ▼
┌────────────────────────────────────┐ ┌─────────────────────────────────┐
│     PRESENTATION COLORMAP LUT      │ │      DOWNSTREAM YOLOv8n-FLS     │
│ - ARIS Amber (Industry Standard)   │ │ - Input: Preprocessed Grayscale │
│ - Monotonic Thermal (Preserved Lum)│ │ - Primary Detector (Bboxes)     │
│ - Inferno (Colorblind Accessible)  │ │ - Immutable Pt Checkpoint       │
│ - Scientific Grayscale             │ │ - Secondary MobileNet Consensus │
└────────────────────────────────────┘ └─────────────────────────────────┘
```

---

## 2. Core Invariants & Scientific Integrity Guarantees

1. **Raw Signal Immutability**:
   - The raw acoustic backscatter data is NEVER overwritten, modified in-place, or discarded.
   - Operators can toggle back to the raw signal instantly via the default `RAW` mode on any view.
2. **Canonical Grayscale Format**:
   - All enhancement algorithms consume 2D `float32 [0.0, 1.0]` and output 2D `float32 [0.0, 1.0]`.
   - Dimensions `(Height, Width)` are preserved exactly across all methods.
3. **Display Colormap Decoupling**:
   - False-color palettes (ARIS Amber, Thermal, Inferno) are presentation-layer transformations applied strictly for human eye visualization.
   - Pseudocolor RGB images are programmatically prohibited from entering the YOLO detector or quantitative metric routines.
4. **Production Model Immutability**:
   - Checkpoint `models/detection/sonar_yolov8_fls_trained.pt` has verified SHA256:
     `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`.
   - The enhancement system operates without altering or fine-tuning this checkpoint.
5. **Detector Attribution Hierarchy**:
   - YOLOv8n-FLS is the primary candidate generator and bounding box detector.
   - MobileNetV3 is strictly a secondary verification model operating on cropped candidate ROIs for consensus confirmation.
6. **Zero Metric Fabrication**:
   - Quality metrics (ENL, CNR, EPI) return `NOT MEASURABLE` with explicit scientific reasons if region requirements (homogeneous background, ground truth target erosion) fail.

---

## 3. Backend Subsystem Architecture

### Provider Hierarchy (`backend/enhancement/providers/`)
- `EnhancementProvider` (Abstract Base Class): Defines `improve()`, `supports()`, `validation_status`, and telemetry.
- `ClassicalEnhancementProvider`: Wraps 8 classical algorithms with high-resolution CPU timing (`VALIDATED`).
- `LearnedEnhancementProvider`: Manages deep-learning checkpoints (WFC-BSN, SEGSID). Truthfully reports `UNAVAILABLE` when weights are absent and invokes automatic fallback.
- `EnhancementManager`: Singleton orchestrator managing method dispatch, telemetry, and SHA256-keyed bounded cache (LRU, max 128 entries).

### Classical Enhancement Pipeline (`backend/enhancement/methods.py`)
1. `identity`: Baseline raw control.
2. `percentile_normalize`: P2-P98 acoustic outlier suppression.
3. `gamma_correct`: Power-law radiometric compression ($\gamma = 0.7$).
4. `clahe_enhance`: Adaptive localized contrast equalization (clip limit = 2.0).
5. `median_clahe`: Impulsive speckle suppression before CLAHE.
6. `bilateral_clahe`: Edge-preserving bilateral filtering before CLAHE (`BALANCED`).
7. `unsharp_clahe`: High-boost Laplacian boundary sharpening before CLAHE.
8. `log_bilateral_clahe`: Multiplicative speckle filtering in homomorphic log domain.

---

## 4. Frontend Component Hierarchy

```
frontend/src/
├── components/sonar/
│   ├── SonarImageModeToggle.tsx       # Reusable [RAW] [IMPROVED] [SPLIT] pill selector
│   ├── ScientificDisclosurePanel.tsx  # Expandable disclosure of parameters, latency & metrics
│   ├── SonarImageViewer.tsx           # Reusable interactive viewer with split slider & pan/zoom
│   ├── DetectionOverlay.tsx           # Bounding box overlay with YOLO + MobileNetV3 attribution
│   └── SonarViewer.tsx                # Main workstation canvas with split support
└── pages/
    ├── SonarEnhancementPage.tsx       # Dedicated research laboratory (/enhancement)
    ├── SonarReplayLab.tsx             # Temporal playback with integrated enhancement
    ├── AcousticEvidencePage.tsx       # Forensic evidence with split slider & tri-pane
    ├── FailureExplorerPage.tsx        # FP/FN error case investigation with live enhancement
    └── TargetRegistryPage.tsx         # Target registry with acoustic crop visualization
```

---

## 5. Security & Caching Protocols

- **Path Traversal Sanitization**: All file parameters are stripped to basenames via `Path(name).name`.
- **Bounded In-Memory Caching**: Cache keys are derived from SHA256 of raw float32 pixels, method string, and parameter dictionary.
- **Payload Safety**: Base64 image inputs are bounded to 15MB max payload size with grayscale decoding enforcement.
