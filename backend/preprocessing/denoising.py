import numpy as np
import cv2
import logging

logger = logging.getLogger(__name__)

def denoise(image: np.ndarray, method: str = 'median', kernel_size: int = 3) -> np.ndarray:
    """
    Denoise the image using either median or bilateral filter.
    Input image is expected to be float32 in [0, 1].
    """
    if image.size == 0:
        return image

    if method not in ['median', 'bilateral']:
        logger.warning(f"Unknown denoising method: {method}. Returning original image.")
        return image

    # Convert to float32 if not already
    img = image.astype(np.float32)

    if method == 'median':
        # cv2.medianBlur works with float32 only for kernel sizes 3 or 5
        # if other sizes, might need conversion
        if img.dtype != np.float32:
            img = img.astype(np.float32)
        res = cv2.medianBlur(img, kernel_size)
        return res
    elif method == 'bilateral':
        # bilateral filter for float32 requires specific params, we'll convert to uint8 just to be safe
        img_uint8 = (img * 255.0).clip(0, 255).astype(np.uint8)
        res = cv2.bilateralFilter(img_uint8, d=kernel_size, sigmaColor=75, sigmaSpace=75)
        return (res / 255.0).astype(np.float32)

    return image
