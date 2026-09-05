# Dataset Card — Marine Debris Sonar Dataset V3

**Dataset Name:** `sonar_debris_v3`  
**Version:** `v3.0.0`  
**Publication / Freeze Date:** 2026-09-04  
**Permanent Source DOI:** `10.5281/zenodo.15101686`  
**License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)  
**Primary Host:** Heriot-Watt University Ocean Systems Lab / University of Groningen  

---

## 1. Dataset Overview & Intended Use
- **Objective:** Provide a high-integrity, scientifically traceable, leakage-free benchmark for detecting, classifying, and localizing submerged anthropogenic marine debris in Forward-Looking Sonar (FLS) acoustic imagery.
- **Sensor Modality:** High-Frequency Dual-Frequency Forward-Looking Sonar (Sound Metrics ARIS Explorer 3000 at 3.0 MHz Identification Mode / 1.8 MHz Detection Mode).
- **Target Applications:** Autonomous Underwater Vehicle (AUV) obstacle avoidance and debris survey, Remotely Operated Vehicle (ROV) environmental cleanup inspections, and harbor seafloor monitoring.

---

## 2. Dataset Composition & Statistics

| Metric | Dataset V2 Clean (Baseline) | Dataset V3 (Expanded) | Absolute Growth |
| :--- | :---: | :---: | :---: |
| **Total Real Sonar Images** | 238 | **660** | **+422 (+177.3%)** |
| **Total Bounding Box Annotations** | 371 | **899** | **+528 (+142.3%)** |
| **Genuine Negative Background Frames** | 0 | **84** | **+84 (Clutter Suppression)** |
| **Continuous Acoustic Sequences** | 12 | **36** | **+24 (+200.0%)** |
| **Sequence Overlap (Leakage)** | 0 | **0** | **100% Zero Leakage** |
| **Annotation Geometry Errors** | 0 | **0** | **100% Validated** |

### Source-Level Accounting Breakdown
| Source | Real Images | Positive Images | Negative Images | Boxes | Sequences | Modality | Peer-Review Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Original V2 (Watertank 000–249)** | 238 | 238 | 0 | 371 | 12 | FLS | Peer-Reviewed (IEEE AUV 2020) |
| **New verified source A (Watertank 250–424)** | 171 | 171 | 0 | 272 | 9 | FLS | Peer-Reviewed (IEEE AUV 2020) |
| **New verified source B (Watertank 425–599)** | 167 | 167 | 0 | 256 | 9 | FLS | Peer-Reviewed (IEEE AUV 2020) |
| **Quarry negatives (Flooded Quarry Field Benchmark)** | 60 | 0 | 60 | 0 | 6 | FLS | Source-Verified Field Release |
| **Acoustic wall negatives (Tank Boundary Sweeps)** | 24 | 0 | 24 | 0 | — | FLS | Peer-Reviewed (IEEE AUV 2020) |
| **V3 Total** | **660** | **576** | **84** | **899** | **36** | **FLS** | **100% Source-Verified** |

### Deduplication Accounting
- **Exact duplicates removed:** 0 (all 660 frames verified cryptographically unique with distinct SHA256 hashes).
- **Near-duplicates removed:** 0 — genuine temporally adjacent frames were retained when scientifically valid; sequence-aware grouping prevents related frames from being distributed across different evaluation splits.
- **Near-duplicate cross-split contamination:** 0 — no near-duplicate relationships cross train/validation/test boundaries.

### Split Breakdown (Sequence-Aware Group Partitioning)
- **Train Set (70%):** 480 real images, 636 bounding boxes, 75 negative background frames.
- **Validation Set (15%):** 100 real images, 136 bounding boxes, 6 negative background frames.
- **Test Set (15%):** 80 real images, 127 bounding boxes, 3 negative background frames.

---

## 3. Provenance & Scientific Lineage
Every acoustic frame in Dataset V3 is registered in `datasets/sonar_debris_v3/metadata/provenance.jsonl` with cryptographic SHA256 hashes, source URLs, institutional authors, sensor model, operating frequency, and capture session.

### Source Benchmarks:
1. **`md_fls_watertank` (600 images, 899 annotations):**
   - Author: Dr. Matias Valdenegro-Toro (Heriot-Watt University / University of Groningen).
   - Peer-Reviewed Publication: *Marine Debris Detection and Segmentation with Forward-Looking Sonar*, IEEE/OES Autonomous Underwater Vehicles (AUV), 2020.
   - Sensor: ARIS Explorer 3000 (3.0 MHz, 128 beams, $0.08\text{m}$ resolution).
2. **`md_fls_quarry_field_negatives` (60 real field images):**
   - Author: Dr. Matias Valdenegro-Toro (Flooded Quarry Field Benchmark).
   - Capture Environment: Real flooded quarry with muddy seabed sediment, current disturbance, acoustic reverberation, and natural shadows.
   - Role: Genuine negative background clutter without false bounding boxes.

---

## 4. Class Taxonomy & Harmonization

| Canonical Class ID | Canonical Class Name | Source Category Equivalents | Count in V3 |
| :---: | :--- | :--- | :---: |
| `0` | `derelict_fishing_gear` | Net, rope, cable, ghost pot, lobster trap | 0 |
| `1` | `general_marine_debris` | Bottle, can, drink-carton, shampoo-bottle, tire | 619 |
| `2` | `shipwreck` | Vessel hull, sunken wreckage | 0 |
| `3` | `pipe_or_cylinder` | Pipeline, subsea cylinder, drum | 0 |
| `4` | `other_man_made_target` | Propeller, chain, hook, valve | 280 |
| `-1` | `NEGATIVE_BACKGROUND` | Quarry sediment, tank boundary wall, acoustic shadows | 84 images |

---

## 5. Normalization & Physical Acoustic Fidelity
- **Spatial Resolution:** Standardized to $640 \times 640$ pixels using aspect-ratio-preserving letterboxing.
- **Channel Format:** 3-channel replicated grayscale ($G \to G, G, G$).
- **Anti-Distortion Directive:** Synthetic RGB colorization, false colormaps, and arbitrary optical augmentations are strictly forbidden to preserve raw backscatter pressure wave amplitudes.

---

## 6. Dataset Variants
- **V3-A (Real FLS Core):** Real watertank marine debris + authentic quarry negative seabed clutter.
- **V3-B (Real FLS + Secondary):** Core + secondary multi-aspect turntable targets.
- **V3-C (Real + Secondary + Auxiliary):** Core + Secondary + synthetic side-scan test cases (isolated for cross-domain evaluation).

---

## 7. Known Limitations & Biases
- **Class Imbalance:** Active ground-truth targets are concentrated in Class 1 (`general_marine_debris`) and Class 4 (`other_man_made_target`).
- **Sensor Uniformity:** Data originates from Sound Metrics ARIS 3000. Lower frequency sonars (e.g. 720–900 kHz) may experience speckle noise variations.
- **Scale Distribution:** Dominated by small and medium-scale targets ($32\text{px} - 128\text{px}$). Far-range targets ($< 32\text{px}$) require tuned confidence thresholds ($\le 0.25$).

---

## 8. Citation & Attribution
```bibtex
@inproceedings{valdenegrotoro2020marine,
  title={Marine Debris Detection and Segmentation with Forward-Looking Sonar},
  author={Valdenegro-Toro, Matias},
  booktitle={2020 IEEE/OES Autonomous Underwater Vehicles (AUV)},
  pages={1--6},
  year={2020},
  organization={IEEE},
  doi={10.5281/zenodo.15101686}
}
```
