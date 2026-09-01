import numpy as np
import logging

logger = logging.getLogger(__name__)

def detect_bottom(image: np.ndarray) -> np.ndarray:
    """
    Detect the bottom line in a 2D sonar image.
    Input: image (H, W) float32
    Output: 1D array of length W with row indices of the bottom line.
    """
    if image.size == 0:
        return np.array([])

    H, W = image.shape
    bottom_line = np.zeros(W, dtype=int)
    threshold = 0.5  # assuming normalized image or scaled properly, can be configurable

    # Compute column-wise gradients for fallback
    gradients = np.gradient(image, axis=0)

    for c in range(W):
        col_data = image[:, c]
        # Find first row exceeding threshold
        above_thresh = np.where(col_data > threshold)[0]
        if len(above_thresh) > 0:
            bottom_line[c] = above_thresh[0]
        else:
            # Gradient-based fallback: finding maximum gradient
            bottom_line[c] = np.argmax(gradients[:, c])

    return bottom_line
