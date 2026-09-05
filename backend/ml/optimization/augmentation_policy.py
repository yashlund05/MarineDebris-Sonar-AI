"""
MarineDebris-Sonar-AI: Physically Plausible Acoustic Sonar Augmentation Policy
Ensures that data augmentation respects acoustic forward-looking sonar physics:
- Single-channel backscatter intensity (no artificial RGB hue/saturation shifts)
- Preservation of grazing-angle geometry (vertical flip strictly prohibited)
- Controlled acoustic speckle and gain perturbations
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass(frozen=True)
class SonarAugmentationPolicy:
    # Plausible spatial transforms
    degrees: float = 5.0          # Minor sensor yaw/pitch perturbation (+/- 5 deg)
    translate: float = 0.05       # Slight platform drift (+/- 5%)
    scale: float = 0.10           # Acoustic range scale jitter (+/- 10%)
    fliplr: float = 0.50          # Port/starboard swath symmetry reflection
    flipud: float = 0.00          # PROHIBITED: Vertical flip destroys grazing incidence & shadow geometry
    
    # Plausible intensity & gain perturbations
    hsv_h: float = 0.00           # PROHIBITED: Acoustic sonar has no optical hue
    hsv_s: float = 0.00           # PROHIBITED: Acoustic sonar has no optical color saturation
    hsv_v: float = 0.15           # Analog TVG (Time Varied Gain) intensity variation (+/- 15%)
    
    # Multi-image blending
    mosaic: float = 0.15          # Controlled mosaic (low probability to preserve acoustic shadow margins)
    mixup: float = 0.00           # Prohibited: Acoustic wavefront superpositions do not linearly alpha-blend
    copy_paste: float = 0.00      # Prohibited: Pasting breaks physical acoustic shadow continuity

    def to_ultralytics_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def get_yolo_training_args(self) -> Dict[str, Any]:
        return self.to_ultralytics_dict()


def get_sonar_augmentations() -> Dict[str, Any]:
    policy = SonarAugmentationPolicy()
    return policy.to_ultralytics_dict()
