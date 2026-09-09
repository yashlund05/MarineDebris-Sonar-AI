"""
Configuration schemas and settings for the SidescanTools Sonar Enhancement Pipeline.
"""

from dataclasses import dataclass, field
from typing import Tuple, Dict, Any, Optional
from enum import Enum


class ColormapName(str, Enum):
    GRAYSCALE = "grayscale"
    VIRIDIS = "viridis"
    INFERNO = "inferno"
    MAGMA = "magma"
    PLASMA = "plasma"
    TURBO = "turbo"
    AMBER = "amber"


class DetectionInputMode(str, Enum):
    RAW = "raw"
    ENHANCED_GRAYSCALE = "enhanced_grayscale"


@dataclass
class SonarEnhancementConfig:
    """
    Configuration parameters for SidescanTools-based acoustic processing.
    Defaults are scientifically conservative: sharpening and gain normalization default to OFF.
    """
    # Radiometric filtering
    convert_to_db: bool = True
    stripe_noise_filter: bool = True
    clahe: bool = True
    clahe_clip_limit: float = 0.01  # SidescanTools skimage default (~1.8 OpenCV equivalent)
    clahe_grid_size: Tuple[int, int] = (8, 8)

    # Experimental high-frequency emphasis (Homomorphic filter) - MUST DEFAULT TO FALSE
    sharpening: bool = False
    sharpening_gamma_h: float = 2.0
    sharpening_gamma_l: float = 0.5
    sharpening_c: float = 1.5

    # Metadata-gated gain normalization (BAC / EGN) - MUST DEFAULT TO FALSE
    gain_normalization: bool = False
    gain_norm_strategy: str = "bac"  # 'bac' (Beam Angle Correction) or 'egn' (Empirical Gain Normalization)

    # Display pseudocolor visualization
    pseudo_color: bool = True
    colormap: str = ColormapName.VIRIDIS.value

    # Downstream ML detection routing
    detection_input_mode: str = DetectionInputMode.RAW.value

    def to_dict(self) -> Dict[str, Any]:
        return {
            "convert_to_db": self.convert_to_db,
            "stripe_noise_filter": self.stripe_noise_filter,
            "clahe": self.clahe,
            "clahe_clip_limit": self.clahe_clip_limit,
            "clahe_grid_size": list(self.clahe_grid_size),
            "sharpening": self.sharpening,
            "sharpening_gamma_h": self.sharpening_gamma_h,
            "sharpening_gamma_l": self.sharpening_gamma_l,
            "sharpening_c": self.sharpening_c,
            "gain_normalization": self.gain_normalization,
            "gain_norm_strategy": self.gain_norm_strategy,
            "pseudo_color": self.pseudo_color,
            "colormap": self.colormap,
            "detection_input_mode": self.detection_input_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SonarEnhancementConfig":
        grid = data.get("clahe_grid_size", (8, 8))
        if isinstance(grid, list):
            grid = tuple(grid)
        return cls(
            convert_to_db=bool(data.get("convert_to_db", True)),
            stripe_noise_filter=bool(data.get("stripe_noise_filter", True)),
            clahe=bool(data.get("clahe", True)),
            clahe_clip_limit=float(data.get("clahe_clip_limit", 0.01)),
            clahe_grid_size=grid,
            sharpening=bool(data.get("sharpening", False)),
            sharpening_gamma_h=float(data.get("sharpening_gamma_h", 2.0)),
            sharpening_gamma_l=float(data.get("sharpening_gamma_l", 0.5)),
            sharpening_c=float(data.get("sharpening_c", 1.5)),
            gain_normalization=bool(data.get("gain_normalization", False)),
            gain_norm_strategy=str(data.get("gain_norm_strategy", "bac")),
            pseudo_color=bool(data.get("pseudo_color", True)),
            colormap=str(data.get("colormap", ColormapName.VIRIDIS.value)),
            detection_input_mode=str(data.get("detection_input_mode", DetectionInputMode.RAW.value)),
        )
