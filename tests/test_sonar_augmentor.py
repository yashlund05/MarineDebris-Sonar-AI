"""
Tests for SonarAcousticAugmentor: validates acoustic physics constraints,
multiplicative speckle, range transmission loss, stripe artifacts, and bbox transformations.
"""

import pytest
import numpy as np

from backend.ml.augmentation.sonar_augmentor import (
    SonarAcousticAugmentor,
    SonarAugmentationMode,
    AugmentationConfig,
)


def test_vertical_flip_prohibition():
    """Asserts that vertical flipping raises ValueError due to grazing-angle physics."""
    with pytest.raises(ValueError, match="CRITICAL ACOUSTIC PHYSICS VIOLATION"):
        _ = SonarAcousticAugmentor(AugmentationConfig(flipud_prob=0.5))


def test_multiplicative_speckle_bounds():
    """Asserts that speckle noise preserves pixel value bounds without producing NaN/Inf."""
    augmentor = SonarAcousticAugmentor.from_policy(SonarAugmentationMode.NOISE_ROBUST, seed=42)
    img = np.random.randint(50, 200, (640, 640, 3), dtype=np.uint8)

    noisy = augmentor.apply_multiplicative_speckle(img)
    assert noisy.shape == img.shape
    assert noisy.dtype == np.uint8
    assert not np.isnan(noisy).any()
    assert not np.isinf(noisy).any()
    assert noisy.min() >= 0
    assert noisy.max() <= 255


def test_transmission_loss_range_profile():
    """Asserts that range transmission loss attenuates far-range intensity more than near-range."""
    augmentor = SonarAcousticAugmentor.from_policy(SonarAugmentationMode.CONSERVATIVE_SONAR, seed=42)
    # Uniform white canvas
    img = np.full((640, 640, 3), 200, dtype=np.uint8)

    attenuated = augmentor.apply_transmission_loss(img)
    near_range_mean = np.mean(attenuated[:50, :])
    far_range_mean = np.mean(attenuated[-50:, :])

    # Far range must have lower mean intensity due to acoustic absorption
    assert far_range_mean < near_range_mean


def test_stripe_artifacts_preserves_dimensions():
    """Asserts that stripe artifact simulation preserves dimensions and types."""
    augmentor = SonarAcousticAugmentor.from_policy(SonarAugmentationMode.NOISE_ROBUST, seed=42)
    img = np.random.randint(20, 220, (640, 640), dtype=np.uint8)

    striped = augmentor.apply_stripe_artifacts(img)
    assert striped.shape == img.shape
    assert striped.dtype == np.uint8
    assert not np.isnan(striped).any()


def test_bbox_transformation_invariants():
    """Asserts that bounding box coordinates remain strictly within [0.0, 1.0] and valid."""
    augmentor = SonarAcousticAugmentor.from_policy(SonarAugmentationMode.CONSERVATIVE_SONAR, seed=42)
    img = np.zeros((640, 640, 3), dtype=np.uint8)
    bboxes = [
        [1, 0.5, 0.5, 0.2, 0.2],    # Centered target
        [4, 0.2, 0.3, 0.1, 0.08],   # Off-center target
        [1, 0.8, 0.7, 0.15, 0.12],  # Far-range target
    ]

    for _ in range(10):
        aug_img, aug_boxes = augmentor.augment(img, bboxes)
        assert aug_img.shape == img.shape
        for b in aug_boxes:
            cid, xc, yc, bw, bh = b
            assert 0 <= cid <= 4
            assert 0.0 <= xc <= 1.0, f"xc out of bounds: {xc}"
            assert 0.0 <= yc <= 1.0, f"yc out of bounds: {yc}"
            assert 0.0 < bw <= 1.0, f"bw out of bounds: {bw}"
            assert 0.0 < bh <= 1.0, f"bh out of bounds: {bh}"
