"""
Unit and Integration Tests for Intelligent Sonar Image Enhancement Engine.

Validates:
1. Mathematical invariants of all 8 classical enhancement algorithms
2. Explicit metric formulas (ENL on homogeneous ROI, deterministic CNR, EPI identity property)
3. Zero metric fabrication and graceful failure behavior
4. Display pseudocolor LUT isolation from canonical grayscale
5. Profile hypotheses and benchmark execution
"""

import pytest
import numpy as np
from backend.enhancement.types import (
    EnhancementMethod,
    PaletteType,
    ProfileName,
    MetricStatus,
)
from backend.enhancement.methods import (
    identity,
    percentile_normalize,
    gamma_correct,
    clahe_enhance,
    median_clahe,
    bilateral_clahe,
    unsharp_clahe,
    log_bilateral_clahe,
    apply_enhancement_method,
    ENHANCEMENT_METHODS,
)
from backend.enhancement.metric_definitions import (
    compute_enl,
    compute_cnr,
    compute_epi,
    extract_homogeneous_background_roi,
    derive_target_and_background_rois,
)
from backend.enhancement.colormap import (
    create_sonar_amber_lut,
    create_thermal_lut,
    apply_palette,
    get_available_palettes,
)
from backend.enhancement.profiles import (
    list_profiles,
    get_profile_info,
    apply_profile,
    PROFILE_REGISTRY,
)
from backend.enhancement.benchmark import EnhancementBenchmarkRunner


# Fixture for a synthetic sonar patch with target and background
@pytest.fixture
def synthetic_sonar_patch():
    np.random.seed(42)
    # 256x256 image with uniform seabed clutter (mean=0.3, std=0.05)
    img = np.random.normal(loc=0.3, scale=0.05, size=(256, 256)).astype(np.float32)
    img = np.clip(img, 0.05, 0.95)
    # Inject a bright target in center (row 100-140, col 100-140) with mean 0.8
    img[100:140, 100:140] = np.random.normal(loc=0.8, scale=0.05, size=(40, 40))
    # Inject acoustic shadow behind it (row 140-180, col 100-140) with mean 0.05
    img[140:180, 100:140] = np.random.normal(loc=0.05, scale=0.01, size=(40, 40))
    return np.clip(img, 0.0, 1.0)


# =====================================================================
# 1. Classical Enhancement Methods Tests
# =====================================================================

def test_identity_baseline(synthetic_sonar_patch):
    res = identity(synthetic_sonar_patch)
    assert res.method == EnhancementMethod.IDENTITY
    assert res.canonical_image.dtype == np.float32
    assert np.allclose(res.canonical_image, synthetic_sonar_patch)


def test_percentile_normalize_range(synthetic_sonar_patch):
    res = percentile_normalize(synthetic_sonar_patch, p_low=5.0, p_high=95.0)
    assert res.canonical_image.dtype == np.float32
    assert np.min(res.canonical_image) >= 0.0
    assert np.max(res.canonical_image) <= 1.0


def test_gamma_correct_behavior(synthetic_sonar_patch):
    res_bright = gamma_correct(synthetic_sonar_patch, gamma=0.5)
    res_dark = gamma_correct(synthetic_sonar_patch, gamma=2.0)
    # Brightened should have higher mean than raw, darkened should have lower
    raw_mean = np.mean(synthetic_sonar_patch)
    assert np.mean(res_bright.canonical_image) > raw_mean
    assert np.mean(res_dark.canonical_image) < raw_mean


def test_clahe_output_spec(synthetic_sonar_patch):
    res = clahe_enhance(synthetic_sonar_patch, clip_limit=2.5)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.canonical_image.dtype == np.float32
    assert np.min(res.canonical_image) >= 0.0
    assert np.max(res.canonical_image) <= 1.0


def test_median_clahe_output_spec(synthetic_sonar_patch):
    res = median_clahe(synthetic_sonar_patch, kernel_size=3, clip_limit=2.0)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.canonical_image.dtype == np.float32


def test_bilateral_clahe_output_spec(synthetic_sonar_patch):
    res = bilateral_clahe(synthetic_sonar_patch, d=5, sigma_color=0.1, clip_limit=1.8)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.canonical_image.dtype == np.float32


def test_unsharp_clahe_output_spec(synthetic_sonar_patch):
    res = unsharp_clahe(synthetic_sonar_patch, amount=0.7, clip_limit=2.0)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.canonical_image.dtype == np.float32


def test_log_bilateral_clahe_output_spec(synthetic_sonar_patch):
    res = log_bilateral_clahe(synthetic_sonar_patch)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.canonical_image.dtype == np.float32
    assert not np.isnan(res.canonical_image).any()
    assert not np.isinf(res.canonical_image).any()


def test_all_methods_empty_image():
    empty = np.zeros((0, 0), dtype=np.float32)
    for m_enum, fn in ENHANCEMENT_METHODS.items():
        res = fn(empty)
        assert res.canonical_image.size == 0


def test_all_methods_constant_image():
    const_img = np.full((64, 64), 0.5, dtype=np.float32)
    for m_enum, fn in ENHANCEMENT_METHODS.items():
        res = fn(const_img)
        assert res.canonical_image.shape == (64, 64)
        assert not np.isnan(res.canonical_image).any()


# =====================================================================
# 2. Metric Foundations & Verification Tests
# =====================================================================

