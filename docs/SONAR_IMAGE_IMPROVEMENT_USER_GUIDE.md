# Sonar Image Improvement System — Operator & Research User Guide

**System**: MarineDebris-Sonar-AI Workstation  
**Capability**: Project-Wide Intelligent Acoustic Image Improvement  

---

## 1. Introduction

Forward-Looking Sonar (FLS) acoustic images captured at 3.0 MHz exhibit severe physical acoustic speckle, low ambient contrast, and reverberation noise that make small debris targets difficult to detect by human operators.

The **Sonar Image Improvement System** enables operators and research scientists to inspect acoustic frames using three synchronized display modes everywhere sonar imagery is presented across the platform:
- **`RAW`**: Direct acoustic backscatter sensor return (completely unmodified).
- **`IMPROVED`**: Denoised, edge-preserved, contrast-boosted acoustic imagery.
- **`SPLIT`**: Interactive before/after split slider allowing real-time forensic comparison on the exact same frame.

---

## 2. Keyboard Navigation & Shortcuts

When viewing any sonar frame equipped with the `SonarImageViewer`, use these rapid keyboard shortcuts:

| Key | Action | Description |
|---|---|---|
| `R` | **Switch to RAW** | Instantly displays unmodified acoustic sensor backscatter |
| `I` | **Switch to IMPROVED** | Displays noise-reduced, contrast-equalized FLS imagery |
| `S` | **Switch to SPLIT** | Activates interactive draggable split divider slider |
| `0` | **Reset Zoom & Pan** | Centers the frame and resets magnification to 100% |
| `F` | **Toggle Fullscreen** | Expands the workstation to full display for deep investigation |
| `+` / `=` | **Zoom In** | Increments magnification up to 600% |
| `-` | **Zoom Out** | Decrements magnification down to 75% |

---

## 3. Workstation Controls & Features

### A. Draggable Split Slider (`SPLIT` Mode)
- Click or touch the white circular handle in the center of the divider line.
- Drag left or right to reveal more of the **RAW** (left) or **IMPROVED** (right) acoustic return.
- Pan and zoom interactions remain 100% synchronized across both sides of the divider.

### B. Display Palette Selection
Switch between standardized oceanographic colormaps via the dropdown menu in the toolbar:
1. **ARIS Amber** (Default): Industry-standard amber/copper acoustic colormap optimized for human photopic response in low-light marine bridge environments.
2. **Thermal**: Luminance-preserving blue-purple-yellow gradient for high dynamic range target isolation.
3. **Inferno**: Perceptually uniform, colorblind-safe colormap designed for publication-quality contrast.
4. **Grayscale**: Pure linear radiometric display representing raw acoustic backscatter intensity.

### C. Operational Profiles
Select pre-tuned parameter sets optimized for specific underwater acoustic conditions:
- **`BALANCED`** (Bilateral + CLAHE): Recommended default for general survey passes. Preserves sharp debris boundaries while smoothing high-frequency speckle.
- **`LOW_SNR`** (Median + CLAHE): Optimized for high-turbidity waters or distant acoustic returns where impulsive speckle dominates.
- **`HIGH_CONTRAST`** (Unsharp + CLAHE): Maximizes acoustic highlight-to-shadow transitions for small composite and metallic fragments.
- **`HEAVY_CLUTTER`**: Suppresses non-uniform background reverberation on rocky or uneven sea floors.

---

## 4. Acoustic Quality Metrics & Scientific Disclosures

Click the **Acoustic Processing Disclosure** bar at the bottom of the viewer to reveal real-time scientific parameters:

- **Equivalent Number of Looks (ENL)**: Quantitative measure of speckle suppression, evaluated strictly on homogeneous acoustic background regions ($\mu^2 / \sigma^2$).
- **Contrast-to-Noise Ratio (CNR)**: Quantitative separation between target acoustic highlights and surrounding seabed rings.
- **Edge Preservation Index (EPI)**: High-boost Laplacian gradient preservation ratio (1.000 = baseline).
- **Execution Latency**: Measured CPU processing time in milliseconds (typically 5–18 ms for real-time operation).

---

## 5. Platform-Wide Availability

The improvement system is integrated into all core investigation workflows:
1. **Mission Control / Main Workstation (`/`)**: Toggle between Raw, Processed, and Split waterfall displays.
2. **Sonar Replay Lab (`/replay`)**: Frame-by-frame temporal playback with real-time enhancement and anomaly scrubbing.
3. **Forensic Evidence Dossier (`/evidence`)**: Target investigation with synchronized tri-pane and interactive split slider.
4. **Failure Analysis Explorer (`/failures`)**: Real-time diagnosis of false negatives and low-contrast debris targets.
5. **Intelligent Enhancement Lab (`/enhancement`)**: Interactive algorithm tuning, batch comparison, and parameter optimization.
