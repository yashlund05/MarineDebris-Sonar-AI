"""
MarineDebris-Sonar-AI: Physically Grounded Acoustic Sonar Augmentation Engine
Applies acoustic wave propagation, transducer artifact, and grazing-geometry-preserving
transformations to forward-looking sonar images and YOLO bounding boxes.
"""

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Tuple, Optional, Union, Any

import cv2
import numpy as np


class SonarAugmentationMode(str, Enum):
    BASELINE = "BASELINE"
    CONSERVATIVE_SONAR = "CONSERVATIVE_SONAR"
    NOISE_ROBUST = "NOISE_ROBUST"
    SMALL_OBJECT = "SMALL_OBJECT"
    HARD_NEGATIVE = "HARD_NEGATIVE"


@dataclass
class AugmentationConfig:
    mode: SonarAugmentationMode = SonarAugmentationMode.CONSERVATIVE_SONAR
    # Multiplicative Speckle
    speckle_prob: float = 0.50
    speckle_scale: float = 0.12
    speckle_distribution: str = "gamma"  # "gamma" or "rayleigh"
    
    # Transmission Loss / Range Attenuation
    transmission_loss_prob: float = 0.35
    attenuation_coeff: float = 0.15
    
    # Transducer Periodic Stripe Artifacts
    stripe_prob: float = 0.25
    num_stripes: int = 4
    stripe_intensity: float = 0.10
    
    # Spatial Geometry (Forward-Looking Sonar)
    degrees: float = 5.0          # Max yaw rotation (+/- deg)
    translate: float = 0.05       # Platform drift (+/- 5%)
    scale: float = 0.08           # Acoustic range jitter (+/- 8%)
    fliplr_prob: float = 0.50     # Port/Starboard swath symmetry
    flipud_prob: float = 0.00     # STRICTLY PROHIBITED: Breaks grazing angle & shadow physics
    
    # Small object targeted scaling
    min_crop_scale: float = 0.85
    max_crop_scale: float = 1.00


