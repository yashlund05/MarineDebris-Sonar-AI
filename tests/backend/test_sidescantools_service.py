"""
Unit and Invariant Tests for SidescanTools Sonar Enhancement Service.
Smart India Hackathon 2026 — PS26057.
"""

import hashlib
import numpy as np
import pytest
import cv2

from backend.services.sonar_enhancement import (
    SonarEnhancementConfig,
    SonarEnhancementPipeline,
    SonarEnhancementProcessor,
    ColormapName,
    DetectionInputMode,
    compute_acoustic_quality_metrics,
)
from backend.services.sonar_enhancement.sidescan_adapter import SidescanToolsAdapter
from backend.services.sonar_enhancement.validators import (
    validate_input_representation,
    RepresentationType,
)
from backend.services.sonar_enhancement.image_export import (
    apply_sonar_colormap,
    encode_to_png_bytes,
    encode_to_base64_data_url,
)
from backend.services.sonar_enhancement.quality_metrics import (
    compute_comparative_quality_metrics,
    compute_brenner_gradient,
    compute_tenengrad,
)


@pytest.fixture
def synthetic_sonar_frame():
    """Generates a synthetic 256x256 noisy sonar image with periodic acquisition stripes."""
    np.random.seed(101)
    base = np.linspace(20, 180, 256).reshape(1, -1) + np.zeros((256, 1))
    speckle = np.random.exponential(scale=15.0, size=(256, 256))
    stripes = (np.sin(np.linspace(0, 32 * np.pi, 256)) * 20.0).reshape(-1, 1)
    frame = (base + speckle + stripes).clip(0, 255).astype(np.uint8)
    return frame


@pytest.fixture
def synthetic_sonar_png_bytes(synthetic_sonar_frame):
    success, buf = cv2.imencode(".png", synthetic_sonar_frame)
    assert success
    return buf.tobytes()


class TestSidescanToolsAdapter:
    """Tests core radiometric algorithms adapted from sonoware/sidescantools."""

    def test_convert_to_dB_positive_values(self):
        arr = np.array([[1.0, 10.0], [100.0, 1000.0]], dtype=np.float32)
        arr_db = SidescanToolsAdapter.convert_to_dB(arr)
        # 20 * log10(10) = 20, 20 * log10(100) = 40, 20 * log10(1000) = 60
        assert np.isclose(arr_db[0, 0], 0.0, atol=1e-3)
        assert np.isclose(arr_db[0, 1], 20.0, atol=1e-3)
        assert np.isclose(arr_db[1, 0], 40.0, atol=1e-3)
        assert np.isclose(arr_db[1, 1], 60.0, atol=1e-3)

    def test_convert_to_dB_handles_zeros_and_negatives(self):
        arr = np.array([[0.0, -5.0], [10.0, 100.0]], dtype=np.float32)
        arr_db = SidescanToolsAdapter.convert_to_dB(arr)
        assert not np.any(np.isnan(arr_db))
        assert not np.any(np.isinf(arr_db))

    def test_hist_equalization(self, synthetic_sonar_frame):
        arr = synthetic_sonar_frame.astype(np.float32)
        eq = SidescanToolsAdapter.hist_equalization(arr, clip_limit=0.01)
        assert eq.shape == arr.shape
        assert 0.0 <= np.min(eq) <= 1.0
        assert 0.0 <= np.max(eq) <= 1.0

    def test_build_pie_H_mask_properties(self):
        H = SidescanToolsAdapter.build_pie_H(M=128, N=128, width_end=0.05)
        assert H.shape == (128, 128)
        assert np.all(H >= 0.0) and np.all(H <= 1.0)
        # Verify vertical symmetry (SidescanTools pie slice symmetry)
        assert np.allclose(H[64:], np.flipud(H[:64]))

    def test_apply_pie_slice_filter_shape_preservation(self, synthetic_sonar_frame):
        filtered, applied = SidescanToolsAdapter.apply_pie_slice_filter(synthetic_sonar_frame)
        assert filtered.shape == synthetic_sonar_frame.shape
        assert not np.any(np.isnan(filtered))

    def test_homomorphic_sharpening_filter(self, synthetic_sonar_frame):
        sharpened, applied = SidescanToolsAdapter.apply_sharpening_filter(
            synthetic_sonar_frame, gamma_h=2.0, gamma_l=0.5, const_c=1.5
        )
        assert applied is True
        assert sharpened.shape == synthetic_sonar_frame.shape
        assert not np.any(np.isnan(sharpened))

    def test_normalize_to_uint8(self):
        arr = np.array([[-10.0, 0.0], [50.0, 100.0]], dtype=np.float32)
        u8 = SidescanToolsAdapter.normalize_to_uint8(arr)
        assert u8.dtype == np.uint8
        assert u8.min() == 0
        assert u8.max() == 255


class TestInputRepresentationValidator:
    """Verifies gating to prevent double dB conversion on rendered PNG images."""

    def test_detects_rendered_grayscale_png(self, synthetic_sonar_frame):
        rep = validate_input_representation(synthetic_sonar_frame, {"filename": "test.png"})
        assert rep.representation_type == RepresentationType.RENDERED_GRAYSCALE
        assert rep.db_conversion_applicable is False
        assert "distort dynamic range" in rep.audit_note

    def test_detects_raw_acoustic_linear_telemetry(self):
        raw_linear = np.random.uniform(5.0, 500.0, size=(100, 100)).astype(np.float32)
        rep = validate_input_representation(raw_linear, {"filename": "survey.xtf", "file_type": "xtf"})
        assert rep.representation_type == RepresentationType.RAW_ACOUSTIC_LINEAR
        assert rep.db_conversion_applicable is True


class TestQualityMetrics:
    """Tests non-reference acoustic quality metrics."""

    def test_metrics_on_flat_and_noisy_images(self):
        flat = np.full((100, 100), 128, dtype=np.uint8)
        noisy = np.random.randint(0, 256, (100, 100), dtype=np.uint8)

        m_flat = compute_acoustic_quality_metrics(flat)
        m_noisy = compute_acoustic_quality_metrics(noisy)

        assert m_flat["rms_contrast"] == 0.0
        assert m_flat["entropy"] == 0.0
        assert m_noisy["rms_contrast"] > 0.1
        assert m_noisy["entropy"] > 6.0

    def test_comparative_metrics_calculates_deltas(self, synthetic_sonar_frame):
        enhanced = cv2.equalizeHist(synthetic_sonar_frame)
        comp = compute_comparative_quality_metrics(synthetic_sonar_frame, enhanced)
        assert "raw" in comp
        assert "enhanced" in comp
        assert "delta" in comp
        assert "contrast_gain" in comp["delta"]
        assert "sharpness_ratio" in comp["delta"]


class TestSonarEnhancementPipeline:
    """Tests pipeline invariants, raw preservation, and outputs."""

    def test_pipeline_raw_immutability(self, synthetic_sonar_frame):
        raw_copy = synthetic_sonar_frame.copy()
        raw_hash_before = hashlib.sha256(raw_copy.tobytes()).hexdigest()

        pipeline = SonarEnhancementPipeline()
        res = pipeline.run(raw_copy)

        raw_hash_after = hashlib.sha256(raw_copy.tobytes()).hexdigest()
        assert raw_hash_before == raw_hash_after
        assert np.array_equal(res.raw_gray_u8, raw_copy)

    def test_conservative_defaults(self):
        cfg = SonarEnhancementConfig()
        assert cfg.sharpening is False
        assert cfg.gain_normalization is False
        assert cfg.clahe is True
        assert cfg.stripe_noise_filter is True

    def test_pipeline_audit_trail_populated(self, synthetic_sonar_frame):
        pipeline = SonarEnhancementPipeline()
        res = pipeline.run(synthetic_sonar_frame)
        assert len(res.audit_trail) >= 4
        assert any("Input analyzed" in step for step in res.audit_trail)
        assert any("CLAHE" in step for step in res.audit_trail)


class TestSonarEnhancementProcessor:
    """Tests processor caching, fast recoloring, and ML isolation."""

    def test_processor_caching(self, synthetic_sonar_png_bytes):
        processor = SonarEnhancementProcessor.get_instance()
        cfg = SonarEnhancementConfig(colormap="amber")

        res1 = processor.process_image_bytes(synthetic_sonar_png_bytes, config=cfg)
        assert res1["cache_hit"] is False

        res2 = processor.process_image_bytes(synthetic_sonar_png_bytes, config=cfg)
        assert res2["cache_hit"] is True
        assert res1["cache_key"] == res2["cache_key"]

    def test_fast_recolor_cached_frame(self, synthetic_sonar_png_bytes):
        processor = SonarEnhancementProcessor.get_instance()
        res = processor.process_image_bytes(synthetic_sonar_png_bytes)
        recolor = processor.render_colormap_fast(res["cache_key"], "viridis")
        assert recolor["success"] is True
        assert recolor["colormap"] == "viridis"
        assert recolor["recolor_time_ms"] < 50.0

    def test_strict_ml_isolation_prohibits_pseudocolor(self, synthetic_sonar_frame):
        processor = SonarEnhancementProcessor.get_instance()
        cfg = SonarEnhancementConfig()
        # Forcibly test violation
        cfg.detection_input_mode = "pseudo_color"
        with pytest.raises(ValueError, match="Attempted to run detection on pseudo-color image"):
            processor._execute_detection(
                synthetic_sonar_frame, synthetic_sonar_frame, cfg, detector=None, conf_threshold=0.25
            )
