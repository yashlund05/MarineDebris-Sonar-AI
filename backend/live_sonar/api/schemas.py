"""Pydantic schemas for Live Sonar REST and WebSocket APIs.

Conforms to Requirement R3 of ORIGINAL_REQUEST.md.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CreateLiveSessionRequest(BaseModel):
    """Payload to create a new live sonar session."""
    session_id: Optional[str] = None
    name: str = "Live Sonar Session"
    source_type: str = Field("demo", description="'demo', 'replay', 'rtsp', 'usb', or 'native_stub'")
    source_uri: str = Field("demo", description="File path, RTSP URL, device ID, stub URI, or 'demo' for built-in demo")
    target_fps: float = Field(15.0, ge=1.0, le=60.0)
    inference_fps: float = Field(10.0, ge=1.0, le=30.0)
    buffer_size: int = Field(60, ge=4, le=1000)
    drop_policy: str = Field("DROP_OLDEST", description="'DROP_OLDEST', 'FIFO', 'DROP_NEWEST', 'LATEST'")
    preprocessing_profile: str = Field("REALTIME", description="'REALTIME', 'BALANCED', 'QUALITY'")
    enable_tracking: bool = True
    enable_recording: bool = False
    confidence_threshold: float = Field(0.35, ge=0.05, le=0.99)
    minimum_confirmed_frames: int = Field(3, ge=1, le=20)


class SessionResponse(BaseModel):
    """Status and configuration of a live sonar session."""
    session_id: str
    name: str
    source_type: str
    source_uri: str
    status: str
    started_at: Optional[str] = None
    stopped_at: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    is_recording: bool = False
    active_tracks_count: int = 0
    confirmed_targets_count: int = 0


class LiveHealthResponse(BaseModel):
    """Truthful system health status."""
    status: str
    active_sessions_count: int
    gpu_available: bool
    inference_device: str
    model_status: str
    model_loaded: bool
    timestamp_utc: str
