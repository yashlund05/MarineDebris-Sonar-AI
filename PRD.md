# PRD.md — Product Requirements Document
## MarineDebris-Sonar-AI: AI-Powered Underwater Marine Debris Detection System

**Version:** 1.0  
**Date:** August 2026  
**Team:** 3 Developers  

---

## 1. Problem Statement

Marine debris — including derelict fishing gear, abandoned crab pots, ghost nets, shipwrecks, and industrial waste — poses a serious ecological and navigational hazard on the seabed. Manual inspection of side-scan sonar (SSS) imagery is slow, expensive, requires specialist expertise, and is inconsistent across surveyors.

This project builds an end-to-end AI system that automatically ingests side-scan sonar data, preprocesses it for acoustic noise and artifacts, detects and classifies man-made seabed objects, georeferences each detection, and presents actionable results through an interactive web dashboard with downloadable reports.

This directly implements **SIH 2026 PS26057** ("AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery", MoES/NIOT, Disaster Management theme). See Section 9, "PS26057 Compliance Matrix," for the requirement-by-requirement mapping.

---

## 1.1 Core Terminology (authoritative — used identically across all six spec files)

### Natural vs. Artificial Anomaly (first-class distinction)

The system's central task is separating **artificial/man-made anomalies** from **natural seafloor topology**. This is not "an object detector that also happens to see rocks" — it is a reasoning pipeline:

```
SSS imagery
  → preprocessing (noise/shadow/resolution normalization)
  → candidate detection (YOLOv8)
  → classification (artificial target class)
  → sonar-aware anomaly verification (shadow/size/shape plausibility checks)
  → natural-feature / false-positive rejection
  → final anomaly result
```

- **Natural seabed features** (rocks, sand ripples, ridges, natural acoustic shadows, sensor noise/artifacts) are not target classes to be reported as debris; the `natural_feature` class (see Section 9 / `DB_SCHEMA.md`) exists so rejected/filtered candidates can still be logged and audited — it is an internal bookkeeping class, not a user-facing "detection type."
- **Artificial anomalies** are the reportable classes: `derelict_fishing_gear`, `general_marine_debris`, `shipwreck`, `pipe_or_cylinder`, `other_man_made_target` (canonical taxonomy defined in Section 8).

### Confidence — two distinct, non-interchangeable numbers

| Term | Field name (DB/API) | Definition |
|---|---|---|
| **Model Confidence** | `confidence` | Raw score output by the YOLOv8 detector for a candidate box (0–1 / 0–100%). This is **not** a calibrated probability. |
| **Final Anomaly Confidence** | `confidence_calibrated` | `confidence` after (a) temperature/Platt-scaling calibration and (b) adjustment by the sonar-aware verification stage (shadow-context filter, size/shape constraint filter). This is the number surfaced as the primary confidence to end users. |

Example (illustrative only, not a validated result):

```
Classification: derelict_fishing_gear
Model confidence: 94%
Final anomaly confidence: 89%
```

No specific calibration formula is mandated beyond temperature/Platt scaling (see `ARCHITECTURAL_BLUEPRINT.md` §5, §8); if a precise combined-score formula is not yet implemented, it must be described conceptually rather than presented as exact.

---

## 2. Target Audience / User Personas

### Persona 1 — Marine Survey Operator (Primary)
- **Who:** Field technician running AUV/towfish SSS surveys for environmental agencies or commercial clients.
- **Goal:** Quickly identify man-made debris or hazards from sonar logs without waiting days for manual expert review.
- **Pain Points:** Hours of sonar footage, high false-positive rate from rocks/shadows, no easy way to export geotagged findings to GIS tools.
- **Tech Comfort:** Moderate. Comfortable uploading files and reading maps; not a data scientist.

### Persona 2 — Environmental Scientist / Researcher (Secondary)
- **Who:** Marine biologist or oceanographer studying debris distribution.
- **Goal:** Get structured, reproducible detection outputs (GeoJSON/CSV) that can feed into GIS analyses.
- **Pain Points:** No standardized pipeline; results vary by analyst.
- **Tech Comfort:** High. Comfortable with scripts, APIs, and data formats.

### Persona 3 — Fisheries Enforcement / Regulatory Officer (Secondary)
- **Who:** Government officer monitoring derelict gear removal compliance.
- **Goal:** Map and document locations of abandoned crab pots and derelict fishing gear in a jurisdiction.
- **Pain Points:** Lack of automated tooling; manual processes can't scale to large survey areas.
- **Tech Comfort:** Low to moderate. Needs a clean UI with map output and PDF/CSV reports.

