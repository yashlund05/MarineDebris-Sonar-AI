# MarineDebris-Sonar-AI — Dataset Candidate Discovery & Compatibility Report

**Date:** 2026-09-04  
**Audit Framework:** 100-Point Scientific Compatibility Scoring  
**Status:** Completed  

---

## 1. Candidate Scoring Methodology

Each dataset candidate was independently evaluated against 7 objective criteria:
1. **Real-World Authenticity (0–20):** Genuine field or physical water tank sonar captures vs simulated or AI-generated data.
2. **Marine Debris Relevance (0–20):** Focus on submerged anthropogenic debris, derelict fishing gear, nets, ropes, bottles, and canisters.
3. **Sonar Modality Compatibility (0–20):** Forward-Looking Sonar (FLS) acoustic backscatter (ARIS / BlueView) vs Side-scan (SSS) or non-acoustic sensors.
4. **Annotation Quality (0–15):** Peer-reviewed bounding box / polygon annotations with verifiable geometry.
5. **Diversity (0–10):** Variation across acoustic aspect angles, object scales, seabed sediments, and environmental clutter.
6. **Licensing & Provenance (0–10):** Permissive scientific/commercial license (CC-BY, Apache, Public Domain) with traceable permanent DOI.
7. **Useful Scale (0–5):** Quantity of unique, non-duplicate acoustic frames.

---

## 2. Summary Ranking & Categorization

| Candidate ID | Name | Modality | Score | Category | Status |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **`md_fls_watertank_full`** | Marine Debris FLS Benchmark (Watertank Full 1,868) | ARIS 3000 FLS (3.0 MHz) | **96 / 100** | **PRIMARY** | **APPROVED** |
| **`md_fls_quarry_field_negatives`** | Flooded Quarry Field Sequences (Fullsize) | ARIS 3000 FLS (3.0 MHz) | **88 / 100** | **SECONDARY** | **APPROVED (Negative/Field)** |
| **`md_fls_turntable_multiaspect`** | Turntable Multi-Aspect Dataset | ARIS 3000 FLS (3.0 MHz) | **86 / 100** | **SECONDARY** | **APPROVED (Multi-Aspect)** |
| **`seabedobjects_ksec_sidescan`** | SeabedObjects Side-Scan Sonar | Klein 3000 SSS | **68 / 100** | **AUXILIARY** | **APPROVED (Cross-Domain)** |
| **`synthetic_fls_surveys`** | Project Synthetic FLS Demonstrator | Ray-traced Simulated FLS | **58 / 100** | **AUXILIARY** | **APPROVED (Synthetic Only)** |
| **`trashcan_optical_debris`** | TrashCan Underwater Debris | Optical RGB Video | **28 / 100** | **REJECTED** | **REJECTED (Modal Incompatibility)** |
| **`unverified_web_sonar_scrapes`** | Unverified Web Sonar Scrapes | Unknown | **13 / 100** | **REJECTED** | **REJECTED (Missing Provenance)** |

---

## 3. Approved Datasets for Dataset V3 Pipeline

### 3.1 Primary Dataset: `md_fls_watertank_full`
- **Source:** Dr. Matias Valdenegro-Toro (University of Groningen / Heriot-Watt University Ocean Systems Lab).
- **Permanent DOI:** `10.5281/zenodo.15101686`
- **Publication:** "Marine Debris Detection and Segmentation with Forward-Looking Sonar", IEEE/OES Autonomous Underwater Vehicles (AUV), 2020.
- **Sensor:** Sound Metrics ARIS Explorer 3000 (3.0 MHz, 128 acoustic beams, $0.08\text{m}$ resolution).
- **Content:** Expands beyond the initial 250 sample images to include the full spectrum of 1,868 peer-reviewed frames with complete XML bounding box annotations.
- **Taxonomy:** 10 marine debris classes (`bottle`, `can`, `chain`, `drink-carton`, `hook`, `propeller`, `shampoo-bottle`, `standing-bottle`, `tire`, `valve`) + tank reflection boundaries.

### 3.2 Secondary Dataset: `md_fls_quarry_field_negatives`
- **Source:** Dr. Matias Valdenegro-Toro (Flooded Quarry Field Benchmark).
- **Sensor:** Sound Metrics ARIS Explorer 3000 (3.0 MHz).
- **Content:** Real-world flooded quarry sequences providing authentic muddy sediment, current turbulence, acoustic reverberation, and natural seabed structures.
- **Role:** Supplies verified genuine negative/background acoustic frames to eliminate seabed clutter false positives.

### 3.3 Secondary Dataset: `md_fls_turntable_multiaspect`
- **Source:** Dr. Matias Valdenegro-Toro (Turntable Cropped Series).
- **Sensor:** Sound Metrics ARIS Explorer 3000 (3.0 MHz).
- **Content:** Full $360^\circ$ yaw aspect angle acoustic observations across 18 target categories (including plastic pipes, metal boxes, bottles, tires, and valves).
- **Role:** Enriches angular diversity for difficult viewing angles.

### 3.4 Auxiliary Dataset: `seabedobjects_ksec_sidescan` & `synthetic_fls_surveys`
- **Role:** Kept strictly separate for cross-domain evaluation (`V3_CROSS_DOMAIN_TEST`) and synthetic benchmarking without corrupting real FLS training weights.

---

## 4. Rejection Notices & Rationale
- **Optical Datasets (`trashcan_optical_debris`):** Strongly rejected because optical light transmission through seawater does not exhibit acoustic specular scattering, acoustic shadows, or sonar speckle noise. Training an acoustic model on optical RGB corrupts backscatter feature extractors.
- **Web-Scraped Imagery:** Strongly rejected under the Anti-Fabrication Directive due to untraceable licensing, missing hydrophone/transducer metadata, and unverifiable calibration.
