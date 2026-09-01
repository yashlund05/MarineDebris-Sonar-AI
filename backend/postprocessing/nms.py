import logging
from typing import List
from backend.inference.detector import RawDetection

logger = logging.getLogger(__name__)

def apply_global_nms(all_detections: List[RawDetection], tile_infos: list, iou_threshold: float = 0.45) -> List[RawDetection]:
    """
    Apply Non-Maximum Suppression (NMS) across all tiles to remove duplicate detections 
    from overlapping tile regions.
    """
    logger.info(f"Applying global NMS with iou_threshold={iou_threshold}")
    
    # Placeholder: currently just returns all detections. 
    # Real implementation would calculate IoU and filter.
    filtered_detections = []
    
    # We'll just return them unchanged for now. 
    # Real implementation needs to map local tile coords to global coords.
    filtered_detections = all_detections
    
    return filtered_detections
