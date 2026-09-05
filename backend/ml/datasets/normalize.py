"""
MarineDebris-Sonar-AI: Acoustic Image Normalizer
Standardizes sonar images to canonical 640x640 3-channel replicated grayscale.
Strictly forbids synthetic colorization or false colormaps, preserving acoustic backscatter.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import cv2
import numpy as np


class ImageNormalizer:
    def __init__(self, target_size: int = 640):
        self.target_size = target_size

    def normalize_image(
        self,
        image_path: Path,
        output_path: Optional[Path] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Loads raw acoustic sonar image, converts to 3-channel replicated grayscale,
        and pads into an aspect-ratio-preserving 640x640 canvas.
        Returns:
            canvas: (640, 640, 3) uint8 numpy array
            transform: dict containing scale, dx, dy, orig_w, orig_h
        """
        img_raw = cv2.imread(str(image_path), cv2.IMREAD_UNCHANGED)
        if img_raw is None:
            raise ValueError(f"Could not read sonar image: {image_path}")

        # Preserve pure grayscale acoustic intensities
        if len(img_raw.shape) == 2:
            gray = img_raw
            orig_h, orig_w = gray.shape
            bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif len(img_raw.shape) == 3:
            orig_h, orig_w, c = img_raw.shape
            if c == 4:
                img_raw = cv2.cvtColor(img_raw, cv2.COLOR_BGRA2BGR)
            # Replicate grayscale to prevent artificial color artifacts
            gray = cv2.cvtColor(img_raw, cv2.COLOR_BGR2GRAY)
            bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            raise ValueError(f"Unexpected image dimensions: {img_raw.shape}")

        # Compute aspect-ratio-preserving scale and letterbox offset
        scale = min(self.target_size / orig_w, self.target_size / orig_h)
        new_w = int(round(orig_w * scale))
        new_h = int(round(orig_h * scale))

        resized = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

        # Center on 640x640 canvas with zero acoustic return (black padding)
        canvas = np.zeros((self.target_size, self.target_size, 3), dtype=np.uint8)
        dx = (self.target_size - new_w) // 2
        dy = (self.target_size - new_h) // 2
        canvas[dy : dy + new_h, dx : dx + new_w] = resized

        transform = {
            "orig_width": orig_w,
            "orig_height": orig_h,
            "scale": scale,
            "dx": dx,
            "dy": dy,
            "target_size": self.target_size,
        }

        if output_path is not None:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), canvas)

        return canvas, transform

    @staticmethod
    def transform_bbox_to_yolo(
        xmin: float,
        ymin: float,
        xmax: float,
        ymax: float,
        transform: Dict[str, Any],
    ) -> Tuple[float, float, float, float]:
        """Maps original image bbox coordinates to normalized [0, 1] YOLO format on padded canvas."""
        scale = transform["scale"]
        dx = transform["dx"]
        dy = transform["dy"]
        ts = transform["target_size"]

        # Scaled coordinates on canvas
        c_xmin = xmin * scale + dx
        c_xmax = xmax * scale + dx
        c_ymin = ymin * scale + dy
        c_ymax = ymax * scale + dy

        x_center = (c_xmin + c_xmax) / (2.0 * ts)
        y_center = (c_ymin + c_ymax) / (2.0 * ts)
        width = (c_xmax - c_xmin) / ts
        height = (c_ymax - c_ymin) / ts

        # Clamp safely into [0, 1]
        x_center = max(0.0, min(1.0, float(x_center)))
        y_center = max(0.0, min(1.0, float(y_center)))
        width = max(0.0, min(1.0, float(width)))
        height = max(0.0, min(1.0, float(height)))

        return round(x_center, 6), round(y_center, 6), round(width, 6), round(height, 6)
