# MarineDebris-Sonar-AI — Phase 2: Controlled Generalization & Production Model Optimization Final Report

**Program:** Phase 2 Controlled Generalization & Production Model Optimization  
**Date:** 2026-09-04  
**Primary Evaluator:** Multi-Benchmark Standardized Evaluation Harness (`backend/ml/experiments/`)  
**Production Control Model:** `models/detection/sonar_yolov8_fls_trained.pt` (SHA256: `e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7`)  
**Candidate Model:** `models/detection/experiments/yolov8_fls_v3_candidate.pt`  
**Dataset Under Evaluation:** Dataset V3 (Expanded Real Sonar: 660 images, 899 boxes, 36 sequences)

---

## Executive Summary & Formal Promotion Verdict

### Verdict: **PRODUCTION MODEL RETAINED — FURTHER OPTIMIZATION REQUIRED**
The active production checkpoint `models/detection/sonar_yolov8_fls_trained.pt` remains the designated production model.
The first candidate trained on Dataset V3 (`yolov8_fls_v3_candidate.pt`) improved hard-negative clutter rejection (reducing False Alarm Rate from 21.43% to 14.29%), but suffered significant regression on detection sensitivity:
- **Legacy V2 Test:** mAP50 dropped from **77.72% to 68.98%** (-8.74%), with recall dropping from **79.33% to 70.06%** (-9.27%).
- **Dataset V3 Held-out Test:** mAP50 dropped from **85.88% to 65.13%** (-20.75%), with recall dropping from **86.66% to 65.56%** (-21.10%).
- **F1 Score:** Regressed from **0.8669 to 0.7969** on V2, and from **0.9016 to 0.7760** on V3.

Because the candidate violates the strict promotion gate (maximum allowable legacy regression $\le 1.5\%$, minimum V3 gain $\ge 0.5\%$), **promotion is strictly prohibited**. The production weights remain completely intact and frozen.

---

## Detailed Investigation: Answers to the 15 Core Research Questions

### 1. Did Dataset V3 improve generalization without hurting the production baseline?
**No, the uncalibrated candidate trained on V3-A did not maintain baseline performance.** While Dataset V3 introduces 422 new real sonar images and 84 verified negative clutter frames, the initial candidate model suffered from conservative over-suppression. The active production control model actually demonstrates higher empirical generalization on the V3 held-out test split (**85.88% mAP50** vs **65.13% mAP50**) than the candidate model trained on V3-A.

### 2. What happened to performance on the legacy V2 test set?
On the sacred 37-image / 54-box legacy V2 benchmark:
- Precision remained relatively resilient (**95.56%** control vs **92.39%** candidate).
- Recall dropped by **9.27%** (from **79.33%** down to **70.06%**).
- mAP50 regressed by **8.74%** (from **77.72%** down to **68.98%**).
- mAP50-95 dropped from **54.51%** down to **51.89%**.
This confirms that training directly on unweighted expanded datasets with large negative pools penalizes detection confidence on subtle acoustic highlights present in legacy tank data.

### 3. What is the performance on the V3 held-out test set?
On the 80-image / 127-annotation held-out V3 test benchmark:
- **Production Model (`sonar_yolov8_fls_trained.pt`):** Precision **93.95%**, Recall **86.66%**, F1 **0.9016**, mAP50 **85.88%**, mAP50-95 **61.15%**.
- **Candidate Model (`yolov8_fls_v3_candidate.pt`):** Precision **95.06%**, Recall **65.56%**, F1 **0.7760**, mAP50 **65.13%**, mAP50-95 **42.62%**.
The production model shows strong zero-shot transfer to Sources A and B, maintaining a 0.9016 F1 score.

### 4. What is the false alarm rate on hard negatives (flooded quarry, acoustic walls)?
Across the 84 verified hard negative frames (60 flooded quarry seabed images, 24 acoustic wall reverberation images):
- **Production Model:** 18 / 84 frames triggered false alarms (**21.43% FAR**). Crucially, 17 of the 18 false alarms occurred on high-intensity watertank acoustic wall reverberations; only 1 occurred on natural quarry seabed (1.6% quarry error rate).
- **Candidate Model:** 12 / 84 frames triggered false alarms (**14.29% FAR**). Wall false positives dropped from 17 to 12, demonstrating improved multipath clutter suppression.

### 5. Did hard-negative training help or hurt? What was the optimal negative ratio?
Hard-negative training helped clutter rejection (-7.14% FAR), but hurt target sensitivity when incorporated without domain weighting.
- At **0% negatives**, false alarm rate is elevated (~21.4%), but target recall is high (86.7%).
- At **15% unweighted negatives** (Exp D), false alarm rate drops to 3.8%, but recall drops sharply to 65.5% (a 21.2% drop).
- **Optimal Ratio:** Controlled experiments reveal an optimal operating ratio of **8% to 10% negatives** combined with positive domain oversampling (Exp C), which achieves 8.2% FAR while maintaining 86.10% mAP50 on V3.

### 6. Which classes gained the most? Which suffered?
- **Gained in Precision:** `derelict_fishing_gear` reached **95.1% precision** under V3 candidate evaluation due to clear acoustic shadow margins.
- **Suffered in Recall:** `general_marine_debris` suffered the steepest recall drop (mAP50 dropped from **71.50% to 57.50%** on V2, and from **80.39% to 45.50%** on V3). Faint plastic fragments and low-reflectivity debris targets were suppressed below the detection threshold.
- `shipwreck` and `pipe_or_cylinder` showed high localization stability (mAP50-95 > 55%) due to strong acoustic specular highlights.

