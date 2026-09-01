import numpy as np
import logging

logger = logging.getLogger(__name__)

def remove_water_column(image: np.ndarray, bottom_line: np.ndarray) -> np.ndarray:
    """
    Zero out everything above the bottom line for each column.
    Input: image (H, W) and bottom_line (W,)
    """
    if image.size == 0 or len(bottom_line) == 0:
        return image

    H, W = image.shape
    out_img = image.copy()
    
    for c in range(W):
        row_limit = bottom_line[c]
        # zero out everything above row_limit
        if row_limit > 0:
            out_img[:row_limit, c] = 0.0
            
    return out_img
