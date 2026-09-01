"""Sidescan Sonar Acoustic Simulator for synthetic dataset generation & demo testing.

Synthesizes sidescan waterfall acoustic strips with realistic physics:
- Water column & nadir zone (near-zero acoustic return)
- Seabed bottom line detection zone (first return interface)
- Seabed reverberation texture with Rayleigh speckle noise
- Grazing-angle acoustic highlight and acoustic shadow pairs for debris targets
- Ground-truth target annotations in normalized YOLO format
- Explicit provenance tagging: source_type="SYNTHETIC", mode="DEMO"
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple
import numpy as np


@dataclass
class SyntheticTarget:
    class_id: int
    class_name: str
    x_center_px: int
    y_center_px: int
    width_px: int
    height_px: int
    shadow_length_px: int


class SonarSimulator:
    """Generates synthetic sidescan sonar waterfall strips and ground truth."""

    CLASSES = [
        "derelict_fishing_gear",
        "general_marine_debris",
        "shipwreck",
        "pipe_or_cylinder",
        "other_man_made_target",
    ]

    def __init__(
        self,
        width: int = 1024,
        height: int = 2000,
        nadir_width_pct: float = 0.08,
        altitude_m: float = 15.0,
        slant_range_m: float = 75.0,
    ) -> None:
        self.width = width
        self.height = height
        self.nadir_width = int(width * nadir_width_pct)
        self.altitude_m = altitude_m
        self.slant_range_m = slant_range_m
        self.range_res_m = slant_range_m / width

    def generate_strip(
        self, num_targets: int = 5, random_seed: Optional[int] = None
    ) -> tuple[np.ndarray, list[SyntheticTarget]]:
        """Generate synthetic sonar image array and injected targets.

        Returns:
            (image_array, targets) where image_array is float32 [0, 1].
        """
        if random_seed is not None:
            np.random.seed(random_seed)
            random.seed(random_seed)

        # 1. Base seabed texture with Rayleigh reverberation noise
        seabed_base = np.random.rayleigh(scale=0.35, size=(self.height, self.width)).astype(
            np.float32
        )

        # 2. Add subtle across-track ripple patterns
        x_coords = np.linspace(0, 40 * np.pi, self.width)
        ripples = (np.sin(x_coords) * 0.08).astype(np.float32)
        image = seabed_base + ripples

        # 3. Model water column / nadir gap (zero return)
        nadir_left = 0
        nadir_right = self.nadir_width
        # Smooth transition into seabed
        for col in range(nadir_left, nadir_right):
            factor = (col / nadir_right) ** 2
            image[:, col] *= factor

        # 4. Inject marine debris targets with acoustic highlight + shadow
        targets: list[SyntheticTarget] = []
        safe_x_min = self.nadir_width + 40
        safe_x_max = self.width - 120
        safe_y_min = 50
        safe_y_max = self.height - 150

        for _ in range(num_targets):
            cls_id = random.randint(0, len(self.CLASSES) - 1)
            cls_name = self.CLASSES[cls_id]

            w_px = random.randint(20, 70)
            h_px = random.randint(15, 60)
            x = random.randint(safe_x_min, safe_x_max)
            y = random.randint(safe_y_min, safe_y_max)

            # Shadow extends away from the transducer (to the right for starboard)
            shadow_len = int(w_px * random.uniform(1.5, 3.0))

            # Draw acoustic highlight (high backscatter reflection)
            y_start = max(0, y - h_px // 2)
            y_end = min(self.height, y + h_px // 2)
            x_start = max(0, x - w_px // 2)
            x_end = min(self.width, x + w_px // 2)

            image[y_start:y_end, x_start:x_end] = np.clip(
                image[y_start:y_end, x_start:x_end] * 2.2 + 0.4, 0.0, 1.0
            )

            # Draw acoustic shadow immediately following highlight
            shadow_start = x_end
            shadow_end = min(self.width, shadow_start + shadow_len)
            image[y_start:y_end, shadow_start:shadow_end] *= 0.05

            targets.append(
                SyntheticTarget(
                    class_id=cls_id,
                    class_name=cls_name,
                    x_center_px=x,
                    y_center_px=y,
                    width_px=w_px,
                    height_px=h_px,
                    shadow_length_px=shadow_len,
                )
            )

        # Normalize whole strip to [0, 1]
        image = np.clip(image, 0.0, 1.0)
        return image, targets

    def export_synthetic_sample(
        self,
        output_dir: str,
        sample_name: str = "synthetic_survey_01",
        num_targets: int = 6,
    ) -> dict[str, Any]:
        """Save synthetic sonar PNG, YOLO labels, and provenance manifest.

        Args:
            output_dir: Target folder.
            sample_name: Base file name.
            num_targets: Number of targets to inject.

        Returns:
            Manifest dict with provenance metadata.
        """
        import cv2

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)

        image, targets = self.generate_strip(num_targets=num_targets)

        # Save PNG image (uint8 grayscale)
        img_uint8 = (image * 255).astype(np.uint8)
        img_file = out_path / f"{sample_name}.png"
        cv2.imwrite(str(img_file), img_uint8)

        # Save YOLO format labels
        txt_lines = []
        for t in targets:
            norm_x = t.x_center_px / self.width
            norm_y = t.y_center_px / self.height
            norm_w = t.width_px / self.width
            norm_h = t.height_px / self.height
            txt_lines.append(
                f"{t.class_id} {norm_x:.6f} {norm_y:.6f} {norm_w:.6f} {norm_h:.6f}"
            )

        txt_file = out_path / f"{sample_name}.txt"
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("\n".join(txt_lines) + "\n")

        # Explicit provenance metadata
        manifest = {
            "source_type": "SYNTHETIC",
            "mode": "DEMO",
            "generator": "MarineDebrisSonarSimulator/1.0.0",
            "filename": f"{sample_name}.png",
            "dimensions": {"width": self.width, "height": self.height},
            "parameters": {
                "altitude_m": self.altitude_m,
                "slant_range_m": self.slant_range_m,
                "range_resolution_m": self.range_res_m,
            },
            "targets_count": len(targets),
            "targets": [
                {
                    "class_id": t.class_id,
                    "class_name": t.class_name,
                    "bbox_px": [t.x_center_px, t.y_center_px, t.width_px, t.height_px],
                }
                for t in targets
            ],
        }

        manifest_file = out_path / f"{sample_name}_provenance.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest
