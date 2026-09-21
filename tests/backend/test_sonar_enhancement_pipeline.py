"""
Unit and Integration Tests for Modular Sonar Enhancement Subsystem.

Tests:
1. Input inspection (FLS vs SSS, saturation, dynamic range, data types)
2. Signal domain conversions (amplitude/power dB, double-log protection)
3. Stripe noise notch filter stage (2D FFT, confidence gating)
4. Speckle denoising stage (Lee, Frost, SRAD, Bilateral)
5. Acoustic shadow preservation diagnostics (shadow retention, alerts)
6. Adaptive contrast stage (CLAHE, gamma, unsharp masking safety gating)
7. Learned denoiser adapters (SEGSID, WFC-BSN, LBD-Enhance surrogates)
8. End-to-end SonarEnhancementPipeline execution (AI-safe vs Human display)
9. Quality metrics evaluation (SSIM, Speckle Index, Edge Density, Modified Pixel Ratio)
10. Standard operational profiles (RAW, MINIMAL, BALANCED, HUMAN_VISUAL, AI_SAFE)
"""

import pytest
import numpy as np
import cv2

from backend.enhancement.pipeline_base import (
    Modality,
    SignalRepresentation,
    ProcessingMode,
    SonarEnhancementContext,
    SonarEnhancementPipeline,
    SonarEnhancementProvenance,
)
from backend.enhancement.inspection import inspect_sonar_input, SonarInspectionReport
from backend.enhancement.signal_domain import (
    amplitude_to_db,
    power_to_db,
    db_to_linear_power,
    safe_percentile_normalization,
    robust_dynamic_range_estimation,
)
from backend.enhancement.stages.stripe_filter import StripeNoiseNotchStage
from backend.enhancement.stages.speckle_filter import (
    SpeckleDenoisingStage,
    lee_filter,
    frost_filter,
    srad_filter,
)
from backend.enhancement.stages.shadow_diagnostics import AcousticShadowPreservationStage
from backend.enhancement.stages.contrast_stage import AdaptiveContrastStage
from backend.enhancement.adapters.learned_denoiser import (
    SEGSIDDenoiserAdapter,
    WFCBSNDenoiserAdapter,
    LBDEnhanceAdapter,
)
from backend.enhancement.quality_metrics import (
    compute_speckle_index,
    compute_entropy,
    compute_edge_density,
    compute_ssim_proxy,
    evaluate_enhancement_quality,
)
from backend.enhancement.profiles import (
    StandardProfile,
    build_pipeline_for_profile,
    list_profiles,
    get_profile_info,
)


@pytest.fixture
def synthetic_sonar_frame():
    """Generates a realistic 128x128 synthetic sonar patch with target and acoustic shadow."""
    np.random.seed(42)
    # Background seabed clutter
    frame = np.random.normal(loc=0.35, scale=0.06, size=(128, 128)).astype(np.float32)
    frame = np.clip(frame, 0.05, 0.95)
    # Specular target highlight (rows 40:60, cols 45:65)
    frame[40:60, 45:65] = np.random.normal(loc=0.85, scale=0.03, size=(20, 20))
    # Acoustic shadow behind target (rows 60:90, cols 45:65)
    frame[60:90, 45:65] = np.random.normal(loc=0.04, scale=0.01, size=(30, 20))
    return np.clip(frame, 0.0, 1.0)


# =====================================================================
# 1. Inspection Tests
# =====================================================================

def test_inspect_sonar_input_fls(synthetic_sonar_frame):
    report = inspect_sonar_input(synthetic_sonar_frame, metadata={"sonar_type": "ARIS_3000"})
    assert report.modality == Modality.FLS
    assert report.shape == [128, 128]
    assert report.saturated_pixel_ratio < 0.05
    assert report.min_value >= 0.0
    assert report.max_value <= 1.0
    assert report.detected_representation == SignalRepresentation.NORMALIZED_FLOAT


def test_inspect_sonar_input_sss():
    # Elongated side-scan geometry (e.g., 512 x 128)
    sss_patch = np.random.uniform(0.1, 0.9, size=(512, 128)).astype(np.float32)
    report = inspect_sonar_input(sss_patch)
    assert report.modality == Modality.SSS


def test_inspect_sonar_input_uint8():
    u8_img = np.random.randint(0, 255, size=(64, 64), dtype=np.uint8)
    report = inspect_sonar_input(u8_img)
    assert report.dtype == "uint8"
    assert report.detected_representation == SignalRepresentation.DISPLAY_GRAYSCALE


# =====================================================================
# 2. Signal Domain Conversions
# =====================================================================

