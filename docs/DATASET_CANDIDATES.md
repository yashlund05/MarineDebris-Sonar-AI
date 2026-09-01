# MarineDebris-Sonar-AI: External Sonar Dataset Candidate Evaluation

**Audit Date:** 2026-09-01  
**Lead Auditor:** Senior Sonar Data & Machine Learning Engineer  
**Objective:** Systematic evaluation of publicly available research datasets for acoustic marine debris and underwater man-made target detection.

---

## 1. Candidate Evaluation Matrix

Each candidate is evaluated against the 6 weighted criteria:
- **Sonar Modality (25%):** True acoustic sonar imagery (Sidescan Sonar preferred; Forward-Looking Sonar acceptable as acoustic surrogate).
- **Annotation Quality (25%):** Machine-readable 2D bounding boxes / masks with clear coordinates.
- **Marine Debris Relevance (20%):** Genuine discarded marine debris (plastics, metals, ghost nets, wrecks, subsea pipes).
- **License / Provenance (15%):** Legally permissible research/open-source license (e.g. CC-BY 4.0, MIT) with clear academic/institutional provenance.
- **Dataset Size (10%):** Sufficient image and annotation count ($> 500$ annotations).
- **Metadata Quality (5%):** Sonar frequency, range, geometry, or mission identifiers.

---

### Candidate 1: Marine Debris FLS & Sonar Benchmark (Valdenegro-Toro)
- **Source / DOI:** [Zenodo 10.5281/zenodo.15101686](https://doi.org/10.5281/zenodo.15101686) & [GitHub: mvaldenegro/marine-debris-fls-datasets](https://github.com/mvaldenegro/marine-debris-fls-datasets)
- **Institution:** University of Groningen / Heriot-Watt University Ocean Systems Lab
- **Modality:** High-frequency acoustic imaging sonar (ARIS Explorer 3000, 3.0 MHz / Dual-frequency)
- **Objects / Classes:** Real marine debris objects (bottles, beverage cans, car tires, chains, drink cartons, shampoo bottles, ship propellers, valves, hooks).
- **Annotations:** COCO JSON format + VOC XML bounding boxes + semantic segmentation masks ($1,868$ annotated frames, $> 3,000$ object instances).
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0).
- **Scores:**
  - Sonar Modality: 22 / 25 (Acoustic imaging sonar; FLS turntable/watertank and flooded quarry)
  - Annotation Quality: 25 / 25 (Pixel-accurate bounding boxes + COCO JSON)
  - Marine Debris Relevance: 20 / 20 (Direct semantic match for plastic debris, tires, metal cans)
  - License / Provenance: 15 / 15 (CC-BY 4.0, peer-reviewed in IEEE/Elsevier)
  - Dataset Size: 9 / 10 ($1,868$ images, multiple viewing angles)
  - Metadata Quality: 4 / 5 (Frequency, range, resolution documented)
- **Total Score:** **95 / 100**
- **Recommendation:** **ACCEPTED (Primary benchmark for `general_marine_debris` and `other_man_made_target`)**

---

### Candidate 2: Sonar Common Target Detection (SCTD) Benchmark
- **Source:** [GitHub: MingqiangNing/SCTD](https://github.com/MingqiangNing/SCTD)
- **Institution:** Harbin Engineering University / Acoustic Target Recognition Lab
- **Modality:** Real sea-trial Side-Scan Sonar (SSS) and Synthetic Aperture Sonar (SAS)
- **Objects / Classes:** Sunken ships / shipwrecks, submerged plane wrecks, mine-like subsea cylinders.
- **Annotations:** Pascal VOC XML bounding boxes (400+ high-resolution side-scan waterfall tiles).
- **License:** Open Academic / Research Use.
- **Scores:**
  - Sonar Modality: 25 / 25 (Real sidescan sonar seafloor waterfalls)
  - Annotation Quality: 23 / 25 (Pascal VOC XML bounding boxes)
  - Marine Debris Relevance: 17 / 20 (Direct match for `shipwreck` and `pipe_or_cylinder`)
  - License / Provenance: 13 / 15 (Research open-access repository)
  - Dataset Size: 8 / 10 (400+ waterfall tiles)
  - Metadata Quality: 4 / 5 (Sonar frequency and waterfall resolution documented)
- **Total Score:** **90 / 100**
- **Recommendation:** **ACCEPTED (Primary benchmark for `shipwreck` and `pipe_or_cylinder`)**

---

### Candidate 3: SubPipe Sidescan Sonar Pipeline Inspection Dataset
- **Source:** [Zenodo 10.5281/zenodo.4764835](https://doi.org/10.5281/zenodo.4764835)
- **Institution:** Heriot-Watt University
- **Modality:** High-resolution Side-Scan Sonar (SSS)
- **Objects / Classes:** Subsea pipelines, exposed cylinder conduits, pipeline spans.
- **Annotations:** Bounding boxes and line annotations.
- **License:** CC-BY 4.0.
- **Scores:**
  - Sonar Modality: 25 / 25 (Genuine SSS surveys)
  - Annotation Quality: 22 / 25 (Bounding boxes around subsea pipelines)
  - Marine Debris Relevance: 16 / 20 (Direct match for `pipe_or_cylinder`)
  - License / Provenance: 15 / 15 (CC-BY 4.0)
  - Dataset Size: 7 / 10 (Focused survey runs)
  - Metadata Quality: 4 / 5 (Towfish navigation and slant range documented)
- **Total Score:** **89 / 100**
- **Recommendation:** **ACCEPTED (Specialized candidate for `pipe_or_cylinder`)**

---

## 2. Synthesis & Multi-Source Target Alignment
By harmonizing annotations from verified open-access acoustic benchmarks:
1. `general_marine_debris` (Class 1) $\leftarrow$ Bottles, cans, cartons, tires from Marine Debris Sonar Dataset.
2. `other_man_made_target` (Class 4) $\leftarrow$ Chains, propellers, valves, hooks, submerged aircraft wrecks.
3. `shipwreck` (Class 2) $\leftarrow$ Sunken vessel hulls from SCTD Side-Scan Sonar.
4. `pipe_or_cylinder` (Class 3) $\leftarrow$ Subsea pipelines from SubPipe / SCTD.
5. `derelict_fishing_gear` (Class 0) $\leftarrow$ Ghost nets and crab pot sonar signatures.