### Persona 4 — ML/CV Developer (Internal)
- **Who:** One of the 3 project developers responsible for model training and evaluation.
- **Goal:** Run training experiments, evaluate per-class metrics, export models for edge deployment.
- **Pain Points:** Disorganized dataset formats, inconsistent annotation standards across SSS datasets.
- **Tech Comfort:** High.

---

## 3. Core Goal

Build a modular, upload-to-report AI pipeline that:
1. Accepts raw SSS data (XTF/JSF files or pre-exported sonar images/PNG strips).
2. Applies sonar-specific preprocessing (bottom detection, slant-range correction, CLAHE, denoising).
3. Runs AI detection (YOLO-family) and optional segmentation (U-Net/SegFormer).
4. Filters false positives using acoustic-shadow and sonar-context rules.
5. Geotags each detection to a real-world latitude/longitude using navigation metadata.
6. Exports results as JSON, CSV, and GeoJSON.
7. Displays findings in an interactive web dashboard with sonar viewer + map.

---

## 4. Scope

### In-Scope (MVP and V1)

| Feature | Priority |
|---|---|
| XTF file ingestion and metadata extraction (initial supported raw format) | MVP |
| PNG image strip ingestion (initial supported pre-exported format) | MVP |
| Streaming/chunked parsing of long sonar logs (no whole-survey in-RAM array) | MVP |
| Sonar preprocessing pipeline (bottom detection, normalization, CLAHE, denoising, water-column removal, slant-range correction) | MVP |
| Sonar Quality / Motion Robustness Layer (dropout detection, degraded-region flagging, quality scoring) | MVP |
| Tile/ping builder for model-ready patches | MVP |
| YOLOv8 object detector (baseline; bounding box) | MVP |
| Model confidence + Final anomaly confidence per detection (see §1.1) | MVP |
| NMS and sonar-aware false-positive filtering (shadow-context, size/shape) | MVP |
| Per-class detection: `derelict_fishing_gear`, `general_marine_debris`, `shipwreck`, `pipe_or_cylinder`, `other_man_made_target` | MVP |
| Basic georeferencing: pixel bbox → lat/lon using available ping nav metadata (lat/lon, heading, altitude, range) | MVP |
| JSON / CSV / GeoJSON report export | MVP |
| Web dashboard: sonar viewer, detection overlay, bounding boxes | MVP |
| Interactive map showing geotagged detections (when available) | MVP |
| Demo mode with bundled sample sonar data | MVP |
| JSF file ingestion (deferred — see §4.1 Format Priority) | V1 |
| TIFF image ingestion (deferred — see §4.1 Format Priority) | V1 |
| U-Net / SegFormer segmentation (pixel masks, AI4Shipwrecks) | V1 |
| Multi-dataset training pipeline (Ghost Pot + SubPipe + AI4Shipwrecks) | V1 |
| Side-by-side raw vs. enhanced sonar viewer | V1 |
| Detection filter UI (by class, confidence, severity) | V1 |
| Port/starboard channel handling as a distinct pipeline path | V1 |
| Advanced georeferencing (richer navigation/attitude corrections) | V2 |
| Edge/lightweight model export (quantization/distillation, ONNX, onboard AUV inference) | V2 |
| Expanded taxonomy (e.g. standalone `ghost_net` class) once sufficient labeled data exists | V2 |

### 4.1 Format Priority

**Initial supported formats (MVP):** XTF (raw sonar log, primary competition-relevant format) and PNG (pre-exported sonar image strips, matches the format most public SSS datasets ship in).

**Future formats (deferred, not removed from the architecture):** JSF and TIFF remain valid `file_type` values in `DB_SCHEMA.md` and accepted upload types in `API_SPEC.md` for forward compatibility, but their parsers are not required for the MVP demonstration and are implemented only once XTF/PNG paths are validated end-to-end.

### Out-of-Scope

- Ghost-net as a standalone class (insufficient labeled SSS data at project start; revisit when labels are secured — see §8 Dataset Taxonomy Mapping).
- Forward-looking sonar (FLS) as primary input — FLS data is a different modality and will only be used for supplementary pretraining if at all.
- RGB satellite imagery processing.
- Beach/surface debris detection.
- Real-time sonar feed (streaming) ingestion — batch file upload only. ("Streaming/chunked parsing" above refers to processing a large uploaded file in chunks, not a live sensor feed.)
- Automated removal operations / robotics integration.
- User account management / multi-tenancy (single-user local/server deployment for V1).
- Mobile native app.

---

## 5. User Stories

### Ingestion
- **US-01:** As a Survey Operator, I want to upload an XTF or JSF sonar file so the system automatically parses sonar pings and navigation metadata without manual configuration.
- **US-02:** As a Survey Operator, I want to upload a folder of sonar PNG strips when I don't have the original XTF/JSF file.
- **US-03:** As a Developer, I want the system to display a processing progress bar so I know the pipeline is running.

