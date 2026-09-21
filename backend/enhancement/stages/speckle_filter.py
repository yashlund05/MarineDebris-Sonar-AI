"""
Sonar-specific speckle denoising stage.

Implements Requirement R11:
- Lee multiplicative speckle model filter
- Frost exponentially damped adaptive filter
- SRAD (Speckle Reducing Anisotropic Diffusion)
- Bilateral edge-preserving smoother
- Conservative parameterization prioritizing small target and shadow boundary retention.
"""

from __future__ import annotations

from typing import Tuple, Dict, Any, Optional
import numpy as np
import cv2
from scipy.ndimage import uniform_filter

from backend.enhancement.pipeline_base import (
    SonarEnhancementStage,
    SonarEnhancementContext,
)


def lee_filter(image: np.ndarray, window_size: int = 5, damping_factor: float = 1.0) -> np.ndarray:
    """
    Lee Speckle Filter based on multiplicative noise model:
    I(x,y) = R(x,y) * u(x,y), where u has mean 1 and variance sigma_u^2.
    R_hat = mean + W * (I - mean), where W = var / (var + sigma_u^2 * mean^2)
    """
    img = image.astype(np.float32)
    k = max(3, window_size if window_size % 2 == 1 else window_size + 1)

    mean = uniform_filter(img, size=k)
    mean_sq = uniform_filter(img ** 2, size=k)
    variance = np.maximum(0.0, mean_sq - mean ** 2)

    # Estimate noise variance from homogeneous regions (lower 20th percentile of variance)
    pos_var = variance[variance > 1e-7]
    sigma_u_sq = float(np.percentile(pos_var, 15)) if pos_var.size > 0 else 0.04

    # Weighting coefficient
    denom = variance + (sigma_u_sq * (mean ** 2)) + 1e-7
    weight = np.clip(variance / denom, 0.0, 1.0) ** damping_factor

    filtered = mean + weight * (img - mean)
    return np.clip(filtered, 0.0, 1.0).astype(np.float32)


def frost_filter(image: np.ndarray, window_size: int = 5, damping_factor: float = 2.0) -> np.ndarray:
    """
    Frost Filter:
    Exponentially damped filter where weights decrease with distance from center
    and local coefficient of variation (sigma/mu).
    """
    img = image.astype(np.float32)
    k = max(3, window_size if window_size % 2 == 1 else window_size + 1)
    radius = k // 2

    mean = uniform_filter(img, size=k)
    mean_sq = uniform_filter(img ** 2, size=k)
    variance = np.maximum(0.0, mean_sq - mean ** 2)

    ci = np.sqrt(variance) / (mean + 1e-6)  # Local coefficient of variation

    # Generate spatial distance matrix from kernel center
    y, x = np.ogrid[-radius : radius + 1, -radius : radius + 1]
    dist_sq = x ** 2 + y ** 2

    out = np.zeros_like(img)
    padded = np.pad(img, radius, mode="reflect")
    ci_padded = np.pad(ci, radius, mode="reflect")

    h, w = img.shape
    # Fast vectorized approximation using separable box filters for efficiency
    for r in range(k):
        for c in range(k):
            d = np.sqrt((r - radius) ** 2 + (c - radius) ** 2)
            w_kernel = np.exp(-damping_factor * ci * d)
            patch = padded[r : r + h, c : c + w]
            out += w_kernel * patch

    # Normalize by sum of weights
    weight_sum = np.zeros_like(img)
    for r in range(k):
        for c in range(k):
            d = np.sqrt((r - radius) ** 2 + (c - radius) ** 2)
            weight_sum += np.exp(-damping_factor * ci * d)

    out /= (weight_sum + 1e-7)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def srad_filter(
    image: np.ndarray,
    n_iter: int = 15,
    dt: float = 0.05,
    q0_squared: float = 0.1,
) -> np.ndarray:
    """
    Speckle Reducing Anisotropic Diffusion (SRAD).
    PDE formulation preserving sharp target boundaries while diffusing speckle noise.
    """
    u = image.astype(np.float32).copy()
    h, w = u.shape

    for _ in range(n_iter):
        # Directional differences (North, South, East, West)
        dn = np.zeros_like(u)
        ds = np.zeros_like(u)
        de = np.zeros_like(u)
        dw = np.zeros_like(u)

        dn[:-1, :] = u[1:, :] - u[:-1, :]
        ds[1:, :] = u[:-1, :] - u[1:, :]
        de[:, :-1] = u[:, 1:] - u[:, :-1]
        dw[:, 1:] = u[:, :-1] - u[:, 1:]

        # Normalized gradient and Laplacian
        grad_sq = (dn ** 2 + ds ** 2 + de ** 2 + dw ** 2) / ((u + 1e-6) ** 2)
        laplacian = (dn + ds + de + dw) / (u + 1e-6)

        # Instantaneous coefficient of variation q(x,y;t)
        num = 0.5 * grad_sq - (1.0 / 16.0) * (laplacian ** 2)
        den = (1.0 + (1.0 / 4.0) * laplacian) ** 2
        q_sq = np.maximum(0.0, num / (den + 1e-6))

        # Diffusion coefficient c(q)
        c = 1.0 / (1.0 + (q_sq - q0_squared) / (q0_squared * (1.0 + q0_squared) + 1e-6))
        c = np.clip(c, 0.0, 1.0)

        # Divergence of (c * grad)
        flux_n = c * dn
        flux_s = c * ds
        flux_e = c * de
        flux_w = c * dw

        div = np.zeros_like(u)
        div[1:, :] += flux_n[:-1, :]
        div[:-1, :] += flux_s[1:, :]
        div[:, 1:] += flux_e[:, :-1]
        div[:, :-1] += flux_w[:, 1:]

        u += dt * div
        u = np.clip(u, 0.0, 1.0)

    return u.astype(np.float32)


