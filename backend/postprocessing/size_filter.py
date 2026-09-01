import logging
from typing import List
from backend.inference.detector import RawDetection

logger = logging.getLogger(__name__)

def filter_by_size(detections: List[RawDetection], min_area_px: int = 100, max_area_px: int = 500000) -> List[RawDetection]:
    """
    Filter detections by bounding box area.
    Too small or too large = likely false positive.
    """
    logger.info(f"Filtering detections by size: {min_area_px} <= area <= {max_area_px}")
    
    for det in detections:
        area = det.bbox_w * det.bbox_h
        if area < min_area_px or area > max_area_px:
            det.is_filtered = True
            det.filtered_reason = 'size_constraint'
            
    return detections