def test_amplitude_and_power_to_db():
    linear_amp = np.array([0.01, 0.1, 1.0], dtype=np.float32)
    db_amp, audit = amplitude_to_db(linear_amp, ref=1.0)
    assert db_amp.shape == linear_amp.shape
    assert np.min(db_amp) >= 0.0
    assert np.max(db_amp) <= 1.0
    assert "formula" in audit

    db_pow, audit_pow = power_to_db(linear_amp, ref=1.0)
    assert db_pow.shape == linear_amp.shape
    assert np.min(db_pow) >= 0.0
    assert np.max(db_pow) <= 1.0


def test_db_to_linear_power():
    # Normalized [0, 1] mapped dB where 1.0 corresponds to 0 dB, 0.0 corresponds to -60 dB
    norm_db = np.array([0.0, 0.5, 1.0], dtype=np.float32)
    linear = db_to_linear_power(norm_db, ref=1.0, clip_min_db=-60.0, clip_max_db=0.0)
    assert linear[2] == pytest.approx(1.0, rel=1e-3)  # 0 dB -> power 1.0
    assert linear[0] == pytest.approx(1e-6, rel=1e-2)  # -60 dB -> power 1e-6


def test_safe_percentile_normalization(synthetic_sonar_frame):
    normed, audit = safe_percentile_normalization(synthetic_sonar_frame, p_low=1.0, p_high=99.0)
    assert normed.dtype == np.float32
    assert np.min(normed) >= 0.0
    assert np.max(normed) <= 1.0
    assert "v_low" in audit


# =====================================================================
# 3. Stripe Noise Notch Filter Stage
# =====================================================================

def test_stripe_notch_filter_synthetic_stripes(synthetic_sonar_frame):
    # Inject synthetic vertical stripe noise
    striped = synthetic_sonar_frame.copy()
    striped[:, ::8] += 0.25
    striped = np.clip(striped, 0.0, 1.0)

    stage = StripeNoiseNotchStage(confidence_threshold=0.20, notch_width=4)
    ctx = SonarEnhancementContext(
        artifact_id="test_stripe",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )

    out, stage_metrics = stage.process(striped, ctx)
    assert out.shape == striped.shape
    assert out.dtype == np.float32
    assert "stripe_confidence" in stage_metrics


# =====================================================================
# 4. Speckle Denoising Stage
# =====================================================================

def test_speckle_denoiser_lee(synthetic_sonar_frame):
    ctx = SonarEnhancementContext(
        artifact_id="test_lee",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )
    stage = SpeckleDenoisingStage(method="lee", window_size=5)
    out, stage_metrics = stage.process(synthetic_sonar_frame, ctx)
    assert out.shape == synthetic_sonar_frame.shape
    assert out.dtype == np.float32
    assert np.min(out) >= 0.0
    assert np.max(out) <= 1.0


def test_speckle_denoiser_srad(synthetic_sonar_frame):
    out = srad_filter(synthetic_sonar_frame, n_iter=2, q0_squared=0.1)
    assert out.shape == synthetic_sonar_frame.shape
    assert out.dtype == np.float32
    assert not np.isnan(out).any()


def test_speckle_denoiser_frost(synthetic_sonar_frame):
    # Test fast Frost filter on 32x32 subpatch
    subpatch = synthetic_sonar_frame[:32, :32]
    out = frost_filter(subpatch, window_size=3, damping_factor=1.0)
    assert out.shape == subpatch.shape
    assert out.dtype == np.float32


# =====================================================================
# 5. Acoustic Shadow Diagnostics
# =====================================================================

def test_acoustic_shadow_preservation(synthetic_sonar_frame):
    ctx = SonarEnhancementContext(
        artifact_id="test_shadow",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
        metadata={"raw_image": synthetic_sonar_frame},
    )
    stage = AcousticShadowPreservationStage(max_area_reduction_ratio=0.25)
    out, stage_metrics = stage.process(synthetic_sonar_frame, ctx)
    assert np.allclose(out, synthetic_sonar_frame)
    assert "area_retention_ratio" in stage_metrics
    assert stage_metrics["area_retention_ratio"] >= 0.80


# =====================================================================
# 6. Adaptive Contrast Stage
# =====================================================================

def test_adaptive_contrast_clahe(synthetic_sonar_frame):
    ctx = SonarEnhancementContext(
        artifact_id="test_contrast",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )
    stage = AdaptiveContrastStage(clip_limit=1.5, tile_grid_size=(8, 8), gamma=1.0)
    out, stage_metrics = stage.process(synthetic_sonar_frame, ctx)
    assert out.shape == synthetic_sonar_frame.shape
    assert out.dtype == np.float32
    assert np.min(out) >= 0.0
    assert np.max(out) <= 1.0


