# MarineDebris-Sonar-AI — Error Analysis Report

**Model Evaluated:** `ml/experiments/exp01_sonar_aug_adamw_640/train_run/weights/best.pt`  
**Split:** `val` | **Confidence Threshold:** `0.3` | **IoU Matching:** `0.45`

## 1. Quantitative Error Breakdown

- **Total Ground-Truth Instances:** 51
- **Total Model Predictions:** 46
- **True Positives (TP):** 43
- **False Positives (FP):** 1
- **False Negatives (FN):** 7
- **Localization & Classification Mismatches:** 2

## 2. False Negative Root Cause Analysis

- **Tiny / Distant Objects (< 32px):** 0 missed targets
- **Low-Contrast / Diffuse Debris:** 7 missed targets

## 3. False Positive Root Cause Analysis

- **Acoustic Clutter / Seabed Shadows:** 1 instances

## 4. Key Recommendations

1. Incorporate acoustic shadow context filtering to suppress false positive clutter on high-intensity reverberation regions.
2. Apply temperature confidence calibration ($T = 1.35$) to ensure consistent probability scaling across detection bounds.
3. Retain multi-scale acoustic gain augmentation to boost detection of low-contrast seabed targets.
