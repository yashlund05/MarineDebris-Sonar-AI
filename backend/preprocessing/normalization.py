import numpy as np
import logging

logger = logging.getLogger(__name__)

def normalize(image: np.ndarray) -> np.ndarray:
    """
    Min-max normalize to float32 [0, 1].
    Handles constant images by returning zeros.
    """
    if image.size == 0:
        return image.astype(np.float32)

    min_val = np.min(image)
    max_val = np.max(image)

    if min_val == max_val:
        logger.warning("Image is constant, returning zeros.")
        return np.zeros_like(image, dtype=np.float32)

    normalized = (image - min_val) / (max_val - min_val)
    return normalized.astype(np.float32)
