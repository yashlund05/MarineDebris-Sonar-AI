import logging
from dataclasses import dataclass
from typing import List, Any

logger = logging.getLogger(__name__)

@dataclass
class RawDetection:
    class_id: int
    class_name: str
    confidence: float
    bbox_x: int
    bbox_y: int
    bbox_w: int
    bbox_h: int
    tile_row: int
    tile_col: int
    mask_rle: str = None
    is_filtered: bool = False
    filtered_reason: str = None
    confidence_calibrated: float = None

CLASS_NAMES = [
    'derelict_fishing_gear',
    'general_marine_debris',
    'shipwreck',
    'pipe_or_cylinder',
    'other_man_made_target',
]

def detect_tiles(tiles: list, model: Any = None, conf_threshold: float = 0.35, device: str = 'cpu') -> List[List[RawDetection]]:
    """
    Run YOLOv8 detection on a batch of tiles.
    """
    if model is None:
        logger.warning("Detection model is None. Returning empty detections.")
        return [[] for _ in tiles]
        
    try:
        # Assuming tiles is a list of numpy arrays or images
        results = model.predict(tiles, conf=conf_threshold, device=device, verbose=False)
        
        all_detections = []
        for i, result in enumerate(results):
            tile_detections = []
            if result.boxes:
                for box in result.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    
                    # Convert to x, y, w, h
                    w = int(x2 - x1)
                    h = int(y2 - y1)
                    x = int(x1)
                    y = int(y1)
                    
                    # Get class name safely
                    class_name = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else "unknown"
                    
                    # Assuming we know tile_row and col somehow, but usually passed via kwargs or zipped
                    # For this signature, we default to 0 and let caller adjust or we assume flat list
                    tile_detections.append(
                        RawDetection(
                            class_id=cls_id,
                            class_name=class_name,
                            confidence=conf,
                            bbox_x=x,
                            bbox_y=y,
                            bbox_w=w,
                            bbox_h=h,
                            tile_row=0, # placeholder, should be updated by caller
                            tile_col=0  # placeholder, should be updated by caller
                        )
                    )
            all_detections.append(tile_detections)
            
        return all_detections
    except Exception as e:
        logger.error(f"Error during tile detection: {e}")
        return [[] for _ in tiles]
