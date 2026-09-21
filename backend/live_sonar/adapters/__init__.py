"""Sonar Stream Adapters package.

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

__all__ = [
    "SonarStreamAdapter",
    "ReplayStreamAdapter",
    "RTSPStreamAdapter",
    "USBCameraStreamAdapter",
    "NativeSonarStubAdapter",
    "sanitize_rtsp_uri",
    "validate_rtsp_uri",
]
