"""
Integration & Invariant Test Suite for Project-Wide Sonar Image Improvement System.

Verifies:
1. Raw acoustic signal immutability (input arrays are never mutated).
2. Canonical output is strictly single-channel float32 [0.0, 1.0].
3. Dimensions (H, W) match raw input exactly across all 8 classical algorithms.
4. Pseudocolor colormaps are strictly presentation-only (RGB uint8).
5. EnhancementManager SHA256-based caching and auto-fallback.
6. Security / path traversal sanitization.
7. Production model checkpoint (sonar_yolov8_fls_trained.pt) SHA256 integrity.
"""

import hashlib
from pathlib import Path
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.api.main import create_app
from backend.enhancement.methods import apply_enhancement_method, ENHANCEMENT_METHODS
from backend.enhancement.colormap import apply_palette, get_available_palettes
from backend.enhancement.types import EnhancementMethod, PaletteType, ProfileName
from backend.enhancement.providers.manager import EnhancementManager
from backend.enhancement.providers.classical import ClassicalEnhancementProvider
from backend.enhancement.providers.learned import LearnedEnhancementProvider
from backend.enhancement.metric_definitions import compute_enl, compute_cnr, compute_epi

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PRODUCTION_CHECKPOINT = PROJECT_ROOT / "models" / "detection" / "sonar_yolov8_fls_trained.pt"
EXPECTED_SHA256 = "e1215c7e7f6e4f3722398bf93d975eb5013c49f78355d0d5f54ce982d495b3d7"


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def synthetic_sonar_frame():
    """Generates realistic synthetic FLS acoustic speckle frame [128, 256]."""
    np.random.seed(42)
    # Rayleigh distributed speckle noise
    noise = np.random.rayleigh(scale=0.15, size=(128, 256)).astype(np.float32)
    # Seabed gradient
    gradient = np.linspace(0.1, 0.4, 128)[:, None] * np.ones((1, 256))
    img = np.clip(noise + gradient, 0.0, 1.0).astype(np.float32)
    # Add a target highlight and shadow
    img[50:65, 100:120] = 0.95  # acoustic highlight
    img[50:65, 121:150] = 0.02  # acoustic shadow
    return img


class TestSonarEnhancementInvariants:
    """Scientific integrity and non-destructive processing tests."""

    def test_production_model_sha256_unmodified(self):
        """CRITICAL INVARIANT: The production model weights must remain 100% untouched."""
        assert PRODUCTION_CHECKPOINT.exists(), f"Missing production checkpoint at {PRODUCTION_CHECKPOINT}"
        h = hashlib.sha256()
        with open(PRODUCTION_CHECKPOINT, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_sha = h.hexdigest().lower()
        assert actual_sha == EXPECTED_SHA256, f"Production checkpoint modified! Expected {EXPECTED_SHA256}, got {actual_sha}"

    def test_raw_signal_immutability(self, synthetic_sonar_frame):
        """Input acoustic array must NEVER be modified in place by any enhancement method."""
        original_copy = synthetic_sonar_frame.copy()
        manager = EnhancementManager.get_instance()

        for method in EnhancementMethod:
            res, _ = manager.improve_sonar_image(synthetic_sonar_frame, method=method.value)
            # Assert input frame remains bit-for-bit identical
            assert np.array_equal(synthetic_sonar_frame, original_copy), f"Method {method.value} mutated input array!"

    def test_canonical_float32_contract(self, synthetic_sonar_frame):
        """Canonical enhanced output must be 2D float32 strictly bounded in [0.0, 1.0]."""
        manager = EnhancementManager.get_instance()

        for method in EnhancementMethod:
            res, _ = manager.improve_sonar_image(synthetic_sonar_frame, method=method.value)
            out = res.canonical_image

            assert isinstance(out, np.ndarray)
            assert out.dtype == np.float32, f"Method {method.value} did not return float32 (got {out.dtype})"
            assert out.ndim == 2, f"Method {method.value} returned {out.ndim}D array instead of 2D"
            assert out.shape == synthetic_sonar_frame.shape, f"Method {method.value} altered dimensions"
            assert np.all(out >= 0.0) and np.all(out <= 1.0), f"Method {method.value} produced values out of [0, 1]"
            assert not np.isnan(out).any(), f"Method {method.value} produced NaNs"
            assert not np.isinf(out).any(), f"Method {method.value} produced Infs"

    def test_pseudocolor_presentation_decoupling(self, synthetic_sonar_frame):
        """Colormap palettes must produce uint8 BGR [H, W, 3] presentation layers only."""
        palettes = get_available_palettes()
        assert len(palettes) >= 4

        for pal_info in palettes:
            pal_enum = PaletteType(pal_info["id"])
            colored = apply_palette(synthetic_sonar_frame, palette=pal_enum)

            assert colored.dtype == np.uint8
            assert colored.ndim == 3
            assert colored.shape[2] == 3
            assert colored.shape[:2] == synthetic_sonar_frame.shape

    def test_enhancement_manager_caching(self, synthetic_sonar_frame):
        """Identical requests must hit the bounded LRU/SHA256 cache."""
        manager = EnhancementManager.get_instance()
        res1, tele1 = manager.improve_sonar_image(synthetic_sonar_frame, method="clahe_enhance", palette="amber")
        res2, tele2 = manager.improve_sonar_image(synthetic_sonar_frame, method="clahe_enhance", palette="amber")

        assert tele2.get("cache_hit") is True
        assert np.array_equal(res1.canonical_image, res2.canonical_image)

    def test_learned_provider_fallback(self, synthetic_sonar_frame):
        """When learned weights are not installed, learned provider reports UNAVAILABLE and falls back."""
        learned = LearnedEnhancementProvider()
        status = learned.validation_status
        assert status in ["UNAVAILABLE", "EXPERIMENTAL"]

        manager = EnhancementManager.get_instance()
        # Request learned method
        res, tele = manager.improve_sonar_image(synthetic_sonar_frame, method="learned")
        # Should gracefully fall back to balanced classical pipeline without error
        assert res.canonical_image is not None
        assert res.canonical_image.shape == synthetic_sonar_frame.shape
        assert tele.get("engine_status") == "CLASSICAL_FALLBACK" or tele.get("provider_used") == "learned"

    def test_identity_baseline_epi_equals_one(self, synthetic_sonar_frame):
        """EPI for identity method against raw must be exactly 1.000."""
        epi = compute_epi(synthetic_sonar_frame, synthetic_sonar_frame)
        assert epi.status.value == "VALID"
        assert abs(epi.value - 1.000) < 1e-4

    def test_security_path_traversal_rejection(self, test_client):
        """API endpoints must sanitize and reject path traversal attacks."""
        bad_payload = {
            "dataset_version": "v3",
            "split": "val",
            "image_name": "../../../etc/passwd",
            "method": "auto",
        }
        res = test_client.post("/api/v1/enhancement/process", json=bad_payload)
        # Should return 404 or 400, never leak system files
        assert res.status_code in [400, 404]

    def test_api_providers_endpoint(self, test_client):
        """GET /enhancement/providers returns valid registry status."""
        res = test_client.get("/api/v1/enhancement/providers")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "providers" in data
        assert len(data["providers"]) >= 2
