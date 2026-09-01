import numpy as np
import logging
from backend.sonar_parser.models import SonarFrame

logger = logging.getLogger(__name__)

def assess_quality(frame: SonarFrame) -> SonarFrame:
    """
    Assess quality and motion robustness of a SonarFrame.
    Flags dropouts and calculates a motion_quality_score.
    """
    if not frame.pings:
        return frame

    num_dropouts = 0
    total_pings = len(frame.pings)

    # Detect dropouts
    for ping in frame.pings:
        if ping.data is None or len(ping.data) == 0:
            ping.is_dropout = True
        else:
            if np.isnan(ping.data).all() or np.all(ping.data == 0) or np.all(ping.data == ping.data[0]):
                ping.is_dropout = True
            else:
                ping.is_dropout = False

        if getattr(ping, 'is_dropout', False):
            num_dropouts += 1

    dropout_pct = num_dropouts / total_pings
    motion_quality_score = 1.0 - (0.3 * dropout_pct)

    # Degrade if pitch/roll exceed thresholds
    pitch_threshold = 5.0
    roll_threshold = 5.0
    for ping in frame.pings:
        if hasattr(ping, 'pitch') and ping.pitch is not None and abs(ping.pitch) > pitch_threshold:
            motion_quality_score -= 0.05
        if hasattr(ping, 'roll') and ping.roll is not None and abs(ping.roll) > roll_threshold:
            motion_quality_score -= 0.05

    motion_quality_score = max(0.0, min(1.0, motion_quality_score))

    if frame.metadata:
        frame.metadata.dropout_pct = dropout_pct
        frame.metadata.motion_quality_score = motion_quality_score

    logger.info(f"Assessed quality: dropout_pct={dropout_pct:.2f}, motion_quality_score={motion_quality_score:.2f}")
    return frame
