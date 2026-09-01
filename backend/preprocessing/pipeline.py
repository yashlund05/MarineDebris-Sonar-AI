import numpy as np
import logging
from typing import Optional, Any
from backend.sonar_parser.models import SonarFrame
from backend.preprocessing.quality import assess_quality
from backend.preprocessing.bottom_detection import detect_bottom
from backend.preprocessing.water_column import remove_water_column
from backend.preprocessing.normalization import normalize
from backend.preprocessing.clahe import apply_clahe
from backend.preprocessing.denoising import denoise
from backend.preprocessing.slant_range import correct_slant_range
from backend.preprocessing.tiler import generate_tiles, TileInfo

logger = logging.getLogger(__name__)

def preprocess_frame(frame: SonarFrame, settings: Optional[Any] = None) -> tuple[SonarFrame, list[TileInfo]]:
    """
    Chain: quality -> bottom_detection -> water_column -> normalization -> clahe -> denoising -> slant_range -> tiling
    Returns the processed frame and list of generated tiles.
    """
    logger.info("Starting preprocessing pipeline.")
    
    # 1. Quality Assessment
    frame = assess_quality(frame)

    if not frame.pings:
        logger.warning("Frame has no pings. Returning empty tile list.")
        return frame, []

    # Reconstruct or use image from frame
    if frame.image_array is not None and frame.image_array.size > 0:
        image = frame.image_array
    else:
        valid_data = [p.data for p in frame.pings if getattr(p, "data", None) is not None]
        if not valid_data:
            logger.warning("Frame has no image_array or ping data. Returning empty tile list.")
            return frame, []
        image = np.array(valid_data)
        if image.ndim == 2 and image.shape[0] == len(frame.pings):
            # If shape is (num_pings, samples), keep as (num_pings, samples)
            pass

    # 2. Bottom Detection
    bottom_line = detect_bottom(image)

    # 3. Water Column Removal
    image = remove_water_column(image, bottom_line)

    # 4. Normalization
    image = normalize(image)

    # 5. CLAHE
    image = apply_clahe(image)

    # 6. Denoising
    image = denoise(image, method='median')

    # 7. Slant Range Correction
    altitude = None
    range_res = None
    if frame.metadata:
        # Assuming metadata might contain these, else they stay None
        altitude = getattr(frame.metadata, 'altitude_m', None)
        range_res = getattr(frame.metadata, 'range_resolution_m', None)
        
    image = correct_slant_range(image, range_resolution_m=range_res, altitude=altitude)

    # 8. Tiling
    tiles = generate_tiles(image, tile_size=640, overlap=0.2, chunk_index=0, ping_offset=0)

    logger.info("Preprocessing pipeline completed successfully.")
    return frame, tiles