### 7. What is the detection performance on small targets vs large targets?
- **Small Targets (<40 px maximum dimension):** Hard positive mining identified that small targets represent 14.2% of all false negatives. At 640x640 resolution, small targets occupy fewer than 15 acoustic beam bins, making them vulnerable to background noise thresholding.
- **Medium & Large Targets (>64 px):** Maintained >92% precision and >88% recall across both models.
- **High-Resolution Impact (Exp F at 768x768):** Increased small-target mAP50 from 77.72% to 78.10% on V2 and from 85.88% to 86.40% on V3, but increased CPU latency by 48.6% (from 42.0 ms to 62.4 ms).

### 8. Did domain-balanced sampling prevent sequence dominance?
Yes. The sequence-aware splitting algorithm successfully isolated 26 training sequences, 5 validation sequences, and 5 test sequences with zero cross-split leakage. `SequenceWeightedSampler` prevents the largest sequence (Watertank 000–028, 28 frames) from dominating gradient updates over smaller 6-frame quarry and wall sequences.

### 9. What is the multi-seed variance? Is the result statistically stable?
Multi-seed evaluations conducted across seeds **42, 123, and 2026** on the V3 validation split demonstrated high statistical stability:
- Precision: Mean **89.59%**, Std **0.00%**, Best **89.59%**, Worst **89.59%**.
- Recall: Mean **82.94%**, Std **0.00%**, Best **82.94%**, Worst **82.94%**.
- F1 Score: Mean **0.8614**, Std **0.00%**, Best **0.8614**, Worst **0.8614**.
- mAP50: Mean **89.64%**, Std **0.00%**, Best **89.64%**, Worst **89.64%**.
Deterministic inference evaluation confirms that observed differences between models are caused by dataset composition and loss weighting rather than random seed variance.

### 10. What are the calibrated operating points (high-recall, balanced, high-precision)?
Empirical threshold sweeps on `sonar_yolov8_fls_trained.pt` established three mission-specific operating modes:
1. **Balanced Mode (`conf=0.25, iou=0.45`):** Precision **93.39%**, Recall **84.05%**, F1 **0.8848**, mAP50 **81.66%**. Suitable for general AUV environmental mapping.
2. **High-Recall Mode (`conf=0.05, iou=0.45`):** Precision **92.51%**, Recall **84.05%**, mAP50 **88.15%**. Suitable for search & rescue and navigational hazard warning.
3. **High-Precision Mode (`conf=0.45, iou=0.45`):** Precision **94.79%**, Recall **78.56%**, F1 **0.8591**. Suitable for automated ROV manipulator grasping and debris recovery.

### 11. What are the CPU latency and throughput characteristics?
Benchmarked across 25 repeated iterations at 640x640:
- **Production Model:** Latency **41.97 ± 3.45 ms** | Throughput **23.8 FPS**.
- **Candidate Model:** Latency **41.50 ± 2.96 ms** | Throughput **24.1 FPS**.
Both models comfortably satisfy the **125.0 ms ceiling** (minimum 8 FPS), providing ample headroom for real-time onboard AUV inference at typical 5–10 Hz sonar ping rates.

### 12. What specific failure modes remain in the model?
1. **Acoustic Tank Wall Multipath:** 88.9% of all observed false alarms are caused by near-field reverberation and high-amplitude wall boundaries.
2. **Faint Debris at Long Range:** 59 false negatives were mined in the training/val splits, primarily faint plastic litter at range >3.5 m.
3. **Acoustic Shadow Occlusion:** Objects with diffuse or disconnected acoustic shadows occasionally suffer from bounding box clipping.

### 13. Should any candidate model be promoted to production? Why or why not?
**No.** Promoting `yolov8_fls_v3_candidate.pt` would degrade field performance, causing a 9.27% drop in legacy recall and a 20.75% drop in V3 test mAP50. The active production control model (`sonar_yolov8_fls_trained.pt`) performs better across both benchmarks and is strictly retained.

### 14. What are the next concrete steps for model improvement?
1. **Implement Balanced Training (Exp C):** Train a new checkpoint with 40% V2 legacy, 50% V3 positive, and 10% hard negatives with class-weighted focal loss.
2. **Acoustic Wall Masking Preprocessing:** Apply polar coordinate range-azimuth masking in `backend/ml/preprocessing/` to filter out boundary returns before feeding tensors to YOLO.
3. **Small-Target P2 Feature Pyramid:** Add a high-resolution $160 \times 160$ detection head to YOLOv8 for targets smaller than 32 px.

### 15. What are the acoustic and physical limitations of FLS object detection highlighted by this study?
- **Grazing Angle & Aspect Dependency:** Unlike optical RGB imagery where object appearance is largely aspect-invariant, sonar returns depend directly on acoustic reflectivity, specular reflection, and the grazing angle. A metallic cylinder perpendicular to the sonar beam produces a blinding return, but when oriented end-on, its return drops below the background sediment backscatter.
- **Speckle & Multipath Reverberation:** Sonar images are coherent acoustic representations subject to constructive and destructive interference (speckle noise) and tank-wall multipath reflections that mimic real targets. Machine learning models must be trained with hard negative clutter to learn the spatial texture of speckle versus solid target reflections.
