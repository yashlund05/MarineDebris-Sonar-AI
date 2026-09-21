"""Live Sonar data models, contracts, payloads, and lifecycle status definitions.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np
from backend.exceptions import AppException


class DropPolicy(str, Enum):
    """Queue overflow drop policies for the bounded frame buffer."""
    DROP_OLDEST = "DROP_OLDEST"  # Discard oldest unconsumed frame to favor lowest latency
    FIFO = "FIFO"                # Strict queue: block or wait until capacity is available
    DROP_NEWEST = "DROP_NEWEST"  # Discard incoming frame if buffer is full
    LATEST = "LATEST"            # Capacity 1: always keep the newest single frame


class SessionStatus(str, Enum):
    """Lifecycle states of a LiveSonarSession."""
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


@dataclass(frozen=True)
class LiveSonarTelemetry:
    """Sonar acoustic operating parameters. Null if source lacks telemetry."""
    frequency_hz: Optional[float] = None
    range_m: Optional[float] = None
    gain_db: Optional[float] = None
    beam_angle_deg: Optional[float] = None
    heading_deg: Optional[float] = None
    pitch_deg: Optional[float] = None
    roll_deg: Optional[float] = None
    depth_m: Optional[float] = None
    sound_speed_mps: Optional[float] = None


# Alias conforming to PROJECT.md interface contract
SonarMetadataPayload = LiveSonarTelemetry


@dataclass(frozen=True)
class LiveNavigationData:
    """GNSS/INS vessel/towfish position. Null if GPS/nav unavailable."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    heading_deg: Optional[float] = None
    depth_m: Optional[float] = None
    altitude_m: Optional[float] = None
    speed_knots: Optional[float] = None


# Alias conforming to PROJECT.md interface contract
NavPayload = LiveNavigationData


@dataclass(frozen=True)
class QualityFlags:
    """Acoustic quality assessment flags."""
    is_dropout: bool = False
    motion_quality_score: Optional[float] = None
    is_degraded: bool = False


# Alias conforming to PROJECT.md interface contract
QualityPayload = QualityFlags


@dataclass
class SonarFrame:
    """Live Sonar Video Frame data contract.
    
    Guarantees raw image immutability by setting ndarray writeable flag to False.
    Provides both .image_data and .raw_image property accessors.
    """
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    sequence_number: int = 0
    timestamp_utc: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_type: str = "replay"
    source_uri: str = ""
    source_metadata: Dict[str, Any] = field(default_factory=dict)
    image_data: np.ndarray = field(default_factory=lambda: np.zeros((1, 1), dtype=np.uint8))
    sonar_metadata: Optional[SonarMetadataPayload] = None
    navigation: Optional[NavPayload] = None
    quality_flags: QualityPayload = field(default_factory=QualityPayload)

    def __post_init__(self) -> None:
        if isinstance(self.image_data, np.ndarray):
            self.image_data.flags.writeable = False
        if self.sonar_metadata is None:
            self.sonar_metadata = SonarMetadataPayload()
        if self.navigation is None:
            self.navigation = NavPayload()

    @property
    def raw_image(self) -> np.ndarray:
        """Alias property matching M1<->M2 interface specification."""
        return self.image_data

    @raw_image.setter
    def raw_image(self, val: np.ndarray) -> None:
        if isinstance(val, np.ndarray):
            val.flags.writeable = False
        self.image_data = val


@dataclass
class StreamMetrics:
    """Real-time backpressure and throughput metrics."""
    input_fps: float = 0.0
    inference_fps: float = 0.0
    display_fps: float = 0.0
    processing_fps: float = 0.0
    effective_fps: float = 0.0
    latency_ms: float = 0.0
    queue_depth: int = 0
    frames_received: int = 0
    frames_processed: int = 0
    frames_dropped: int = 0
    drop_rate: float = 0.0
    active_tracks_count: int = 0
    confirmed_targets_count: int = 0


# Alias conforming to PROJECT.md interface contract
LiveMetricsPayload = StreamMetrics


@dataclass
class StreamHealth:
    """Health telemetry of a sonar source connection."""
    status: str = "OK"  # "OK" | "RECONNECTING" | "NOT_CONFIGURED" | "ERROR" | "DISCONNECTED"
    details: str = ""
    source_uri: str = ""
    reconnect_attempts: int = 0


@dataclass
class SonarStreamMetadata:
    """Static or stream-level parameters describing the sonar feed."""
    source_type: str = ""
    source_uri: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    total_frames: Optional[int] = None
    is_live: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LiveSonarSessionConfig:
    """Configuration settings for initiating a live sonar session."""
    session_id: str
    name: str = ""
    source_type: str = "replay"  # "replay" | "rtsp" | "usb" | "native_stub"
    source_uri: str = ""
    target_fps: float = 15.0
    inference_fps: float = 10.0
    buffer_size: int = 60
    drop_policy: DropPolicy = DropPolicy.DROP_OLDEST
    preprocessing_profile: str = "REALTIME"  # "REALTIME" | "BALANCED" | "QUALITY"
    enable_tracking: bool = True
    enable_recording: bool = False
    confidence_threshold: float = 0.35
    minimum_confirmed_frames: int = 3
    track_max_age_frames: int = 30
    loop: bool = True


# Domain Exceptions for Live Sonar Subsystem
class LiveSonarException(AppException):
    """Base exception for all live sonar streaming errors."""
    status_code: int = 500
    error_code: str = "LIVE_SONAR_ERROR"
    message: str = "Live sonar subsystem error occurred."


class LiveSonarSourceConnectionError(LiveSonarException):
    """Raised when connection to the sonar stream or device cannot be established."""
    status_code: int = 502
    error_code: str = "LIVE_SONAR_CONNECTION_ERROR"
    message: str = "Failed to connect to sonar stream source."


class LiveSonarSourceInvalidError(LiveSonarException):
    """Raised when a stream source URI, file path, or device specification is invalid."""
    status_code: int = 400
    error_code: str = "LIVE_SONAR_SOURCE_INVALID"
    message: str = "Sonar stream source configuration or URI is invalid."


class LiveSonarSecurityViolationError(LiveSonarException):
    """Raised when a stream source URI violates SSRF or security allowlists."""
    status_code: int = 400
    error_code: str = "LIVE_SONAR_SECURITY_VIOLATION"
    message: str = "Sonar stream source URI violates security policy."


class LiveSonarStateError(LiveSonarException):
    """Raised when attempting an invalid lifecycle state transition."""
    status_code: int = 409
    error_code: str = "LIVE_SONAR_STATE_ERROR"
    message: str = "Invalid operation for current live sonar session state."
