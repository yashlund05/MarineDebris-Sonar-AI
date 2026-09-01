# MarineDebris-Sonar-AI: Dataset Class Taxonomy Mapping

**Date:** 2026-09-01  
**Lead Engineer:** Senior Computer Vision & Sonar Data Engineer  
**Canonical Project Taxonomy:** PRD.md §8, DB_SCHEMA.md §2.4, API_SPEC.md §6  

---

## 1. Source-to-Target Class Harmonization Table

The following authoritative mapping translates object categories from candidate marine debris and underwater acoustic benchmarks into the project's canonical 5-class target taxonomy:

| Source Dataset | Source Class Name | Target Class ID | Target Class Name | Justification | Mapping Confidence |
| :--- | :--- | :---: | :--- | :--- | :---: |
| **Marine Debris Sonar** | `bottle` | **1** | `general_marine_debris` | Direct semantic match for consumer plastic/glass debris | **High (1.0)** |
| **Marine Debris Sonar** | `can` | **1** | `general_marine_debris` | Metal beverage cans discarded in marine environment | **High (1.0)** |
| **Marine Debris Sonar** | `drink-carton` | **1** | `general_marine_debris` | Discarded tetra-pak/cardboard consumer waste | **High (1.0)** |
| **Marine Debris Sonar** | `shampoo-bottle`| **1** | `general_marine_debris` | High-density polyethylene plastic debris | **High (1.0)** |
| **Marine Debris Sonar** | `standing-bottle` | **1** | `general_marine_debris` | Upright glass bottle debris on seabed | **High (1.0)** |
| **Marine Debris Sonar** | `tire` | **1** | `general_marine_debris` | Synthetic rubber tire marine debris | **High (1.0)** |
| **Marine Debris Sonar** | `propeller` | **4** | `other_man_made_target` | Submerged metallic propulsion machinery | **High (1.0)** |
| **Marine Debris Sonar** | `chain` | **4** | `other_man_made_target` | Steel mooring and anchoring chains | **High (1.0)** |
| **Marine Debris Sonar** | `hook` | **4** | `other_man_made_target` | Submerged heavy rigging and metallic hooks | **High (1.0)** |
| **Marine Debris Sonar** | `valve` | **4** | `other_man_made_target` | Industrial pipeline valve and manifold fittings | **High (1.0)** |
| **SCTD Sonar** | `shipwreck` / `ship` | **2** | `shipwreck` | Sunken vessel hull on seabed | **High (1.0)** |
| **SCTD Sonar** | `aircraft` / `plane` | **4** | `other_man_made_target` | Submerged aircraft wreckage | **High (1.0)** |
| **SubPipe Sonar** | `pipe` / `pipeline` | **3** | `pipe_or_cylinder` | Subsea pipeline conduits and cylindrical structures | **High (1.0)** |
| **GhostPot SSS** | `ghost_pot` / `net` | **0** | `derelict_fishing_gear` | Abandoned traps, crab pots, and gillnets | **High (1.0)** |
| **Any Source** | `wall` / `tank` | **EXCLUDE** | *None* | Tank boundary fixture; not debris | **Exclusion** |
| **Any Source** | `rock` / `seabed` | **EXCLUDE** | *None* | Natural geomorphic feature; negative background | **Exclusion** |

---

## 2. Strict Class-Mapping Rules
1. **No Pseudo-Debris Mapping:** Geomorphic seabed features (`rock`, `boulder`, `sand_ripple`) must **never** be mapped to `general_marine_debris`.
2. **Deterministic Category Filtering:** Only objects matching the canonical taxonomy $\{0, 1, 2, 3, 4\}$ receive positive bounding box labels.
3. **Audit Preservation:** Negative seabed anomalies are reserved exclusively for the post-processing acoustic filter verification and tagged as `natural_feature` when filtered.
