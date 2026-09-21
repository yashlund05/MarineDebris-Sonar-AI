# Synthetic Sonar Data Policy & Quality Screening Specification

This document establishes the mandatory governance, screening protocols, and architectural safeguards regarding the generation, validation, and usage of synthetic acoustic sonar data within `MarineDebris-Sonar-AI`.

---

## 1. Principles of Synthetic Data Governance

1. **Secondary Priority to Real Data**:
   Synthetic data must never replace genuine real-world sonar acquisition. It is strictly an experimental mechanism to address measured data shortages (e.g., extremely rare debris classes, deep-shadow targets under specific grazing angles).
2. **Never Contaminate Evaluation Sets**:
   Synthetic data is strictly prohibited from entering validation and held-out test splits (`datasets/sonar_debris_v2_clean`, `datasets/sonar_debris_v3/images/test`). Evaluation is real-only.
3. **Never Blindly Mix with Real Training Sets**:
   Every dataset variant containing synthetic images must be isolated under a distinct version tag (e.g., `v3_c`, `detection_real_plus_synthetic_v1`) with full accounting in `DATASET_MANIFEST.json`.
4. **Zero Untested Assumptions**:
   Literature claims regarding diffusion or GAN augmentation in optical vision do not translate directly to underwater acoustics. Every synthetic candidate must pass automated physical screening.

---

## 2. Automated Quality Screening Gates

The `SyntheticQualityScreener` enforces multi-point acoustic physics and label validation before admitting any synthetic candidate:

| Quality Gate | Check | Threshold / Requirement | Failure Action |
| :--- | :--- | :--- | :--- |
| **Q1. Geometric Readability** | File format, dimensions, uncorrupted byte stream | Exactly $640 \times 640$ 2D scalar array | `REJECTED` |
| **Q2. Numerical Integrity** | NaN, Inf, and flat array checks | $\text{std}(I) \ge 3.0$, zero NaN/Inf | `REJECTED` |
| **Q3. Bounding-Box Validity** | Normalized coordinates in $[0.0, 1.0]$, $w > 0, h > 0$ | Standard 5-token YOLO format | `REJECTED` |
| **Q4. Target Contrast Ratio** | $\mu_{\text{target}} / \mu_{\text{background}}$ | $\ge 1.15$ | `REJECTED` |
| **Q5. Acoustic Shadow Verification** | Downstream range intensity depression behind highlight | $\mu_{\text{target}} / \mu_{\text{shadow}} \ge 1.20$ | `EXPERIMENTAL_ONLY` / `REJECTED` |

---

## 3. Status Classifications

- **`ACCEPTED`**: Conforms to all geometric, acoustic contrast, and shadow depth criteria. Eligible for controlled ablation experiments.
- **`EXPERIMENTAL_ONLY`**: Exhibits partial acoustic fidelity (e.g., plausible target return but weak shadow). Restricted to exploratory research runs.
- **`NEEDS_REVIEW`**: Requires human sonar operator inspection.
- **`REJECTED`**: Violates one or more quality gates. Immediately purged from training manifests.
