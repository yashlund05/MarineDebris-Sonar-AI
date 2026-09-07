# GitHub Research Survey: Sonar Image Enhancement & Despeckling

## Executive Summary
This survey benchmarks open-source academic research repositories and state-of-the-art methods targeting Forward-Looking Sonar (FLS) and high-frequency Acoustic Camera systems (specifically Sound Metrics ARIS Explorer 3000 at 3.0 MHz / 1.8 MHz).

---

## 1. Deep Learning Candidates & Compatibility Audit

### SEGSID (Semantic-Guided Sonar Image Despeckling)
- **Repository**: [deng-ai-lab/SEGSID](https://github.com/deng-ai-lab/SEGSID)
- **Publication**: *IEEE Transactions on Image Processing (TIP), 2025*
- **License**: **MIT License** (fully permissive)
- **Checkpoints**: Pretrained models available, including `SEGSID_DEBRIS.pth` and distilled lightweight student `SEGSID_KD_DEBRIS.pt`.
- **Architecture**:
  - Receptive Field Augmentation (RFA) to defeat spatially correlated acoustic speckle.
  - Global Semantic Enhancement (GSE) to recover debris boundaries.
  - Knowledge Distillation (KD) student model capable of CPU-only execution (~120–250 ms for 512×512 tiles).
- **FLS Compatibility**: Single-channel float intensity maps. Fully compatible with ARIS 3000 backscatter matrices.
- **Priority**: **Highest Priority External Benchmark**.

### WFC-BSN (Wavelet Fusion-Based Conditional Blind-Spot Network)
- **Repository**: [xzq-2000/WFC-BSN](https://github.com/xzq-2000/WFC-BSN)
- **Publication**: *Engineering Applications of Artificial Intelligence (EAAI), Oct 2025*
- **License**: Open academic research
- **Key Innovation**: Specifically designed for **Forward-Looking Sonar (FLS)** without requiring clean ground truth. Decomposes noisy FLS images into multi-frequency sub-bands using 2D DWT. Constructs clean/noisy pairs directly from consecutive temporal real sonar frames.
- **FLS Compatibility**: Direct fit for continuous ARIS 3000 sequence streams.
- **Priority**: **Highest Priority FLS Denoising Research Candidate**.

### LBD-Enhance (Label-guided Multi-beam FLS Image Enhancement)
- **Repository**: [PiratePai/LBD_Enhance](https://github.com/PiratePai/LBD_Enhance)
- **Publication**: *Neurocomputing, Sept 2025*
- **License**: Open academic research
- **Note**: Evaluated on EOD-Test for multibeam forward-looking sonar. Task-driven loss focused on bounding box priors.
- **Priority**: **Compatibility & Ablation Candidate** (not a drop-in replacement for ARIS 3000 without domain adaptation).

---

## 2. Classical Baselines & Acoustic Physics

FLS degradation is governed by:
1. **Multiplicative Speckle Noise**: Coherent interference of acoustic backscatter, modeled by Rayleigh or Gamma distributions.
2. **Range-Dependent Transmission Loss**: Acoustic absorption and spherical geometric spreading cause far-field returns to be substantially darker than near-field returns.
3. **Reverberation & Acoustic Multipath**: Surface and boundary bounces that degrade target-to-shadow contrast.

### Evaluated Classical Pipelines
- **Identity**: Unmodified control baseline.
- **Percentile Normalization**: 2nd to 98th percentile dynamic range stretching.
- **Gamma Correction**: Power-law scaling to improve far-field and shadow visibility.
- **CLAHE**: Localized adaptive histogram equalization (production standard).
- **Median + CLAHE**: Salt-and-pepper and impulsive clutter suppression before contrast expansion.
- **Bilateral + CLAHE**: Edge-preserving spatial/radiometric filtering followed by CLAHE.
- **Unsharp + CLAHE**: High-boost edge sharpening followed by CLAHE.
- **Log-Bilateral + CLAHE**: Homomorphic domain conversion of multiplicative speckle into additive noise.

---

## 3. Visualization & Pseudocolor Standards

- **Canonical Grayscale**: The single-channel float32 array is the immutable scientific source of truth for all quantitative analysis, metrics, and machine learning detectors.
- **Display Palettes**:
  - **ARIS Copper/Amber**: Industry standard for Sound Metrics ARIS 3000 / DIDSON sonar. High dynamic range with bright yellow/white target specular highlights and dark amber background.
  - **Monotonic Thermal**: Preserves monotonic luminance ordering to avoid perceptual contour artifacts.
  - **Inferno**: Matplotlib perceptually uniform, colorblind-safe colormap.
- **Negative Finding**: Standard Jet/Rainbow colormaps introduce false intensity contours and artificial boundaries that mislead operators and are strictly prohibited.
