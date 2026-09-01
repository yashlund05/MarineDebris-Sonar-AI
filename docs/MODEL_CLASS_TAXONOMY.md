# MarineDebris-Sonar-AI: Model Class Taxonomy & Label Harmonization

**Date:** 2026-09-01  
**Authority:** PRD.md §8, DB_SCHEMA.md §2.4, API_SPEC.md §6, `frontend/src/types/index.ts`  
**Status:** **VERIFIED & HARMONIZED (100% Alignment across DB, API, Training, and Frontend)**  

---

## 1. Canonical Taxonomy Mapping

The project utilizes a 5-class target debris taxonomy for YOLOv8 object detection, complemented by a 6th audit rejection class (`natural_feature`) utilized strictly for false positive logging:

| Class ID | Canonical Slug / Label | Human-Readable Name | Purpose / Operational Context | DB Constraint Valid? | Frontend Type Valid? |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **0** | `derelict_fishing_gear` | Derelict Fishing Gear / Ghost Nets | Primary target: abandoned nets, traps, longlines | Yes | Yes |
| **1** | `general_marine_debris` | General Marine Debris | Plastic accumulations, containers, tires, drums | Yes | Yes |
| **2** | `shipwreck` | Shipwreck / Vessel Hull | Submerged maritime wreckage, sunken hulls | Yes | Yes |
| **3** | `pipe_or_cylinder` | Pipe or Cylinder | Subsea pipelines, metallic cylinders, torpedo tubes | Yes | Yes |
| **4** | `other_man_made_target` | Other Man-Made Target | Anchors, cinder blocks, structural debris | Yes | Yes |
| **N/A** | `natural_feature` | Natural Seabed Feature | **Audit Candidate Only:** Used exclusively when `is_filtered = True` (e.g. sand ripples, rock outcrops, boulder shadows rejected by acoustic filter). | Yes | Yes |

---

## 2. Layer-by-Layer Verification

### 2.1 Database Layer (`backend/database/models.py` & `alembic`)
The `detections` table enforces:
```sql
CHECK (class_name IN (
    'derelict_fishing_gear',
    'general_marine_debris',
    'shipwreck',
    'pipe_or_cylinder',
    'other_man_made_target',
    'natural_feature'
))
```

### 2.2 Inference Layer (`backend/inference/detector.py`)
```python
CLASS_NAMES = [
    'derelict_fishing_gear',    # Index 0
    'general_marine_debris',    # Index 1
    'shipwreck',                # Index 2
    'pipe_or_cylinder',         # Index 3
    'other_man_made_target',    # Index 4
]
```

### 2.3 Training Conversion Layer (`training/conversion/coco_to_yolo.py`)
```python
CANONICAL_CLASSES = [
    'derelict_fishing_gear',    # YOLO Class 0
    'general_marine_debris',    # YOLO Class 1
    'shipwreck',                # YOLO Class 2
    'pipe_or_cylinder',         # YOLO Class 3
    'other_man_made_target',    # YOLO Class 4
]
```

### 2.4 Frontend TypeScript Layer (`frontend/src/types/index.ts`)
```typescript
export type DetectionClass =
  | "derelict_fishing_gear"
  | "general_marine_debris"
  | "shipwreck"
  | "pipe_or_cylinder"
  | "other_man_made_target"
  | "natural_feature";
```

---

## 3. Label Normalization & Preprocessing Rules
- **Case Sensitivity:** All classes must be strictly lowercase snake_case across APIs, database rows, and JSON exports.
- **Index Consistency:** Class indices `0` through `4` are immutable and strictly mapped in both Ultralytics training and inference post-processing.
- **Audit Preservation:** Rejected seabed anomalies are recorded with `class_name = 'natural_feature'`, `is_filtered = True`, and `filtered_reason = 'acoustic_shadow_mismatch'` or `'size_constraint'`.