def test_adaptive_contrast_ai_safe_gating():
    ctx = SonarEnhancementContext(
        artifact_id="test_gate",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )
    # Aggressive unsharp masking should not be AI-safe
    aggressive_stage = AdaptiveContrastStage(clip_limit=3.0, unsharp_amount=0.8)
    assert aggressive_stage.is_ai_safe(ctx) is False

    # Moderate contrast should be AI-safe
    conservative_stage = AdaptiveContrastStage(clip_limit=1.5, unsharp_amount=0.1)
    assert conservative_stage.is_ai_safe(ctx) is True


# =====================================================================
# 7. Learned Denoiser Adapters
# =====================================================================

def test_learned_denoiser_adapters_surrogate(synthetic_sonar_frame):
    ctx = SonarEnhancementContext(
        artifact_id="test_learned",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.HUMAN_DISPLAY,
    )
    segsid = SEGSIDDenoiserAdapter()
    out1, _ = segsid.process(synthetic_sonar_frame, ctx)
    assert out1.shape == synthetic_sonar_frame.shape
    assert segsid.is_ai_safe(ctx) is False

    wfc_bsn = WFCBSNDenoiserAdapter()
    out2, _ = wfc_bsn.process(synthetic_sonar_frame, ctx)
    assert out2.shape == synthetic_sonar_frame.shape

    lbd = LBDEnhanceAdapter()
    out3, _ = lbd.process(synthetic_sonar_frame, ctx)
    assert out3.shape == synthetic_sonar_frame.shape


# =====================================================================
# 8. Pipeline Execution & AI-Safe Gating
# =====================================================================

def test_pipeline_ai_safe_execution(synthetic_sonar_frame):
    pipeline = SonarEnhancementPipeline(name="Test_AISafe_Pipeline")
    pipeline.add_stage(StripeNoiseNotchStage())
    pipeline.add_stage(SpeckleDenoisingStage(method="lee", window_size=5))
    pipeline.add_stage(AdaptiveContrastStage(clip_limit=1.5))
    # Add an unsafe stage
    unsafe_stage = AdaptiveContrastStage(clip_limit=4.0, unsharp_amount=0.9)
    pipeline.add_stage(unsafe_stage)

    ctx = SonarEnhancementContext(
        artifact_id="test_pipeline_run",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )

    result = pipeline.execute(synthetic_sonar_frame, ctx)
    assert result.canonical_image.shape == synthetic_sonar_frame.shape
    assert result.is_ai_safe is True
    # Unsafe stage must have been skipped in AI_SAFE mode
    assert any(unsafe_stage.name in s for s in result.skipped_stages)


def test_pipeline_human_display_execution(synthetic_sonar_frame):
    pipeline = build_pipeline_for_profile("HUMAN_VISUAL", mode=ProcessingMode.HUMAN_DISPLAY)
    ctx = SonarEnhancementContext(
        artifact_id="test_human_run",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.HUMAN_DISPLAY,
    )
    result = pipeline.execute(synthetic_sonar_frame, ctx)
    assert result.canonical_image.shape == synthetic_sonar_frame.shape
    assert len(result.applied_stages) >= 2


# =====================================================================
# 9. Quality Metrics Comprehensive Evaluation
# =====================================================================

def test_evaluate_enhancement_quality(synthetic_sonar_frame):
    # Enhance slightly with CLAHE
    ctx = SonarEnhancementContext(
        artifact_id="test_metrics",
        modality=Modality.FLS,
        representation=SignalRepresentation.NORMALIZED_FLOAT,
        mode=ProcessingMode.AI_SAFE,
    )
    stage = AdaptiveContrastStage(clip_limit=1.5)
    enhanced, _ = stage.process(synthetic_sonar_frame, ctx)

    metrics = evaluate_enhancement_quality(synthetic_sonar_frame, enhanced)
    assert "ssim" in metrics
    assert metrics["ssim"] > 0.75  # High structural similarity
    assert "speckle_index" in metrics
    assert "edge_density" in metrics
    assert "modified_pixel_ratio" in metrics
    assert metrics["modified_pixel_ratio"] > 0.0


# =====================================================================
# 10. Operational Profiles Factory
# =====================================================================

def test_standard_profiles_factory():
    for prof in StandardProfile:
        pipeline = build_pipeline_for_profile(prof.value)
        assert isinstance(pipeline, SonarEnhancementPipeline)

    profiles = list_profiles()
    assert len(profiles) == 6
    profile_names = [p["id"] for p in profiles]
    assert "RAW" in profile_names
    assert "MINIMAL" in profile_names
    assert "BALANCED" in profile_names
    assert "HUMAN_VISUAL" in profile_names
    assert "AI_SAFE" in profile_names
    assert "RESEARCH_CUSTOM" in profile_names
