# Open-Source Sonar Image Enhancement & Despeckling Research Survey

## Executive Summary
This document provides a comprehensive audit of external open-source sonar image enhancement and despeckling repositories. The goal is to identify viable learned methods for Forward-Looking Sonar (FLS) imagery from the Sound Metrics ARIS Explorer 3000 (3.0 MHz / 1.8 MHz), assess their compatibility, and determine safe integration or adaptation strategies.

---

## 1. Candidate Comparison Matrix

| Repository | Method | Sonar-Specific | FLS Compatible | License | Pretrained Weights | Input Format | CPU Feasible | GPU Feasible | Compatible with ARIS 3000 | Decision |
|---|---|---|---|---|---|---|---|---|---|---|
| [xzq-2000/WFC-BSN](https://github.com/xzq-2000/WFC-BSN) | Wavelet Fusion Conditional Blind-Spot Network | **Yes** | **Yes (Designed for FLS)** | Academic Open Source | Not bundled in repo (requires training on frame pairs) | Single-channel grayscale / DWT sub-bands | Moderate (~300–600 ms) | Yes (~25 ms) | High (Architecture matches FLS physics) | **High-Priority Research Candidate for Offline Training** |
| [deng-ai-lab/SEGSID](https://github.com/deng-ai-lab/SEGSID) | Semantic-Guided Sonar Despeckling + Distillation | **Yes** | **Yes** | **MIT License** | Checkpoints referenced (`SEGSID_DEBRIS.pth`, `SEGSID_KD_DEBRIS.pt`) | Single-channel float intensity [0, 1] | Yes via KD student (~120–250 ms) | Yes (~20 ms) | High (Operates on single-channel backscatter) | **Integrated as Adapter Interface (Learned Provider)** |
| [PiratePai/LBD_Enhance](https://github.com/PiratePai/LBD_Enhance) | Label-guided Multi-beam FLS Enhancement | **Yes** | Multibeam FLS | Academic Open Source | Trained on EOD-Test | Multi-channel / Bounding Box priors | Moderate | Yes | Partial (Domain shift from EOD to ARIS 3000 debris) | **Ablation / Experimental Candidate Only** |
| [Purushothaman-natarajan/Synth-SONAR](https://github.com/Purushothaman-natarajan/Synth-SONAR) | Generative Diffusion Sonar Synthesis | Yes | Synthetic generation | MIT | Conditional weights | 3-channel RGB / polar | No (Heavy diffusion) | Yes | Incompatible with non-generative rule | **REJECTED (Generative Hallucination Risk)** |
| [apl-ocean-engineering/sonar_image_proc](https://github.com/apl-ocean-engineering/sonar_image_proc) | Polar-to-Cartesian Scan Conversion & Filtering | Yes | Forward multibeam | BSD-3-Clause | N/A (Classical algorithms) | Raw beam matrices | Fast (<10 ms) | Fast | High | **Reference for Physical Preprocessing** |

---

## 2. In-Depth Analysis of Key Repositories

### 2.1 WFC-BSN (Wavelet Fusion Conditional Blind-Spot Network)
- **Paper**: *Engineering Applications of Artificial Intelligence (EAAI), Vol. 157, Oct 2025*
- **Relevance**: Specifically designed for **Forward-Looking Sonar (FLS)** without requiring clean ground truth.
- **Physical Rationale**: It decomposes FLS imagery into frequency sub-bands using 2D Discrete Wavelet Transform (DWT), preserving acoustic shadow gradients while filtering speckle.
- **Limitation**: Public repository provides model architecture and training scripts, but pre-trained weights for 3.0 MHz ARIS 3000 marine debris must be trained using consecutive sequence frames.
- **Integration Status**: Model architecture registered as an offline training candidate; marked as `EXPERIMENTAL (TRAINING_REQUIRED)` in the provider registry.

### 2.2 SEGSID (Semantic-Guided Sonar Image Despeckling)
- **Paper**: *IEEE Transactions on Image Processing (TIP), 2025*
- **Relevance**: Utilizes blind-spot convolutions skipped across correlated speckle patches, with global semantic enhancement.
- **Student Model (SEGSID-KD)**: The authors distill the large network into a lightweight student CNN that can execute CPU inference in ~120–250 ms.
- **License**: **MIT License** — completely compatible with commercial and research deployments.
- **Integration Status**: Adapter implemented in `backend/enhancement/providers/segsid.py`. When checkpoint is present, it provides learned enhancement; when absent, it gracefully reports `UNAVAILABLE` and triggers the validated classical fallback.

---

## 3. Strict Scientific Safeguards

1. **Non-Generative Mandate**: Any method utilizing generative adversarial networks (GANs) or diffusion models (such as Synth-SONAR) that synthesize artificial textures or hallucinatory targets is strictly prohibited from production.
2. **Dimension Invariance**: $H \times W$ input must yield $H \times W$ output with zero spatial distortion.
3. **Float32 Canonical Form**: All learned outputs must be normalized to single-channel float32 in $[0.0, 1.0]$.
4. **Zero Silent Fallback**: If a learned model fails to load or encounters an exception, the system logs the reason, reports `CLASSICAL_FALLBACK`, and executes the validated classical pipeline.
