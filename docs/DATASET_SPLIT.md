# MarineDebris-Sonar-AI: Dataset Sequence & Survey-Level Split Protocol

**Document Date:** 2026-09-01  
**Authority:** Architectural Blueprint §9, Production QA Directive  
**Status:** **ACTIVE PARTITIONING SPECIFICATION**

---

## 1. Rationale: Preventing Spatial & Temporal Leakage

Sidescan Sonar and Forward-Looking Sonar datasets consist of continuous acoustic waterfall lines or temporal frame sequences. 

> [!CAUTION]
> **Random Tile Splitting Prohibited:** Splitting neighboring frames or continuous waterfall patches randomly across `train`, `val`, and `test` causes extreme data leakage (optimistically biased validation metrics due to identical seabed textures and towfish altitude profiles).

To ensure genuine generalization:
- The dataset is partitioned into **discrete contiguous blocks / acquisition sessions**.
- All images within an acquisition sequence belong exclusively to one split.

---

## 2. Partition Breakdown

| Partition / Sequence Block | Frame Range | Target Split | Image Count | Bounding Box Count | Primary Canonical Classes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Sequence Block A** | `aris3k-0` to `aris3k-174` | **`train`** (70%) | 166 | 258 | Class 1 (`general_marine_debris`), Class 4 (`other_man_made_target`) |
| **Sequence Block B** | `aris3k-175` to `aris3k-212`| **`val`** (15%) | 35 | 55 | Class 1 (`general_marine_debris`), Class 4 (`other_man_made_target`) |
| **Sequence Block C** | `aris3k-213` to `aris3k-249`| **`test`** (15%) | 37 | 58 | Class 1 (`general_marine_debris`), Class 4 (`other_man_made_target`) |
| **Total** | `250 sequence span` | **100%** | **238** | **371** | **Harmonized 5-Class Target Taxonomy** |

---

## 3. Class Distribution by Partition

| Class ID | Class Name | Train Instances | Val Instances | Test Instances | Total Instances |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **0** | `derelict_fishing_gear` | 0 | 0 | 0 | **0** |
| **1** | `general_marine_debris` | 185 | 40 | 42 | **267** |
| **2** | `shipwreck` | 0 | 0 | 0 | **0** |
| **3** | `pipe_or_cylinder` | 0 | 0 | 0 | **0** |
| **4** | `other_man_made_target` | 73 | 15 | 16 | **104** |
| **Total** | | **258** | **55** | **58** | **371** |
