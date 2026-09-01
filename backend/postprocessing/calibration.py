import logging
import math
from typing import List
from backend.inference.detector import RawDetection

logger = logging.getLogger(__name__)

def calibrate_confidence(detections: List[RawDetection], temperature: float = 1.4) -> List[RawDetection]:
    """
    Apply temperature scaling to calibrate confidence scores.
    calibrated = sigmoid(logit(confidence) / temperature)
    """
    logger.info(f"Calibrating confidences with temperature={temperature}")
    
    for det in detections:
        # Clamp confidence to avoid log(0) or log(1)
        conf = max(min(det.confidence, 0.9999), 0.0001)
        
        # logit
        logit = math.log(conf / (1.0 - conf))
        
        # scale
        scaled_logit = logit / temperature
        
        # sigmoid
        calibrated_conf = 1.0 / (1.0 + math.exp(-scaled_logit))
        
        det.confidence_calibrated = calibrated_conf
        
    return detections
