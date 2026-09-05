# MarineDebris-Sonar-AI — Model Optimization Comparison Dashboard

| Model | Dataset | Legacy mAP50 | Legacy F1 | V3 mAP50 | V3 F1 | Hard Neg FAR | Cross-Domain mAP | Latency | FPS | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **sonar_yolov8_fls_trained.pt** | V2 Baseline (Watertank FLS) | 77.72% | 0.8669 | 85.88% | 0.9016 | 21.43% | 33.80% | 42.0 ms | 23.8 | **CONTROL** |
| **yolov8_fls_v3_candidate.pt** | Dataset V3-A (Expanded Real FLS) | 68.98% | 0.7969 | 65.13% | 0.7760 | 14.29% | 25.50% | 41.5 ms | 24.1 | **REGRESSION** |
| **exp_c_balanced_v2_v3** | V3 Balanced (40% V2, 50% V3+, 10% Neg) | 77.10% | 0.8620 | 86.10% | 0.8950 | 8.20% | 34.10% | 42.1 ms | 23.8 | **HIGH_FALSE_ALARM** |
| **exp_d_hard_neg_15pct** | V3 Hard-Negative (15% Negatives) | 74.20% | 0.8210 | 83.50% | 0.8540 | 3.80% | 31.20% | 42.0 ms | 23.8 | **REGRESSION** |
| **exp_f_hires_768** | V3 High-Resolution (768x768) | 78.10% | 0.8690 | 86.40% | 0.9020 | 19.80% | 34.50% | 62.4 ms | 16.0 | **HIGH_FALSE_ALARM** |
