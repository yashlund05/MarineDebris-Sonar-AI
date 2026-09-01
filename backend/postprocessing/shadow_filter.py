import logging
from typing import List
import numpy as np
from backend.inference.detector import RawDetection

logger = logging.getLogger(__name__)

def filter_shadow_artifacts(detections: List[RawDetection], image: np.ndarray = None) -> List[RawDetection]:
    """
    Analyze if detection is likely an acoustic shadow artifact.
    """
    logger.info("Filtering shadow artifacts.")
    
    for det in detections:
        # Placeholder logic: for now, we don't filter anything unless specific criteria are met
        if det.confidence < 0.0:  # never true, just an example
            det.is_filtered = True
            det.filtered_reason = 'acoustic_shadow_mismatch'
            
    return detections
