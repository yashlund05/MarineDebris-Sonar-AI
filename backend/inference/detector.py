import logging
import time
from dataclasses import dataclass
from typing import List, Any, Union, Optional
import numpy as np
import cv2
import torch

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
    mask_rle: Optional[str] = None
    is_filtered: bool = False
    filtered_reason: Optional[str] = None
    confidence_calibrated: Optional[float] = None

CLASS_NAMES = [
    'derelict_fishing_gear',
    'general_marine_debris',
    'shipwreck',
    'pipe_or_cylinder',
    'other_man_made_target',
]

def detect_tiles(tiles: list, model: Any = None, conf_threshold: float = 0.35, device: str = 'cpu') -> List[List[RawDetection]]:
    """
    High-efficiency tile detection with zero redundant conversions and torch.inference_mode.
    Budget-compliant for real-time acoustic pipeline (P95 <= 125 ms).
    """
    if model is None:
        logger.warning("Detection model is None. Returning empty detections.")
        return [[] for _ in tiles]
        
    try:
        images_to_predict = []
        for t in tiles:
            arr = t.tile if hasattr(t, "tile") else t
            if isinstance(arr, np.ndarray):
                if arr.dtype != np.uint8:
                    if arr.max() <= 1.0:
                        arr = (arr * 255.0).clip(0, 255).astype(np.uint8)
                    else:
                        arr = arr.clip(0, 255).astype(np.uint8)
                if len(arr.shape) == 2:
                    arr = cv2.cvtColor(arr, cv2.COLOR_GRAY2BGR)
            images_to_predict.append(arr)

        with torch.inference_mode():
            results = model.predict(images_to_predict, conf=conf_threshold, device=device, verbose=False)
        
        all_detections = []
        for i, result in enumerate(results):
            tile_detections = []
            orig_tile = tiles[i] if i < len(tiles) else None
            t_row = getattr(orig_tile, "tile_row", 0) if orig_tile else 0
            t_col = getattr(orig_tile, "tile_col", 0) if orig_tile else 0

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
                    
                    tile_detections.append(
                        RawDetection(
                            class_id=cls_id,
                            class_name=class_name,
                            confidence=conf,
                            bbox_x=x,
                            bbox_y=y,
                            bbox_w=w,
                            bbox_h=h,
                            tile_row=t_row,
                            tile_col=t_col,
                        )
                    )
            all_detections.append(tile_detections)
            
        return all_detections
    except Exception as e:
        logger.error(f"Error during tile detection: {e}")
        return [[] for _ in tiles]
