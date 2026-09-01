import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, tile_grid_size: tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization).
    Input image must be float32 [0, 1].
    """
    if image.size == 0:
        return image

    # Convert to uint8 for CLAHE
    img_uint8 = (image * 255.0).clip(0, 255).astype(np.uint8)
    
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    cl1 = clahe.apply(img_uint8)
    
    # Convert back to float32 [0, 1]
    res_float = (cl1 / 255.0).astype(np.float32)
    return res_float
