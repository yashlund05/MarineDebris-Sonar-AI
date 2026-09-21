# Sonar-Aware Acoustic Augmentation Guide

This guide establishes the theoretical foundations, acoustic physics justifications, and operational specifications for data augmentation in the `MarineDebris-Sonar-AI` object detection pipeline.

---

## 1. Acoustic Physics Rationale vs. Optical Image Augmentation

Standard computer vision augmentation techniques developed for optical cameras (ImageNet, COCO) make implicit physical assumptions that are invalid or destructive for underwater acoustic imaging:

| Optical Technique | Acoustic Validity | Physical Rationale & Impact on Sonar |
| :--- | :--- | :--- |
| **Hue / Saturation Jitter (`hsv_h`, `hsv_s`)** | **STRICTLY PROHIBITED** | Sonar sensors emit single-frequency acoustic pulses and measure scalar pressure waves (backscatter intensity). Acoustic data has no optical wavelength spectrum or color. Applying color shifts destroys acoustic intensity calibration. |
| **Vertical Flipping (`flipud`)** | **STRICTLY PROHIBITED** | In forward-looking sonar (FLS) and side-scan sonar (SSS), the range axis represents time-of-flight from the sensor. Highlights always face the transducer, followed by acoustic shadows behind the target. Vertical flipping places shadows in front of targets, creating physically impossible acoustic artifacts. |
| **Unconstrained Copy-Paste** | **PROHIBITED** | Acoustic wavefronts cannot be naively blended. Pasting targets without continuous seabed acoustic shadows breaks spatial coherence and causes detectors to hallucinate floating objects. |
| **Multiplicative Speckle Noise** | **RECOMMENDED** | Speckle is the coherent interference pattern of sub-resolution acoustic scatterers. Modeling multiplicative speckle via Rayleigh and Gamma distributions reflects physical sea-state turbulence. |
| **Transmission Loss / TVG Jitter** | **RECOMMENDED** | Acoustic wave energy attenuates via geometric spreading ($20\log_{10} r$) and seawater absorption ($\alpha r$). Perturbing time-varied gain (TVG) trains models to identify debris under poor propagation. |
| **Periodic Beam Stripe Noise** | **RECOMMENDED** | Multibeam transducers exhibit inter-element beam calibration drift and angular sensitivity ripples. Simulating horizontal/radial stripe artifacts improves detector robustness. |
| **Port/Starboard Swath Symmetry (`fliplr`)** | **RECOMMENDED** | Acoustic cameras have bilateral beam symmetry across the cross-range swath. Horizontal reflection preserves grazing incidence angles and shadow geometry. |

---

## 2. Mathematical Formulations

### 2.1 Multiplicative Acoustic Speckle
Speckle noise is modeled as multiplicative granular interference:
$$I_{\text{noisy}}(x, y) = I(x, y) \cdot \eta(x, y)$$
where $\eta$ is drawn from a Gamma distribution with unit mean:
$$\eta \sim \text{Gamma}\left(\kappa, \frac{1}{\kappa}\right), \quad \kappa = \frac{1}{\sigma_{\text{speckle}}^2}$$
or a Rayleigh distribution parameterized by backscatter variance $\sigma$.

### 2.2 Range Transmission Loss & Gain Attenuation
As acoustic pulses propagate through the water column, signal intensity drops across the range axis $y$:
$$A(y) = 1.0 - \alpha_{\text{absorb}} \cdot \left(\frac{y}{H}\right)$$
where $H$ is image height, and $\alpha_{\text{absorb}} \in [0.08, 0.25]$ simulates environmental absorption variability.

### 2.3 Transducer Periodic Stripe Artifacts
Beam calibration imbalances are modeled as harmonic spatial intensity modulations:
$$S(x) = 1.0 + A_{\text{stripe}} \cdot \sin\left(2\pi f x + \phi\right)$$
where $f$ matches multibeam array element frequencies and $\phi \sim \mathcal{U}(0, 2\pi)$.

---

## 3. Standard Augmentation Policies

| Parameter | BASELINE | CONSERVATIVE_SONAR | NOISE_ROBUST | SMALL_OBJECT | HARD_NEGATIVE |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Speckle Probability** | 0.00 | 0.50 | 0.85 | 0.30 | 0.75 |
| **Speckle Scale ($\sigma$)** | 0.00 | 0.10 | 0.22 | 0.08 | 0.20 |
| **Speckle Distribution** | N/A | Gamma | Rayleigh | Gamma | Gamma |
| **Transmission Loss Prob** | 0.00 | 0.30 | 0.60 | 0.20 | 0.50 |
| **Stripe Artifact Prob** | 0.00 | 0.20 | 0.50 | 0.10 | 0.45 |
| **Stripe Intensity ($A$)** | 0.00 | 0.08 | 0.18 | 0.05 | 0.15 |
| **Max Yaw Rotation ($\theta$)**| $0.0^\circ$ | $\pm 4.0^\circ$ | $\pm 6.0^\circ$ | $\pm 3.0^\circ$ | $\pm 5.0^\circ$ |
| **Horizontal Swath Flip** | 0.00 | 0.50 | 0.50 | 0.50 | 0.50 |
| **Vertical Range Flip** | **0.00 (Prohibited)** | **0.00 (Prohibited)** | **0.00 (Prohibited)** | **0.00 (Prohibited)** | **0.00 (Prohibited)** |

---

## 4. Bounding-Box Geometry Transformation & Verification

When spatial transforms (rotation, platform drift translation, swath reflection) are applied:
1. Corner coordinates $(x_1, y_1), (x_2, y_2), (x_3, y_3), (x_4, y_4)$ are transformed via affine matrix $M$.
2. The enclosing axis-aligned bounding box $[x_{\min}, y_{\min}, x_{\max}, y_{\max}]$ is recalculated.
3. Coordinates are clipped to image canvas boundaries $[0, W] \times [0, H]$.
4. Degenerate boxes ($W_{\text{box}} < 4\text{ px}$ or $H_{\text{box}} < 4\text{ px}$) are pruned to avoid corrupt training gradients.
5. Unit tests (`test_sonar_augmentor.py`) verify that box center coordinates, widths, and heights remain mathematically valid and strictly inside $[0.0, 1.0]$.