class SpeckleDenoisingStage(SonarEnhancementStage):
    """Configurable sonar speckle filtering stage."""

    def __init__(
        self,
        method: str = "lee",
        window_size: int = 5,
        srad_iterations: int = 12,
        damping_factor: float = 1.0,
        name: str = "SpeckleDenoisingStage",
    ):
        super().__init__(name=name, is_ai_safe_default=True)
        self.method = method.lower()
        self.window_size = window_size
        self.srad_iterations = srad_iterations
        self.damping_factor = damping_factor

    def validate_input(self, image: np.ndarray, context: SonarEnhancementContext) -> bool:
        return image is not None and image.ndim == 2 and image.size > 0

    def process(
        self, image: np.ndarray, context: SonarEnhancementContext
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        img = image.copy()

        if self.method == "lee":
            denoised = lee_filter(img, window_size=self.window_size, damping_factor=self.damping_factor)
        elif self.method == "frost":
            denoised = frost_filter(img, window_size=self.window_size, damping_factor=self.damping_factor)
        elif self.method == "srad":
            denoised = srad_filter(img, n_iter=self.srad_iterations)
        elif self.method == "bilateral":
            img_u8 = (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)
            filtered_u8 = cv2.bilateralFilter(img_u8, d=self.window_size, sigmaColor=25, sigmaSpace=3)
            denoised = (filtered_u8.astype(np.float32) / 255.0)
        elif self.method == "median":
            k = max(3, self.window_size if self.window_size % 2 == 1 else self.window_size + 1)
            img_u8 = (np.clip(img, 0.0, 1.0) * 255.0).astype(np.uint8)
            denoised = (cv2.medianBlur(img_u8, k).astype(np.float32) / 255.0)
        else:
            denoised = img

        diff = np.abs(denoised - img)
        metrics = {
            "method": self.method,
            "window_size": self.window_size,
            "mean_delta": float(np.mean(diff)),
            "max_delta": float(np.max(diff)),
            "modified_pixel_ratio": float(np.sum(diff > 0.005) / img.size),
        }
        return denoised, metrics
