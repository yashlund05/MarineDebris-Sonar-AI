# Third-Party Software Notices and Attribution

This project incorporates and adapts code and algorithmic implementations from the following open-source software:

---

## SidescanTools

- **Upstream Repository**: [https://github.com/sonoware/sidescantools](https://github.com/sonoware/sidescantools)
- **Copyright**: (c) 2023-2025 SidescanTools Team (<sidescantools@sonoware.de>), Sonoware GmbH, Aili Xue
- **License**: GNU General Public License Version 3 (GPL-3.0)
- **SPDX-License-Identifier**: GPL-3.0-or-later
- **Integration Strategy**:
  The acoustic radiometric processing algorithms from sidescantools.sidescan_preproc and sidescantools.aux_functions are adapted within ackend/services/sonar_enhancement/sidescan_adapter.py to serve as the core preprocessing foundation for Forward-Looking Sonar (FLS) and Side-Scan Sonar (SSS) imagery in MarineDebris-Sonar-AI.
  
  Specifically adapted algorithmic components:
  1. **2D-FFT Pie-Slice Stripe Noise Filter**: Directional frequency-domain suppression of horizontal acquisition stripes (uild_pie_H, get_sup_line_lin, pply_pie_slice_filter).
  2. **Homomorphic High-Frequency Sharpening Filter**: Log-domain frequency emphasis filter (comp_D, pply_sharpening_filter).
  3. **Acoustic Dynamic Range dB Conversion**: Amplitude to decibels logarithmic transform (convert_to_dB).
  4. **Contrast-Limited Adaptive Histogram Equalization**: Local contrast expansion (hist_equalization).
  5. **Gain Normalization Gates**: Beam Angle Correction (BAC) and Empirical Gain Normalization (EGN) metadata checks.

### License Text Summary
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

A copy of the GNU General Public License is available at: <https://www.gnu.org/licenses/gpl-3.0.html>.

---

## 5. NanKai Sonar Image Dataset (NKSID)
- **Source:** Nankai University, College of Artificial Intelligence
- **Authors:** Wenpei Jiao, Jianlei Zhang, Chunyan Zhang
- **Publication:** "Open-set recognition with long-tail sonar images", Expert Systems with Applications, 2024
- **License:** MIT License
- **Copyright:** (c) 2023 Wenpei Jiao
- **Sensor:** Oculus M750d Multi-beam Forward-Looking Sonar (1.2 MHz / 750 kHz)
- **Usage:** Canonical evaluation benchmark for derelict_fishing_gear and pipe_or_cylinder.

---

## 6. SeabedObjects-KLSG / TGRS BETL Dataset
- **Source:** Hohai University / Ocean University of China
- **Authors:** Guanying Huo, Zhengxian Yang, Wenpei Jiao
- **Publication:** "Underwater object classification in sidescan sonar images using deep transfer learning and semisynthetic training data", IEEE TGRS 2020 / 2022
- **License:** MIT License
- **Copyright:** (c) 2023 Wenpei Jiao
- **Sensor:** Klein 3000 Side-Scan Sonar Towfish (455 kHz / 900 kHz)
- **Usage:** Canonical evaluation benchmark for shipwreck.

---

## 7. Marine Debris FLS Benchmark (Turntable Series)
- **Source:** University of Groningen / Heriot-Watt University Ocean Systems Lab
- **Author:** Dr. Matias Valdenegro-Toro
- **DOI:** 10.5281/zenodo.15101686
- **Publication:** "Marine Debris Detection and Segmentation with Forward-Looking Sonar", IEEE/OES AUV 2020
- **License:** Creative Commons Attribution 4.0 International (CC-BY 4.0)
- **Sensor:** Sound Metrics ARIS Explorer 3000 (3.0 MHz)
- **Usage:** Canonical evaluation benchmark for pipe_or_cylinder.