class SonarAcousticAugmentor:
    """
    Physically grounded acoustic augmentor for forward-looking and side-scan sonar.
    Preserves acoustic shadow orientation, grazing incidence angles, and single-channel intensity.
    """

    def __init__(self, config: Optional[AugmentationConfig] = None, seed: Optional[int] = None):
        self.config = config or AugmentationConfig()
        if self.config.flipud_prob > 0.0:
            raise ValueError(
                "CRITICAL ACOUSTIC PHYSICS VIOLATION: flipud_prob must be 0.0. "
                "Vertical flipping inverts acoustic grazing angle and shadow geometry."
            )
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    @classmethod
    def from_policy(cls, mode: Union[str, SonarAugmentationMode], seed: Optional[int] = None) -> "SonarAcousticAugmentor":
        if isinstance(mode, str):
            mode = SonarAugmentationMode(mode.upper())

        if mode == SonarAugmentationMode.BASELINE:
            cfg = AugmentationConfig(
                mode=mode,
                speckle_prob=0.0,
                transmission_loss_prob=0.0,
                stripe_prob=0.0,
                degrees=0.0,
                translate=0.0,
                scale=0.0,
                fliplr_prob=0.0,
                flipud_prob=0.0,
            )
        elif mode == SonarAugmentationMode.CONSERVATIVE_SONAR:
            cfg = AugmentationConfig(
                mode=mode,
                speckle_prob=0.50,
                speckle_scale=0.10,
                speckle_distribution="gamma",
                transmission_loss_prob=0.30,
                attenuation_coeff=0.12,
                stripe_prob=0.20,
                stripe_intensity=0.08,
                degrees=4.0,
                translate=0.04,
                scale=0.06,
                fliplr_prob=0.50,
            )
        elif mode == SonarAugmentationMode.NOISE_ROBUST:
            cfg = AugmentationConfig(
                mode=mode,
                speckle_prob=0.85,
                speckle_scale=0.22,
                speckle_distribution="rayleigh",
                transmission_loss_prob=0.60,
                attenuation_coeff=0.25,
                stripe_prob=0.50,
                stripe_intensity=0.18,
                degrees=6.0,
                translate=0.06,
                scale=0.10,
                fliplr_prob=0.50,
            )
        elif mode == SonarAugmentationMode.SMALL_OBJECT:
            cfg = AugmentationConfig(
                mode=mode,
                speckle_prob=0.30,
                speckle_scale=0.08,
                transmission_loss_prob=0.20,
                stripe_prob=0.10,
                degrees=3.0,
                translate=0.08,
                scale=0.15,
                fliplr_prob=0.50,
                min_crop_scale=0.70,
            )
        elif mode == SonarAugmentationMode.HARD_NEGATIVE:
            cfg = AugmentationConfig(
                mode=mode,
                speckle_prob=0.75,
                speckle_scale=0.20,
                transmission_loss_prob=0.50,
                stripe_prob=0.45,
                stripe_intensity=0.15,
                degrees=5.0,
                translate=0.05,
                scale=0.08,
                fliplr_prob=0.50,
            )
        else:
            cfg = AugmentationConfig(mode=mode)

        return cls(config=cfg, seed=seed)

    def apply_multiplicative_speckle(self, img: np.ndarray) -> np.ndarray:
        """
        Multiplicative acoustic speckle noise modeling:
        I_noisy = I * (1 + eta), where eta follows Gamma or Rayleigh distribution.
        """
        is_uint8 = img.dtype == np.uint8
        img_f = img.astype(np.float32)

        h, w = img_f.shape[:2]
        c = img_f.shape[2] if img_f.ndim == 3 else 1

        scale = self.config.speckle_scale
        if self.config.speckle_distribution == "gamma":
            # Gamma distribution with mean=1.0
            shape_param = max(1.0, 1.0 / (scale ** 2))
            noise = np.random.gamma(shape=shape_param, scale=1.0 / shape_param, size=(h, w))
        else:
            # Rayleigh noise
            noise = np.random.rayleigh(scale=scale, size=(h, w)) + (1.0 - scale * math.sqrt(math.pi / 2.0))

        if c > 1 and img_f.ndim == 3:
            noise = np.expand_dims(noise, axis=-1)

        noisy = np.clip(img_f * noise, 0.0, 255.0 if is_uint8 else 1.0)
        return noisy.astype(np.uint8) if is_uint8 else noisy.astype(np.float32)

    def apply_transmission_loss(self, img: np.ndarray) -> np.ndarray:
        """
        Simulates spherical spreading and acoustic medium attenuation across range:
        A(r) decreases with acoustic distance (typically top to bottom in FLS).
        """
        is_uint8 = img.dtype == np.uint8
        img_f = img.astype(np.float32)

        h, w = img_f.shape[:2]
        # Range profile along vertical axis (0: near-range transducer, h: far-range)
        r = np.linspace(0.0, 1.0, h, dtype=np.float32)
        # Absorption and spreading drop
        drop = 1.0 - (self.config.attenuation_coeff * r)
        drop = np.tile(drop[:, np.newaxis], (1, w))
        if img_f.ndim == 3:
            drop = np.expand_dims(drop, axis=-1)

        attenuated = np.clip(img_f * drop, 0.0, 255.0 if is_uint8 else 1.0)
        return attenuated.astype(np.uint8) if is_uint8 else attenuated.astype(np.float32)

    def apply_stripe_artifacts(self, img: np.ndarray) -> np.ndarray:
        """
        Simulates transducer beam calibration imbalances and periodic beam stripe noise.
        """
        is_uint8 = img.dtype == np.uint8
        img_f = img.astype(np.float32)
        h, w = img_f.shape[:2]

        # Horizontal or radial beam striping
        freq = self.config.num_stripes * 2.0 * math.pi
        phase = random.uniform(0.0, 2.0 * math.pi)
        x = np.linspace(0.0, freq, w, dtype=np.float32) + phase
        stripe = 1.0 + (self.config.stripe_intensity * np.sin(x))
        stripe = np.tile(stripe[np.newaxis, :], (h, 1))

        if img_f.ndim == 3:
            stripe = np.expand_dims(stripe, axis=-1)

        striped = np.clip(img_f * stripe, 0.0, 255.0 if is_uint8 else 1.0)
        return striped.astype(np.uint8) if is_uint8 else striped.astype(np.float32)

    def apply_spatial_transforms(
        self,
        img: np.ndarray,
        bboxes: Optional[List[List[float]]] = None,
    ) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Applies grazing-angle-preserving spatial transformations to image and YOLO bboxes:
        - Bounded yaw rotation (+/- degrees)
        - Horizontal flip (port/starboard swath symmetry)
        - Translation and scaling jitter
        - VERTICAL FLIP STRICTLY PROHIBITED
        """
        h, w = img.shape[:2]
        boxes = [list(b) for b in bboxes] if bboxes is not None else []
        transformed_img = img.copy()

        # 1. Swath Reflection (Horizontal Flip)
        if random.random() < self.config.fliplr_prob:
            transformed_img = cv2.flip(transformed_img, 1)
            new_boxes = []
            for b in boxes:
                cls_id, xc, yc, bw, bh = b[0], b[1], b[2], b[3], b[4]
                new_xc = 1.0 - xc
                new_boxes.append([cls_id, new_xc, yc, bw, bh])
            boxes = new_boxes

        # 2. Bounded Rotation & Translation
        angle = random.uniform(-self.config.degrees, self.config.degrees)
        tx_px = random.uniform(-self.config.translate, self.config.translate) * w
        ty_px = random.uniform(-self.config.translate, self.config.translate) * h
        scale_val = 1.0 + random.uniform(-self.config.scale, self.config.scale)

        if abs(angle) > 0.01 or abs(tx_px) > 0.5 or abs(ty_px) > 0.5 or abs(scale_val - 1.0) > 0.01:
            cx, cy = w / 2.0, h / 2.0
            M = cv2.getRotationMatrix2D((cx, cy), angle, scale_val)
            M[0, 2] += tx_px
            M[1, 2] += ty_px

            transformed_img = cv2.warpAffine(
                transformed_img,
                M,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_REFLECT_101,
            )

            # Transform bounding boxes
            new_boxes = []
            for b in boxes:
                cls_id, xc, yc, bw, bh = b[0], b[1], b[2], b[3], b[4]
                # Convert normalized YOLO to pixel corners
                xmin = (xc - bw / 2.0) * w
                xmax = (xc + bw / 2.0) * w
                ymin = (yc - bh / 2.0) * h
                ymax = (yc + bh / 2.0) * h

                corners = np.array([
                    [xmin, ymin, 1.0],
                    [xmax, ymin, 1.0],
                    [xmax, ymax, 1.0],
                    [xmin, ymax, 1.0],
                ], dtype=np.float32)

                warped = M.dot(corners.T).T  # 4x2
                new_xmin = max(0.0, float(np.min(warped[:, 0])))
                new_xmax = min(float(w), float(np.max(warped[:, 0])))
                new_ymin = max(0.0, float(np.min(warped[:, 1])))
                new_ymax = min(float(h), float(np.max(warped[:, 1])))

                new_w_px = new_xmax - new_xmin
                new_h_px = new_ymax - new_ymin

                # Discard boxes clipped outside image or degenerate (< 4px)
                if new_w_px >= 4.0 and new_h_px >= 4.0:
                    box_xc = (new_xmin + new_w_px / 2.0) / w
                    box_yc = (new_ymin + new_h_px / 2.0) / h
                    box_w = new_w_px / w
                    box_h = new_h_px / h
                    new_boxes.append([cls_id, box_xc, box_yc, box_w, box_h])

            boxes = new_boxes

        return transformed_img, boxes

    def augment(
        self,
        img: np.ndarray,
        bboxes: Optional[List[List[float]]] = None,
    ) -> Tuple[np.ndarray, List[List[float]]]:
        """
        Executes full acoustic augmentation pipeline according to active configuration.
        """
        bboxes = bboxes or []
        res_img = img.copy()

        # 1. Multiplicative Speckle
        if random.random() < self.config.speckle_prob:
            res_img = self.apply_multiplicative_speckle(res_img)

        # 2. Transmission Loss / Range Attenuation
        if random.random() < self.config.transmission_loss_prob:
            res_img = self.apply_transmission_loss(res_img)

        # 3. Transducer Stripe Artifacts
        if random.random() < self.config.stripe_prob:
            res_img = self.apply_stripe_artifacts(res_img)

        # 4. Grazing-Angle Geometry Preserving Spatial Transforms
        res_img, res_boxes = self.apply_spatial_transforms(res_img, bboxes)

        return res_img, res_boxes