def test_epi_identity_property(synthetic_sonar_patch):
    """Mathematical requirement: EPI(I, I) must equal exactly 1.0000."""
    res = compute_epi(synthetic_sonar_patch, synthetic_sonar_patch)
    assert res.status == MetricStatus.VALID
    assert res.value == 1.0000


def test_epi_shape_mismatch():
    img1 = np.zeros((64, 64), dtype=np.float32)
    img2 = np.zeros((64, 32), dtype=np.float32)
    res = compute_epi(img1, img2)
    assert res.status == MetricStatus.INVALID
    assert res.value is None


def test_enl_on_homogeneous_roi(synthetic_sonar_patch):
    # Homogeneous seabed patch in top-left (no target)
    patch = synthetic_sonar_patch[10:50, 10:50]
    res = compute_enl(synthetic_sonar_patch, roi=patch)
    assert res.status == MetricStatus.VALID
    assert res.value is not None
    assert res.value > 1.0  # Synthetic seabed has mean ~0.3, std ~0.05 -> ENL ~ 36


def test_enl_degenerate_handling():
    # Pure zero image (unmeasurable looks)
    zeros = np.zeros((64, 64), dtype=np.float32)
    res = compute_enl(zeros)
    assert res.status == MetricStatus.NOT_MEASURABLE
    assert res.value is None


def test_derive_target_and_background_rois(synthetic_sonar_patch):
    # Target in synthetic_sonar_patch is at row 100-140, col 100-140 (center ~120, 120, size 40, 40)
    # Normalized: cx = 120/256 = 0.46875, cy = 0.46875, w = 40/256 = 0.15625, h = 0.15625
    bbox = (0.46875, 0.46875, 0.15625, 0.15625)
    tgt, bg, status, reason = derive_target_and_background_rois(synthetic_sonar_patch, bbox)
    assert status == MetricStatus.VALID
    assert tgt.size >= 16
    assert bg.size >= 16
    # Target mean should be significantly higher than background ring
    assert np.mean(tgt) > np.mean(bg)


def test_cnr_computation(synthetic_sonar_patch):
    bbox = (0.46875, 0.46875, 0.15625, 0.15625)
    res = compute_cnr(synthetic_sonar_patch, bbox_xywh_norm=bbox)
    assert res.status == MetricStatus.VALID
    assert res.value is not None
    assert res.value > 2.0  # Significant target-to-background contrast


def test_cnr_invalid_box(synthetic_sonar_patch):
    # Degenerate 1-pixel box
    bbox = (0.5, 0.5, 0.001, 0.001)
    res = compute_cnr(synthetic_sonar_patch, bbox_xywh_norm=bbox)
    assert res.status == MetricStatus.NOT_MEASURABLE
    assert res.value is None


# =====================================================================
# 3. Colormaps & Display Separation Tests
# =====================================================================

def test_amber_lut_geometry():
    lut = create_sonar_amber_lut()
    assert lut.shape == (256, 1, 3)
    assert lut.dtype == np.uint8
    # Background shadow (index 0) must be black
    assert np.all(lut[0, 0] == [0, 0, 0])
    # Peak specular reflection (index 255) must have high red and green
    assert lut[255, 0, 2] > 200  # Red
    assert lut[255, 0, 1] > 200  # Green


def test_thermal_lut_monotonic_ordering():
    lut = create_thermal_lut()
    assert lut.shape == (256, 1, 3)
    # Red ramp should rise monotonically from 0
    red_values = lut[:, 0, 2]
    assert np.all(np.diff(red_values) >= 0)


def test_palette_application(synthetic_sonar_patch):
    display_bgr = apply_palette(synthetic_sonar_patch, PaletteType.AMBER)
    assert display_bgr.shape == (256, 256, 3)
    assert display_bgr.dtype == np.uint8


def test_display_palette_isolation(synthetic_sonar_patch):
    """Enforces programmatic rule: Colormaps are strictly 3-channel display images."""
    enh_res = bilateral_clahe(synthetic_sonar_patch)
    display_img = apply_palette(enh_res.canonical_image, PaletteType.AMBER)
    # Canonical output is single-channel float32
    assert enh_res.canonical_image.ndim == 2
    assert enh_res.canonical_image.dtype == np.float32
    # Display output is 3-channel uint8
    assert display_img.ndim == 3
    assert display_img.shape[2] == 3
    assert display_img.dtype == np.uint8


# =====================================================================
# 4. Profiles & Benchmark Integration Tests
# =====================================================================

def test_profile_registry_integrity():
    profiles = list_profiles()
    assert len(profiles) == 6  # RAW, MINIMAL, BALANCED, HUMAN_VISUAL, AI_SAFE, RESEARCH_CUSTOM
    for p in profiles:
        assert "hypothesis" in p
        assert "target_condition" in p
        assert "id" in p


def test_apply_profile(synthetic_sonar_patch):
    res = apply_profile(synthetic_sonar_patch, ProfileName.BALANCED)
    assert res.canonical_image.shape == synthetic_sonar_patch.shape
    assert res.execution_time_ms >= 0.0


def test_benchmark_smoke_execution():
    runner = EnhancementBenchmarkRunner()
    # Evaluate 2 methods on 2 frames of val split
    summary = runner.run_method_benchmark(
        methods=["identity", "clahe_enhance"],
        dataset_version="v3",
        split="val",
        sample_limit=2
    )
    assert "identity" in summary
    assert "clahe_enhance" in summary
    assert summary["identity"]["latency_mean_ms"] > 0.0
    assert summary["identity"]["epi_mean"] == 1.000

