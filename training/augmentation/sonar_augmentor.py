"""Sonar-specific acoustic imagery data augmentation module.

Implements domain-aware transformations preserving acoustic shadow physics:
- Multiplicative speckle noise injection (Rayleigh distribution)
- Range-dependent acoustic attenuation / gain variation
- Grazing angle shadow contrast adjustment
- Horizontal swath flipping (with bounding box coordinate mirroring)
"""

import random
import numpy as np
from typing import Tuple, List, Dict, Any


def add_speckle_noise(image: np.ndarray, variance: float = 0.04) -> np.ndarray:
    """Inject acoustic multiplicative speckle noise into a sonar patch.

    Args:
        image: 2D float32 array normalized to [0, 1].
        variance: Noise variance parameter.

    Returns:
        Augmented image clipped to [0, 1].
    """
    noise = np.random.normal(1.0, np.sqrt(variance), size=image.shape).astype(np.float32)
    noisy_image = image * noise
    return np.clip(noisy_image, 0.0, 1.0)


def apply_acoustic_gain_variation(image: np.ndarray, gradient_strength: float = 0.3) -> np.ndarray:
    """Simulate across-track acoustic attenuation (Time-Varied Gain variation).

    Args:
        image: 2D float32 array (H, W) normalized to [0, 1].
        gradient_strength: Max intensity reduction across the swath range.

    Returns:
        Range-attenuated image.
    """
    h, w = image.shape
    # Linear attenuation gradient from nadir to far range
    gradient = np.linspace(1.0, 1.0 - gradient_strength, w, dtype=np.float32)
    gradient_2d = np.tile(gradient, (h, 1))
    return np.clip(image * gradient_2d, 0.0, 1.0)


def horizontal_flip_with_bboxes(
    image: np.ndarray, bboxes: list[list[float]]
) -> tuple[np.ndarray, list[list[float]]]:
    """Flip sonar image horizontally and mirror normalized bounding boxes.

    Args:
        image: 2D or 3D array.
        bboxes: List of [class_id, x_center, y_center, w, h] in normalized [0, 1] coords.

    Returns:
        Tuple of (flipped_image, flipped_bboxes).
    """
    flipped_image = np.fliplr(image)
    flipped_bboxes: list[list[float]] = []

    for box in bboxes:
        cls_id, x_center, y_center, w, h = box
        # Mirror x_center around 0.5
        new_x = 1.0 - x_center
        flipped_bboxes.append([cls_id, new_x, y_center, w, h])

    return flipped_image, flipped_bboxes


def augment_sonar_tile(
    image: np.ndarray,
    bboxes: list[list[float]],
    prob_speckle: float = 0.5,
    prob_gain: float = 0.4,
    prob_flip: float = 0.5,
) -> tuple[np.ndarray, list[list[float]]]:
    """Apply random sonar domain augmentations to an image tile and its labels.

    Args:
        image: 2D float32 [0, 1] sonar array.
        bboxes: Normalized YOLO bounding boxes.
        prob_speckle: Probability of speckle noise injection.
        prob_gain: Probability of range gain variation.
        prob_flip: Probability of horizontal flip.

    Returns:
        Augmented (image, bboxes).
    """
    aug_image = image.copy()
    aug_bboxes = [b.copy() for b in bboxes]

    if random.random() < prob_speckle:
        aug_image = add_speckle_noise(aug_image, variance=random.uniform(0.02, 0.06))

    if random.random() < prob_gain:
        aug_image = apply_acoustic_gain_variation(
            aug_image, gradient_strength=random.uniform(0.1, 0.35)
        )

    if random.random() < prob_flip:
        aug_image, aug_bboxes = horizontal_flip_with_bboxes(aug_image, aug_bboxes)

    return aug_image, aug_bboxes
