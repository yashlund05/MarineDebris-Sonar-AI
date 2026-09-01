from dataclasses import dataclass, field
from typing import Optional
import numpy as np


@dataclass
class SonarPing:
    ping_number: int = 0               # absolute index within the full survey
    timestamp: float = 0.0
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading: Optional[float] = None
    pitch: Optional[float] = None      # degrees; populated only if source file provides attitude data
    roll: Optional[float] = None       # degrees; populated only if source file provides attitude data
    altitude: Optional[float] = None
    range_m: Optional[float] = None
    is_dropout: bool = False           # flagged by the Quality/Motion Robustness Layer
    pixel_y: int = 0                   # row index within this chunk's image_array
    data: Optional[np.ndarray] = None  # optional raw samples for this ping


@dataclass
class SonarMetadata:
    frequency_hz: Optional[float] = None
    samples_per_ping: int = 0
    range_resolution_m: Optional[float] = None
    along_track_resolution_m: Optional[float] = None
    motion_quality_score: Optional[float] = None   # 0-1, set by Quality/Motion Robustness Layer
    dropout_pct: Optional[float] = None            # % of pings flagged as dropout
    min_latitude: Optional[float] = None
    max_latitude: Optional[float] = None
    min_longitude: Optional[float] = None
    max_longitude: Optional[float] = None
    survey_start_time: Optional[float] = None
    survey_end_time: Optional[float] = None
    sonar_system: Optional[str] = None
    has_attitude_data: bool = False


@dataclass
class SonarFrame:
    survey_id: str = ""
    source_file: str = ""
    channel: str = "starboard"              # 'port' | 'starboard'
    chunk_index: int = 0                    # 0-based position within survey
    ping_offset: int = 0                    # index of first ping in full survey
    pings: list[SonarPing] = field(default_factory=list)
    image_array: Optional[np.ndarray] = None   # (chunk_H, W) float32, normalized 0-1
    metadata: SonarMetadata = field(default_factory=SonarMetadata)
