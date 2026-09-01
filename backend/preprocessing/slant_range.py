import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def correct_slant_range(image: np.ndarray, range_resolution_m: Optional[float] = None, altitude: Optional[float] = None) -> np.ndarray:
    """
    Apply slant-range correction to sonar image.
    If range_resolution_m and altitude are available, apply geometric correction.
    Otherwise return image unchanged with a warning logged.
    """
    if image.size == 0:
        return image

    if range_resolution_m is None or altitude is None:
        logger.warning("Missing range_resolution_m or altitude. Skipping slant-range correction.")
        return image

    if altitude <= 0 or range_resolution_m <= 0:
        logger.warning("Invalid altitude or range_resolution_m. Skipping slant-range correction.")
        return image

    H, W = image.shape
    out_img = np.zeros_like(image)
    
    # Calculate pixel row corresponding to altitude (water depth)
    alt_pixel = int(altitude / range_resolution_m)
    
    for r in range(H):
        if r < alt_pixel:
            # Water column, already handled or just zero
            continue
            
        # Ground range calculation
        # slant_range^2 = ground_range^2 + altitude^2
        slant_range = r * range_resolution_m
        
        if slant_range > altitude:
            ground_range = np.sqrt(slant_range**2 - altitude**2)
            ground_pixel = int(ground_range / range_resolution_m)
            
            if 0 <= ground_pixel < H:
                out_img[ground_pixel, :] = image[r, :]
                
    # Fill gaps (simple interpolation could be added here if needed)
    return out_img