### Preprocessing
- **US-04:** As a Survey Operator, I want to see both the raw sonar image and the preprocessed/enhanced version side-by-side so I can judge how much enhancement was applied.
- **US-05:** As a Researcher, I want preprocessing parameters (CLAHE clip limit, denoising strength) to be logged in the output report for reproducibility.

### Detection
- **US-06:** As a Survey Operator, I want the system to automatically draw bounding boxes over detected objects on the sonar image with a confidence score label.
- **US-07:** As a Regulatory Officer, I want the system to classify each detection into one of the supported target classes (derelict gear, debris, shipwreck, pipe, other).
- **US-08:** As a Researcher, I want to filter detections by minimum confidence threshold and class to reduce false positives in the output.
- **US-09:** As a Survey Operator, I want the system to indicate when a detection was filtered out as a likely acoustic artifact so I understand why it was excluded.

### Georeferencing
- **US-10:** As a Regulatory Officer, I want each detected object to have an estimated latitude and longitude so I can plan physical recovery operations.
- **US-11:** As a Researcher, I want estimated object dimensions (length × width in metres) for each detection to support debris assessment.
- **US-12:** As a Developer, I want the system to clearly mark a detection as "geotagging unavailable" when the sonar file lacks navigation metadata rather than fabricating coordinates.

### Reporting
- **US-13:** As a Researcher, I want to download a GeoJSON file of all detections to import directly into QGIS or ArcGIS.
- **US-14:** As a Regulatory Officer, I want a CSV report with one row per detection containing class, confidence, coordinates, and dimensions.
- **US-15:** As a Survey Operator, I want a JSON report that matches the defined report schema for programmatic consumption.

### Dashboard
- **US-16:** As a Survey Operator, I want an interactive map that shows pins for every geotagged detection so I can see the spatial distribution across the survey area.
- **US-17:** As a Survey Operator, I want to click on a detection pin on the map and see the corresponding sonar image patch and metadata in a side panel.
- **US-18:** As a Regulatory Officer, I want to filter the map by detection class and confidence to focus on high-priority findings.
- **US-19:** As a Developer, I want to see processing status (pipeline stage, model version, inference latency) in the dashboard for debugging.
- **US-20:** As any user, I want a Demo Mode with pre-loaded sample sonar data so I can explore the system without needing my own sonar file.

### Training (Developer-facing)
- **US-21:** As a Developer, I want a unified annotation format converter that transforms COCO, YOLO, and dataset-specific formats into a single internal schema.
- **US-22:** As a Developer, I want survey-level train/validation/test splits (not random image-level) to prevent data leakage from correlated adjacent pings.
- **US-23:** As a Developer, I want per-class evaluation metrics (precision, recall, mAP50, mAP50-95, F1) in a human-readable report after each training run.

---

## 6. Success Metrics

These are **targets to evaluate against**, not achieved results. Any metric value appearing elsewhere in this documentation (e.g. `mAP50 = 0.724` in `DB_SCHEMA.md` seed data) is illustrative/mock unless a real training run has produced it.

| Metric | Target |
|---|---|
| mAP50 on held-out Ghost Pot SSS test set (survey-level split) | ≥ 0.70 |
| mAP50-95 | ≥ 0.45 |
| False positive rate on known acoustic artifact patches | < 15% |
| Geotagging position error | Evaluated only when navigation metadata and ground-truth position are both available; no fixed accuracy figure (e.g. "≤5 m") is guaranteed as a general system capability. Where ground truth exists, report the measured error rather than asserting a target. |
| Dashboard page load time (post-processing) | < 3 s |
| Batch processing throughput | ≥ 10 SSS tiles/sec on GPU |
| Edge model inference latency (CPU, V2 optimization stage) | < 200 ms per tile |

---

## 7. Constraints and Known Limitations

- Ghost-net labels are scarce in public SSS datasets; `ghost_net` is not a guaranteed trained class. `derelict_fishing_gear` is the broader canonical class used at MVP; a standalone `ghost_net` class is V2/future work, contingent on sufficient labeled data (see §8).
- FLS and SSS modalities must never be blindly merged — model trained on one cannot be evaluated on the other.
- Basic georeferencing requires per-ping navigation metadata (lat/lon, heading, altitude, range); without it, only relative pixel positions are available and detections are marked `geotagging_available: false` rather than assigned fabricated coordinates. Advanced (higher-accuracy) georeferencing additionally depends on richer attitude/navigation metadata that is not guaranteed to be present in every source file.
- Sonar acquisition motion (heave, pitch, roll) and data dropouts are not fully compensated unless the source file provides the corresponding attitude/navigation channels. The MVP Sonar Quality / Motion Robustness Layer provides quality scoring and dropout/degraded-region detection, not full physical motion compensation. Where sensor attitude data is unavailable, robustness is evaluated using simulated/augmented degradation, clearly labeled as such (never presented as measured real-survey performance).
- Adjacent sonar pings from the same survey are highly correlated — random image splits inflate metrics; survey-level splits are mandatory.
- Acoustic shadows can partially occlude objects; segmentation labels require expert verification.
- Model Confidence (raw detector output) is not automatically a calibrated probability. The pipeline applies temperature/Platt scaling plus sonar-aware verification to produce Final Anomaly Confidence (see §1.1); no more precise formula is guaranteed unless already implemented and evaluated.
- Initial format support is XTF and PNG only; JSF and TIFF parsing is deferred (§4.1).

