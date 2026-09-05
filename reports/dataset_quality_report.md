# MarineDebris-Sonar-AI — Dataset Forensics & Quality Audit Report

**Dataset Location:** `datasets\sonar_debris`  
**Total Images:** 238  
**Total Ground-Truth Annotations:** 371  

## 1. Split Partitioning & Instance Counts

| Split | Images | Annotations | Avg Boxes/Img | Median Boxes/Img | Min/Max Boxes |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **train** | 166 | 266 | 1.6 | 1.0 | 1 / 4 |
| **val** | 35 | 51 | 1.46 | 1.0 | 1 / 4 |
| **test** | 37 | 54 | 1.46 | 1.0 | 1 / 3 |

## 2. Class Distribution

| Class Name | Annotations | Percentage of Dataset |
| :--- | :---: | :---: |
| `general_marine_debris` | 267 | 72.0% |
| `other_man_made_target` | 104 | 28.0% |

## 3. Object Scale Distribution (on 640×640 Canvas)

| Size Category | Definition | Count | Percentage |
| :--- | :--- | :---: | :---: |
| **tiny (< 32x32 px)** | Max dim on 640px canvas | 1 | 0.3% |
| **small (32x32 - 64x64 px)** | Max dim on 640px canvas | 63 | 17.0% |
| **medium (64x64 - 128x128 px)** | Max dim on 640px canvas | 257 | 69.3% |
| **large (> 128x128 px)** | Max dim on 640px canvas | 50 | 13.5% |

## 4. Geometric Summary Statistics

- **Bounding Box Width:** Mean = 76.0 px (Norm: 0.1188), Range: [21.3 px, 298.7 px]
- **Bounding Box Height:** Mean = 83.2 px (Norm: 0.1301), Range: [21.3 px, 297.3 px]
- **Aspect Ratio (W/H):** Mean = 1.03, Median = 0.94, Range: [0.2, 4.44]

## 5. Sequence Leakage & Data Independence Audit

Cross-split sequence block overlap:
- **train_vs_val:** 0 sequence overlaps (0 - Clean)
- **train_vs_test:** 0 sequence overlaps (0 - Clean)
- **val_vs_test:** 0 sequence overlaps (0 - Clean)

**Zero-Leakage Status:** ✅ ZERO LEAKAGE VERIFIED (Strict sequence-block partitioning)

## 6. Label Integrity & Defect Audit

✅ **Zero label syntax, out-of-bounds, or duplicate box errors detected.** All 371 annotations pass strict schema validation.
