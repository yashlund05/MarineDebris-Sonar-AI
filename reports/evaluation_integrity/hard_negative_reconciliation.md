# MarineDebris-Sonar-AI — Hard-Negative False Alarm Rate (FAR) Reconciliation

**Audit Date:** 2026-09-05  
**Evaluated Negative Benchmark:** 84 Verified Acoustic Clutter Frames  
- 60 Natural Flooded Quarry Benthic Images (Sediment, Ripples, Rock Ridges)
- 24 Watertank Boundary Wall Sweeps (Multipath Reverberation)

---

## 1. Mathematical Definitions & Metric Formulations

To eliminate ambiguity between detection-level counts and image-level operational rates, the system defines:

### 1.1 Negative Image False Alarm Rate (`negative_image_FAR`)
$$\text{negative\_image\_FAR} = \frac{\text{Count of verified-negative images containing } \ge 1 \text{ false-positive detection}}{\text{Total verified-negative images evaluated}}$$

### 1.2 False Positives per Image (`fps_per_negative_image`)
$$\text{fps\_per\_negative\_image} = \frac{\text{Total false-positive bounding boxes across all negative images}}{\text{Total verified-negative images evaluated}}$$

---

## 2. Empirical Audit & Reconciliation Table

| Metric | Production Control (`sonar_yolov8_fls_trained.pt`) | Candidate Model (`yolov8_fls_v3_candidate.pt`) | Clarification / Mathematical Derivation |
| :--- | :---: | :---: | :--- |
| **Total Verified Negatives** | 84 | 84 | 60 Quarry Natural Seabed + 24 Wall Clutter |
| **Negative Images with $\ge 1$ FP** | **18** | **12** | Number of distinct images that triggered alerts |
| **Total False-Positive Detections** | **18** | **13** | Total bounding boxes generated |
| **Negative Image FAR (`negative_image_FAR`)** | **21.43%** ($18 / 84$) | **14.29%** ($12 / 84$) | Exactly explains why candidate FAR is $12/84 = 14.29\%$ |
| **FPs per Negative Image** | 0.2143 ($18 / 84$) | 0.1548 ($13 / 84$) | Detection density per negative survey frame |
| **Max FPs in a Single Image** | 1 | 2 | Candidate produced 2 FPs on one wall sweep frame |
| **Quarry Natural Seabed FPs** | 1 (1.67%) | 1 (1.67%) | High resilience on natural benthic sediment |
| **Watertank Wall Reverberation FPs** | 17 (70.83%) | 12 (50.00%) | Wall multipath is primary clutter source |

---

## 3. Explanation of Previous Reporting Discrepancy

- In the previous report, the table stated:
  `Total False Positives: 13 | FAR: 14.29%`
  A reviewer noticed: $13 / 84 = 15.48\% \neq 14.29\%$.
- **Audit Finding:**
  $14.29\%$ is the **image-level false alarm rate** ($12 / 84 = 0.142857...$).
  One of the 12 images contained **2 false-positive bounding boxes**, resulting in **13 total false positive detections**.
- **Resolution:**
  Both metrics are valid but describe different physical phenomena. All future dashboards and manifests now explicitly report `negative_image_FAR` and `total_false_positive_detections` separately.