---

## 8. Dataset Sources & Taxonomy Mapping

Datasets are **not** simply concatenated. Each source dataset's original classes are mapped explicitly into the canonical project taxonomy below before training.

### Canonical Taxonomy

`derelict_fishing_gear` · `general_marine_debris` · `shipwreck` · `pipe_or_cylinder` · `other_man_made_target`

(`natural_feature` is an internal rejection/audit label, not a training target — see §1.1.)

| Dataset | Format | Size | License | Original Class(es) | Canonical Mapping | Nav Metadata | Use |
|---|---|---|---|---|---|---|---|
| Ghost Pot SSS (PING Ecosystem / HuggingFace) | SSS images + YOLO bbox | 6,674 images | CC-BY-SA-4.0 | crab pot / derelict gear | `derelict_fishing_gear` | Not guaranteed per-image | Primary training |
| SubPipe (REMARO) | SSS images + YOLO/COCO | 10,030 images / 6,335 annotations | Check repo | pipe | `pipe_or_cylinder` | Partial (survey-level) | Secondary training |
| AI4Shipwrecks | SSS images + segmentation masks | 286 labeled images | Check repo | shipwreck | `shipwreck` | Partial | Segmentation train/eval |
| NOAA GOMMDP | GeoJSON / location files | Varies | Public | n/a (locations only) | Not a training class — geospatial context only | Yes (location) | Geospatial reference only |
| SeabedObjects | SSS images | 385 ships, 62 planes | Academic | ship, plane | `shipwreck`, `other_man_made_target` | Not guaranteed | Supplementary training |

Do not force an incompatible source class into a canonical class it does not resemble; if a source class has no reasonable mapping, exclude it rather than misassigning it, and record the exclusion in the training run's dataset manifest.

---

## 9. PS26057 Compliance Matrix

| PS26057 Requirement | Project Implementation | Status |
|---|---|---|
| SSS ingestion | XTF (MVP) + PNG (MVP) ingestion; JSF/TIFF deferred (§4.1) | Implemented (MVP formats) |
| Artificial anomaly detection | YOLOv8 baseline detector + sonar-aware verification pipeline (§1.1) | Implemented |
| Shipwreck detection | `shipwreck` class, trained from AI4Shipwrecks + SeabedObjects (§8) | Implemented |
| Pipe/cylinder detection | `pipe_or_cylinder` class, trained from SubPipe (§8) | Implemented |
| Fishing gear / entangled debris | `derelict_fishing_gear` class, trained from Ghost Pot SSS; standalone `ghost_net` deferred to V2 pending labeled data | Implemented (broader class); expansion deferred |
| Noise handling (speckle) | Preprocessing: denoising, CLAHE, normalization (MVP) | Implemented |
| Acoustic shadow handling | Shadow-context filter in sonar-aware verification (MVP) | Implemented |
| Resolution variation | Preprocessing normalization + tiling; augmentation for robustness | Implemented |
| Motion (heave/pitch/roll) & dropout robustness | Sonar Quality / Motion Robustness Layer: quality scoring, dropout/degraded-region detection (MVP); full physical motion compensation only where attitude data exists (V1/V2) | Partially implemented — quality-layer scope only at MVP |
| Confidence scoring | Model Confidence + Final Anomaly Confidence, defined in §1.1 | Implemented |
| False-positive reduction | Sonar-aware verification + NMS + calibration | Implemented |
| Geotagging | Basic georeferencing using available ping nav metadata; conditional, not guaranteed for every source file | Implemented (conditional) |
| Dimensions | `estimated_length_m` / `estimated_width_m` from bbox + range resolution | Implemented |
| JSON/CSV/GeoJSON reporting | Reporting engine (`API_SPEC.md` §8, §11) | Implemented |
| UI dashboard | Web dashboard (`UI_UX_SPEC.md`) | Implemented |
| Map visualization | Leaflet detection map | Implemented |
| Edge readiness | Deferred to V2 optimization stage (quantization/distillation/ONNX), not a prerequisite for MVP demo | Planned (V2) |

---

*End of PRD.md*
