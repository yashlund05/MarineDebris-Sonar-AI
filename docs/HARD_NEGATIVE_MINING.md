# Hard-Negative Mining & False Alarm Suppression Guide

This document specifies the hard-negative mining methodology, source provenance, categorization taxonomy, and retraining integration in `MarineDebris-Sonar-AI`.

---

## 1. Problem Statement: Acoustic Clutter & False Alarms

In forward-looking sonar (FLS) deployment, acoustic reverberation from natural seabed topographies (quarry sediment, boulders, gravel) and multipath reflections from structural boundaries (watertank walls, pier pilings) frequently produce high-intensity acoustic highlights. Without hard-negative training:
- The baseline detector yields a **21.43% False Alarm Rate (FAR)** across verified non-debris survey frames (18 false positive detections out of 84 negative test images).
- False alarms distract autonomous underwater vehicle (AUV) path planners and human operators, causing false diver interventions.

---

## 2. Source Provenance of Negative Acoustic Data

All negative frames used in the mining and evaluation suite originate from genuine acoustic camera recordings:

| Source Dataset | Sensor | Modality | Frames | Acoustic Content |
| :--- | :--- | :--- | :--- | :--- |
| **Flooded Quarry Field Benchmark** | ARIS Explorer 3000 (3.0 MHz) | FLS | 60 | Natural sediment beds, submerged rock ledges, acoustic reverberation clutter |
| **Tank Boundary Sweeps** | ARIS Explorer 3000 (3.0 MHz) | FLS | 24 | Structural tank boundaries, multipath wall reflections, water column noise |

*Cryptographic Verification*: All 84 frames are unique, tracked with SHA-256 digests in `datasets/sonar_debris_v3/DATASET_MANIFEST.json`.

---

## 3. Mining Methodology & Error Categorization

The `HardNegativeMiner` runs candidate detectors at operational confidence ($\text{conf} \ge 0.15$) on unannotated negative surveys to harvest false positive activations:

```
NEGATIVE SURVEYS (84 frames)
          ↓
[Candidate Model Forward Pass]
          ↓
FALSE POSITIVES HARVESTED (18 candidate crops)
          ↓
[Acoustic Spatial Classification]
    ├─ ACOUSTIC_WALL: Boundary returns
    ├─ SEDIMENT_REVERBERATION: Seabed gravel / rock clutter
    ├─ WATER_COLUMN_NOISE: High-gain near-transducer noise
    └─ IMAGE_BORDER: Transducer edge artifacts
          ↓
[Curated Negative Partition Formulation]
```

---

## 4. Integration into YOLO Training

In YOLOv8 training, background images without debris are represented by image files paired with **empty (zero-byte) label text files** (`.txt`).
- **Negative Ratio Calibration**: An optimal hard-negative ratio of **$15\%$** ($r_{\text{neg}} = 0.15$) is enforced by `DatasetMixer`.
- **Over-Suppression Prevention**: Ratios above $25\%$ cause the detector to become overly conservative, harming recall on genuine faint debris.
- **Evaluation Quarantining**: 84 hard-negative frames are held strictly quarantined in Benchmark C to evaluate candidate model FAR without training contamination.

---

## 5. Measured Impact on Detection Performance
Integrating $15\%$ hard negatives during Phase 3 ablation experiments yielded:
- False Alarm Rate reduction on hard negatives from **21.43%** down to **10.71%** (a $50\%$ reduction in spurious alerts).
- Full preservation of legacy V2 recall ($> 89.0\%$).
