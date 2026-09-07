# Sonar Visibility & Enhancement Workstation — Operator & Researcher Guide

## 1. Accessing the Workstation
In the MarineDebris-Sonar-AI navigation:
1. Select the **RESEARCH** mode from the top header or sidebar.
2. Click **Enhancement Lab** (`/enhancement`) in the research navigation panel.

---

## 2. Interactive Split-Slider Viewer
The central viewport renders raw vs enhanced acoustic frames with pan/zoom and split visualization:
- **Draggable Vertical Slider**: Click and drag the cyan divider horizontally to dynamically inspect before/after transitions.
- **View Modes**:
  - **Split Slider**: Default overlay mode with interactive divider.
  - **Side-by-Side**: Places raw and enhanced images into synchronized parallel viewports.
  - **Enhanced Only**: Full-screen presentation with active pseudocolor mapping.
  - **Canonical Float**: Renders the underlying single-channel float32 $[0, 1]$ grayscale scientific image.
- **Pan & Zoom**:
  - Scroll wheel to zoom ($0.4\times$ to $6.0\times$).
  - Click and drag anywhere in the viewport to pan.
  - Press `Reset` to re-center the viewport at $100\%$ scale.
  - Click `Fullscreen` for high-resolution target inspection.

---

## 3. Operational Profiles & Scientific Hypotheses
The workstation provides 7 candidate operational profiles. Each profile represents a specific operational hypothesis to be evaluated:

| Profile | Primary Algorithm | Acoustic Context |
|---|---|---|
| **Balanced** | Bilateral + CLAHE | General-purpose coastal & estuary surveys. Edge preservation with balanced dynamic range. |
| **Low-SNR** | Homomorphic Bilateral | Highly turbid water, high acoustic reverberation, weak return signatures. |
| **High-Contrast** | Unsharp Mask + CLAHE | Hard metallic debris, cylindrical pipes, sharp boundary delineation. |
| **Heavy Clutter** | Median (k=5) + CLAHE | Rocky seabed, quarry walls, impulsive multipath reflections. |
| **Long-Range** | Gamma Correction ($\gamma=0.6$) | Far-field attenuation compensation ($>10\text{ m}$ range on ARIS 3000). |
| **Human Inspection** | Tuned Bilateral + CLAHE | Optimized specifically for human eye differentiability in ARIS Amber. |
| **Detection Optimized** | Production CLAHE (clip=2.0) | Standard preprocessing alignment with the YOLOv8 detector. |

---

## 4. Display-Only Pseudocolor Palettes
Display palettes map single-channel acoustic intensity to RGB colors for presentation:
- **ARIS Copper / Amber**: Sound Metrics ARIS 3000 standard. Acoustic shadows are black, background seabed is dark amber, targets appear bright gold/yellow, and peak returns reach pure white.
- **Monotonic Thermal**: Oceanographic progression preserving monotonic intensity ordering to prevent false contour boundaries.
- **Inferno**: Colorblind-safe perceptually uniform colormap.
- **Scientific Grayscale**: Raw acoustic backscatter intensity without false coloring.

> **Rule**: The pseudocolor image is strictly a presentation layer and is never fed to the YOLOv8 detection model.

---

## 5. Interpreting Quantitative Metrics
The bottom bar displays measured metrics for the active frame:
- **ENL (Looks)**: Equivalent Number of Looks evaluated on a homogeneous background ROI. Higher values indicate reduced acoustic speckle noise.
- **CNR (Contrast-to-Noise Ratio)**: Evaluated on the centroid-eroded target interior vs the surrounding dilated background ring. Higher values indicate targets stand out clearly above clutter.
- **EPI (Edge Preservation Index)**: High-pass Laplacian energy ratio. A value of $1.000$ indicates perfect edge retention; $>1.0$ indicates boundary sharpening; $<0.5$ warns of boundary blurring.
- **CPU Latency (ms)**: Measured execution latency on host CPU. Latencies $\le 10.0\text{ ms}$ qualify for real-time edge processing.
