# Final Detection Model Comparison & Trade-Off Matrix

This report compares all evaluated YOLOv8 forward-looking sonar (FLS) detection checkpoints across accuracy, generalization, false-alarm behavior, small-object recall, and embedded edge latency.

---

## 1. Full Model Comparison Matrix

All models evaluated under identical benchmark protocols on real held-out test data:

| Model ID | Architecture | V2 Test mAP50 | V2 Test Recall | V3 Test mAP50 | Hard-Neg FAR | Small Recall (<40px) | CPU P95 Latency | Throughput | Gate Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`sonar_yolov8_fls_trained.pt`** | YOLOv8n | 89.21% | 90.15% | 91.92% | 21.43% | 87.50% (7/8) | 85.57 ms | 12.38 FPS | **ACTIVE_PROD** |
| **`P3_E0_V2_CONTROL`** | YOLOv8n | 84.77% | 68.32% | 90.55% | 17.86% | 87.50% (7/8) | 44.41 ms | 24.40 FPS | `REJECTED` |
| **`P3_E1_V3_REAL`** | YOLOv8n | 93.49% | 84.32% | 94.82% | 4.76% | 75.00% (6/8) | 48.35 ms | 22.08 FPS | `REJECTED` |
| **`P3_E2_NAIVE_MIX`** | **YOLOv8n** | **93.43%** | **90.16%** | **94.60%** | **10.71%** | **100.0% (8/8)** | **49.46 ms** | **23.65 FPS** | **`ELIGIBLE`** |
| **`P3_E3_BALANCED`** | YOLOv8n | 89.63% | 83.43% | 90.93% | 3.57% | 87.50% (7/8) | 45.53 ms | 23.20 FPS | `REJECTED` |
| **`P3_E4_HARD_NEG`** | YOLOv8n | 89.18% | 82.56% | 91.00% | 4.76% | 75.00% (6/8) | 48.11 ms | 23.04 FPS | `REJECTED` |
| **`P3_E5_HARD_POS`** | YOLOv8n | 91.87% | 90.01% | 93.05% | 26.19% | 100.0% (8/8) | 45.61 ms | 22.91 FPS | `REJECTED` |
| **`E6_SEED_42`** | **YOLOv8n** | **99.11%** | **98.99%** | **95.10%** | **14.29%** | **100.0% (8/8)** | **101.50 ms** | **10.55 FPS** | **`ELIGIBLE`** |
| **`E6_SEED_123`** | **YOLOv8n** | **97.07%** | **89.67%** | **95.31%** | **15.48%** | **100.0% (8/8)** | **51.33 ms** | **21.29 FPS** | **`ELIGIBLE`** |
| **`E6_SEED_2026`** | YOLOv8n | 98.27% | 100.0% | 97.42% | 11.90% | 87.50% (7/8) | 195.13 ms | 8.33 FPS | `REJECTED` |
| **`yolov8_fls_v3_candidate`** | YOLOv8n | 87.68% | 77.89% | 85.06% | 14.29% | 75.00% (6/8) | 112.63 ms | 11.92 FPS | `REJECTED` |

---

## 2. Multi-Dimensional Trade-Off Analysis

### 2.1 Accuracy vs. Latency Trade-off
- **`P3_E2_NAIVE_MIX`** delivers the best overall operational efficiency:
  - Latency P95 is **$49.46\text{ ms}$** ($23.65\text{ FPS}$), nearly $2\times$ faster than the baseline ($85.57\text{ ms}$).
  - Delivers $+4.22\%$ mAP gain on legacy V2 test and $+2.68\%$ mAP gain on held-out V3 test.
- **`E6_SEED_42`** delivers peak localization accuracy ($99.11\%$ V2 mAP50, $98.99\%$ recall), but with a higher latency ($101.50\text{ ms}$). Both satisfy the $125.0\text{ ms}$ budget.

### 2.2 False Alarm Rate vs. Target Sensitivity
- Baseline detector flags **$18$ false positive boxes** across 84 negative survey images ($\text{FAR} = 21.43\%$).
- `P3_E2_NAIVE_MIX` cuts false positive boxes in half to **$9$ boxes** ($\text{FAR} = 10.71\%$) while improving small-object sensitivity from $87.5\%$ to $100.0\%$.
- Overly aggressive negative weighting (E4 and E3) cut FAR to $3.5\% - 4.7\%$, but caused catastrophic recall loss on genuine legacy debris (down to $82.5\% - 83.4\%$).

---

## 3. Subgroup & Per-Class Performance

Evaluation on the 127 ground truth targets in the V3 held-out test split:

| Target Category | Subgroup Definition | Baseline Recall | `P3_E2_NAIVE_MIX` Recall | `E6_SEED_42` Recall |
| :--- | :--- | :--- | :--- | :--- |
| **Small Targets** | Dimension $< 40\text{ px}$ (8 targets) | 87.5% (7/8) | **100.0% (8/8)** | **100.0% (8/8)** |
| **Medium Targets** | Dimension $40 - 100\text{ px}$ (89 targets) | 91.0% (81/89) | **96.6% (86/89)** | **95.5% (85/89)** |
| **Large Targets** | Dimension $> 100\text{ px}$ (30 targets) | 83.3% (25/30) | **83.3% (25/30)** | **90.0% (27/30)** |
| **Far-Range Targets**| Acoustic range $> 3.5\text{ m}$ (27 targets) | 81.5% (22/27) | **88.9% (24/27)** | **85.2% (23/27)** |
| **Faint / Low Contrast**| Contrast ratio $< 1.15$ (102 targets) | 88.2% (90/102) | **93.1% (95/102)** | **94.1% (96/102)** |
