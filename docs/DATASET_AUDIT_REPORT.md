# Comprehensive Dataset Audit Report

**Audit Date**: 2026-09-19T13:24:07.254235+00:00  
**Overall Status**: **PASS**  
**Auditor**: `AnnotationAuditor` (MarineDebris-Sonar-AI Core ML Engine)

---

## 1. Executive Summary

This audit evaluates the integrity, geometric correctness, scale distributions, and cross-split sequence leakage for both the frozen legacy benchmark dataset (`sonar_debris_v2_clean`) and the production research dataset (`sonar_debris_v3`).

All samples have been verified against forward-looking sonar (FLS) acoustic constraints, normalized coordinate bounds $[0.0, 1.0]$, and cryptographic SHA-256 deduplication.

| Metric | V2 Legacy Clean (`sonar_debris_v2_clean`) | V3 Production (`sonar_debris_v3`) | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Total Images** | 238 | 660 | Verified Genuine |
| **Total Bounding Boxes** | 371 | 899 | Verified Genuine |
| **Empty / Negative Frames** | 0 | 84 | Accounted |
| **Annotation Errors** | 0 | 0 | **ZERO ANOMALIES** |
| **Exact Cross-Split Leakage** | 0 | 0 | **ZERO LEAKAGE** |
| **Sequence-Level Leakage** | 0 | 0 | **ZERO LEAKAGE** |
| **Audit Status** | **PASS** | **PASS** | **PASSED** |

---

## 2. Dataset Split Accounting

### 2.1 V3 Production Dataset Splits (`sonar_debris_v3`)
- **Train Split**: 480 images (636 boxes, 75 negatives)
- **Validation Split**: 100 images (136 boxes, 6 negatives)
- **Held-Out Test Split**: 80 images (127 boxes, 3 negatives)

### 2.2 V2 Legacy Dataset Splits (`sonar_debris_v2_clean`)
- **Train Split**: 166 images (266 boxes)
- **Validation Split**: 35 images (51 boxes)
- **Held-Out Test Split**: 37 images (54 boxes)

---

## 3. Class Distribution & Scale Categorization

### 3.1 V3 Class Distribution
- **Class 0 (derelict_fishing_gear)**: 0 boxes (0.0%)
- **Class 1 (general_marine_debris)**: 619 boxes (68.9%)
- **Class 2 (shipwreck)**: 0 boxes (0.0%)
- **Class 3 (pipe_or_cylinder)**: 0 boxes (0.0%)
- **Class 4 (other_man_made_target)**: 280 boxes (31.1%)

### 3.2 V3 Target Scale Distribution
- **Tiny (< 32 px)**: 2 targets
- **Small (32 - 64 px)**: 160 targets
- **Medium (64 - 128 px)**: 609 targets
- **Large (> 128 px)**: 128 targets

---

## 4. Leakage & Sequence Boundary Verification

To ensure evaluation integrity, temporal sonar sequences must not cross split boundaries:
- **Exact Hash Duplicate Check**: Passed with 0 cross-split duplicates.
- **Continuous Ping Sequence Separation**: Group-aware sequence parsing confirmed that no ping acquisition sequence crosses between train, validation, and test partitions.
- **Test Partition Protection**: The 80 test images in V3 and 37 test images in V2 remain strictly quarantined from all training processes.

---

## 5. Certification & Compliance
This dataset audit confirms that `datasets/sonar_debris_v3` and `datasets/sonar_debris_v2_clean` comply with the non-negotiable research safeguards of `MarineDebris-Sonar-AI`.
