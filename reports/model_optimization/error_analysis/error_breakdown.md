# MarineDebris-Sonar-AI — Categorical Error Analysis & Failure Breakdown

**Evaluation Date:** 2026-09-04  
**Evaluated Models:**
- `sonar_yolov8_fls_trained.pt` (Active Production Control)
- `yolov8_fls_v3_candidate.pt` (Dataset V3 Candidate)

---

## 1. Executive Summary of Failure Modes

Acoustic object detection in Forward-Looking Sonar (FLS) suffers from four distinct failure modes:
1. **Low-SNR / Faint Returns (False Negatives):** Small or acoustically absorbent debris (e.g. decayed fabric, thin synthetic lines) produce minimal acoustic highlights, leading to missed detections at higher confidence thresholds.
2. **Acoustic Boundary False Positives:** Reverberant wall echoes in watertanks and high-intensity surface-reflection multipath reflections are frequently misidentified as rigid man-made debris.
3. **Acoustic Shadow Occlusion / Truncation (Localization Error):** Objects situated at the grazing angle threshold have acoustic shadows that merge into the dark background, distorting predicted bounding box coordinates.
4. **Natural Seabed Clutter Confusion:** Sediment ripples, boulders, and rock ridges in quarry benchmarks create false positives under grazing incidence.

---

## 2. Benchmark-by-Benchmark Error Breakdown

### Benchmark 1: Legacy V2 Held-out Control (37 Images, 54 Instances)
- **Production Model (`sonar_yolov8_fls_trained.pt`):**
  - True Positives (TP): 43 / 54 (80% recall)
  - False Negatives (FN): 11
  - False Positives (FP): 2 (on high-gain boundary reverberation)
  - Precision: 95.56% | Recall: 79.33% | mAP50: 77.72%
  - **Dominant Failure:** Faint general marine debris at distance > 3.5 meters where SNR drops below 6 dB.

- **V3 Candidate Model (`yolov8_fls_v3_candidate.pt`):**
  - True Positives (TP): 38 / 54 (70% recall)
  - False Negatives (FN): 16 (Significant regression on faint objects)
  - False Positives (FP): 3
  - Precision: 92.39% | Recall: 70.06% | mAP50: 68.98%
  - **Root Cause of Regression:** Over-penalization from training on 75 negative frames suppressed model confidence for faint legacy targets.

---

### Benchmark 2: Dataset V3 Held-out Generalization (80 Images, 127 Instances)
- **Production Model (`sonar_yolov8_fls_trained.pt`):**
  - True Positives (TP): 110 / 127 (86.6% recall)
  - False Negatives (FN): 17
  - False Positives (FP): 7
  - Precision: 93.95% | Recall: 86.66% | mAP50: 85.88%
  - Strong generalization across new sequences (Sources A and B) without prior exposure.

- **V3 Candidate Model (`yolov8_fls_v3_candidate.pt`):**
  - True Positives (TP): 83 / 127 (65.4% recall)
  - False Negatives (FN): 44
  - False Positives (FP): 4
  - Precision: 95.06% | Recall: 65.56% | mAP50: 65.13%
  - Higher precision (+1.1%), but dramatic drop in recall (-21.1%) due to excessive conservative thresholding learned during unweighted negative training.

---

### Benchmark 3: Hard Negatives Clutter Suite (84 Genuine Negative Images)
- **Production Model (`sonar_yolov8_fls_trained.pt`):**
  - Images with False Alarms: 18 / 84
  - False Alarm Rate (FAR): 21.43%
  - Total False Positives: 18 (1 on flooded quarry seabed, 17 on acoustic wall reverberation)
  - **Analysis:** Demonstrates near-zero false alarms on natural seabed clutter (1.6% quarry error rate), but vulnerability to high-intensity acoustic tank wall multipath.

- **V3 Candidate Model (`yolov8_fls_v3_candidate.pt`):**
  - Images with False Alarms: 12 / 84
  - False Alarm Rate (FAR): 14.29% (-7.14% improvement)
  - Total False Positives: 13 (1 quarry, 12 wall)
  - Successfully suppressed wall reverberations, but at the cost of target recall.

---

### Benchmark 4: Cross-Domain & Auxiliary Suite (82 Images, 136 Instances)
- **Production Model (`sonar_yolov8_fls_trained.pt`):**
  - Precision: 37.6% | Recall: 33.9% | mAP50: 33.80% | mAP50-95: 24.0%
- **V3 Candidate Model (`yolov8_fls_v3_candidate.pt`):**
  - Precision: 38.0% | Recall: 25.6% | mAP50: 25.50% | mAP50-95: 16.6%
- **Cross-Domain Insight:** Both models show expected drop on cross-modality (SSS side-scan and auxiliary acoustic sensors) due to fundamental differences in grazing angle and fan-beam projection geometry.

---

## 3. Categorical Defect Table

| Defect ID | Description | Severity | Frequency | Recommended Mitigation |
| :---: | :--- | :---: | :---: | :--- |
| **DEF-01** | Small object miss (<32 px) in far range | HIGH | 14.2% of FNs | P2 small object feature head; train at 768px resolution |
| **DEF-02** | Acoustic wall reverberation false alarm | MEDIUM | 88.9% of FPs | Polar coordinate masking; multipath wall rejection filter |
| **DEF-03** | Low contrast acoustic shadow misalignment | LOW | 6.8% of boxes | CIoU loss weight tuning ($\beta_{box} = 7.5$); shadow augmentation |
| **DEF-04** | Over-suppression by background negatives | HIGH | 21.1% recall loss | Domain-balanced sampling (max 10% hard negatives in training) |
