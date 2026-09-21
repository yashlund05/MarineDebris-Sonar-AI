"""Live Sonar AI Detection & Tracking Subsystem.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.adapters.native import NativeSonarStubAdapter
from backend.live_sonar.adapters.replay import ReplayStreamAdapter
from backend.live_sonar.adapters.rtsp import (
    RTSPStreamAdapter,
    sanitize_rtsp_uri,
    validate_rtsp_uri,
)
from backend.live_sonar.adapters.usb import USBCameraStreamAdapter
from backend.live_sonar.buffer import FrameBuffer
from backend.live_sonar.models import (
    DropPolicy,
    LiveMetricsPayload,
    LiveNavigationData,
    LiveSonarException,
    LiveSonarSecurityViolationError,
    LiveSonarSessionConfig,
    LiveSonarSourceConnectionError,
    LiveSonarSourceInvalidError,
    LiveSonarStateError,
    LiveSonarTelemetry,
    NavPayload,
    QualityFlags,
    QualityPayload,
    SessionStatus,
    SonarFrame,
    SonarMetadataPayload,
    SonarStreamMetadata,
    StreamHealth,
    StreamMetrics,
)
from backend.live_sonar.session import LiveSonarSession, create_adapter

__all__ = [
    # Models and Payloads
    "SonarFrame",
    "SonarMetadataPayload",
    "NavPayload",
    "QualityPayload",
    "LiveMetricsPayload",
    "SessionStatus",
    "DropPolicy",
    "LiveSonarTelemetry",
    "LiveNavigationData",
    "QualityFlags",
    "StreamMetrics",
    "StreamHealth",
    "SonarStreamMetadata",
    "LiveSonarSessionConfig",
    # Exceptions
    "LiveSonarException",
    "LiveSonarSourceConnectionError",
    "LiveSonarSourceInvalidError",
    "LiveSonarSecurityViolationError",
    "LiveSonarStateError",
    # Buffer
    "FrameBuffer",
    # Adapters
    "SonarStreamAdapter",
    "ReplayStreamAdapter",
    "RTSPStreamAdapter",
    "USBCameraStreamAdapter",
    "NativeSonarStubAdapter",
    "sanitize_rtsp_uri",
    "validate_rtsp_uri",
    # Session
    "LiveSonarSession",
    "create_adapter",
]
