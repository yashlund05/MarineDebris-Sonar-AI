# MarineDebris-Sonar-AI — Dataset Acquisition Priority & Gap Analysis

**Date:** 2026-09-04  
**Framework:** Empirical Dataset Statistics & Gap Identification  
**Status:** Active Guidance for Future Field Campaigns  

---

## 1. Quantitative Baseline & V3 Gap Analysis

Based on the empirical audit of the 660 real acoustic images (899 ground-truth annotations and 84 negative background frames) in **Dataset V3**:

| Dimension | Measured Status in V3 | Gap Severity | Primary Risk |
| :--- | :--- | :---: | :--- |
| **Derelict Fishing Gear (Nets/Ropes)** | 0 positive annotations in tank data (Class 0) | **CRITICAL** | Poor generalization to tangled synthetic ghost nets and ropes. |
| **Pipelines & Cylinders (Class 3)** | Low sample count in primary FLS (present in turntable) | **HIGH** | Vulnerability in industrial conduit & drum localization. |
| **Small Targets (< 32px)** | 2 targets (0.2% of annotations) | **MEDIUM** | Distant or highly fragmented debris detection dropoff. |
| **Sensor Diversity** | 100% ARIS Explorer 3000 (3.0 MHz) | **HIGH** | Acoustic beamforming bias; potential frequency domain shift on other sonars. |
| **Depth & Offshore Environment** | Shallow water tank + flooded quarry pits | **MEDIUM** | Thermocline distortion and surface acoustic bounce in deep ocean surveys. |

---

## 2. Acquisition Priority Hierarchy

### Priority 1: In-Situ Derelict Fishing Gear (Ghost Nets & Lobster Pots)
- **Target Category:** Class 0 (`derelict_fishing_gear`).
- **Target Modality:** High-frequency Forward-Looking Sonar (ARIS 3000 or BlueView M900/P900).
- **Justification:** Derelict gillnets and crab traps represent the deadliest forms of marine debris to marine fauna. They exhibit unique diffuse acoustic backscatter and tangled shadow patterns that cannot be fully approximated by rigid bottles or tires.
- **Recommended Sources:** NOAA Marine Debris Program derelict net removal surveys, Puget Sound Ghost Gear recovery logs, Gulf of Maine trap surveys.

### Priority 2: Alternative Imaging Sonar Platforms (Cross-Sensor Generalization)
- **Target Platforms:** Teledyne BlueView M900-2250, Tritech Gemini 720ik / 1200ik, Norbit Forward-Looking Multibeam.
- **Operating Frequencies:** 720 kHz, 900 kHz, 1.2 MHz, 2.25 MHz.
- **Justification:** ARIS 3000 operates at 3.0 MHz (very high acoustic frequency with narrow beam divergence). Lower frequency sonars (720–900 kHz) exhibit higher speckle noise, lower azimuth resolution, and longer acoustic shadows.

### Priority 3: Subsea Pipeline, Drum & Cylinder Surveys
- **Target Category:** Class 3 (`pipe_or_cylinder`).
- **Justification:** Cylindrical geometries produce specular highlight lines accompanied by extensive acoustic shadows. Expanding field captures of exposed pipelines, oil drums, and discarded gas cylinders will enable reliable Class 3 detection.

### Priority 4: Far-Range Small Targets (< 32px, Low-SNR Debris)
- **Target Geometry:** Bounding boxes $< 32 \times 32$ pixels on a $640 \times 640$ normalized canvas.
- **Justification:** Targets beyond 8–10 meters range from the transducer head project onto fewer acoustic beams, yielding faint acoustic returns. Controlled acquisition of distant debris will directly improve small-target AP.

### Priority 5: High-Energy Coastal & Muddy Seabed Clutter
- **Target Condition:** Heavy silt suspension, kelp forests, rocky reefs.
- **Justification:** Expand the hard-negative background library to prevent false positive alarms on biogenic and geologic structures.
