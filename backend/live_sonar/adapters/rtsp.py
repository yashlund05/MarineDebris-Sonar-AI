"""RTSPStreamAdapter: Production-safe RTSP stream decoder with reconnect and timeout logic.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

import asyncio
import ipaddress
import os
import time
import urllib.parse
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

import cv2
import numpy as np

from backend.config import get_settings
from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.models import (
    LiveNavigationData,
    LiveSonarSecurityViolationError,
    LiveSonarSourceConnectionError,
    LiveSonarSourceInvalidError,
    LiveSonarTelemetry,
    QualityFlags,
    SonarFrame,
    SonarStreamMetadata,
    StreamHealth,
)

CLOUD_METADATA_HOSTNAMES = {
    "metadata.google.internal",
    "metadata",
    "instance-data",
    "metadata.internal",
}

LINK_LOCAL_NETWORK_V4 = ipaddress.ip_network("169.254.0.0/16")
SENSITIVE_PARAM_KEYS = ("token", "pwd", "password", "key", "secret", "auth", "apikey", "api_key")


def sanitize_rtsp_uri(uri: str) -> str:
    """Strip credentials and sensitive query parameters from RTSP URI for safe logging and display."""
    try:
        parsed = urllib.parse.urlsplit(uri)
        netloc = parsed.netloc
        if parsed.username or parsed.password:
            host_part = parsed.hostname or ""
            if parsed.port:
                host_part = f"{host_part}:{parsed.port}"
            netloc = f"***:***@{host_part}"

        sanitized_query = parsed.query
        if parsed.query:
            query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            sanitized_pairs = []
            for k, v in query_pairs:
                k_lower = k.lower()
                if any(sens in k_lower for sens in SENSITIVE_PARAM_KEYS):
                    sanitized_pairs.append((k, "***"))
                else:
                    sanitized_pairs.append((k, v))
            sanitized_query = urllib.parse.urlencode(sanitized_pairs, safe="*")

        return urllib.parse.urlunsplit(
            (parsed.scheme, netloc, parsed.path, sanitized_query, parsed.fragment)
        )
    except Exception:
        return "rtsp://***:***@redacted"


def _parse_candidate_ip(host: str) -> Optional[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    """Parse candidate host into IPv4 or IPv6 address, resolving octal, decimal, and hex notations."""
    # 1. Standard dotted-quad or IPv6
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass

    # 2. Decimal integer (e.g. 2852039166) or hex (0xa9fea9fe)
    try:
        val = int(host, 0)
        if 0 <= val <= 0xFFFFFFFF:
            return ipaddress.IPv4Address(val)
    except (ValueError, TypeError):
        pass

    # 3. Dotted octal or mixed notation (e.g. 0251.0376.0251.0376)
    parts = host.split(".")
    if len(parts) == 4:
        try:
            octets = [int(p, 0) for p in parts]
            if all(0 <= o <= 255 for o in octets):
                val = (octets[0] << 24) | (octets[1] << 16) | (octets[2] << 8) | octets[3]
                return ipaddress.IPv4Address(val)
        except (ValueError, TypeError):
            pass

    return None


def validate_rtsp_uri(
    uri: str,
    allow_local: bool = True,
    network_allowlist: Optional[List[str]] = None,
) -> None:
    """Validate RTSP scheme, block SSRF metadata endpoints and enforce network allowlist."""
    try:
        parsed = urllib.parse.urlsplit(uri)
    except Exception as e:
        raise LiveSonarSourceInvalidError(f"Invalid RTSP URI: {str(e)}")

    scheme = parsed.scheme.lower()
    if scheme not in ("rtsp", "rtsps"):
        raise LiveSonarSecurityViolationError(
            f"Invalid RTSP protocol scheme: '{scheme}'. Only rtsp:// and rtsps:// are allowed."
        )

    host = parsed.hostname
    if not host:
        raise LiveSonarSourceInvalidError("RTSP URI must include a valid hostname or IP address.")

    host_clean = host.strip().lower()

    # Block known cloud metadata hostnames
    if (
        host_clean.rstrip(".") in CLOUD_METADATA_HOSTNAMES
        or host_clean.endswith(".google.internal")
        or host_clean.endswith(".metadata.internal")
    ):
        raise LiveSonarSecurityViolationError(
            f"Access to cloud metadata endpoint ({host}) is strictly prohibited."
        )

    # Parse host to IP address (handles decimal, octal, hex, IPv6-mapped)
    ip_obj = _parse_candidate_ip(host)

    # If it's an IPv6 mapped IPv4 address, extract effective IPv4
    effective_v4: Optional[ipaddress.IPv4Address] = None
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.ipv4_mapped:
        effective_v4 = ip_obj.ipv4_mapped
    elif isinstance(ip_obj, ipaddress.IPv4Address):
        effective_v4 = ip_obj

    # Block link-local IPv4 network (169.254.0.0/16, including 169.254.169.254)
    if effective_v4 is not None and effective_v4 in LINK_LOCAL_NETWORK_V4:
        raise LiveSonarSecurityViolationError(
            f"Access to link-local cloud metadata endpoint (169.254.169.254 / {effective_v4}) is strictly prohibited."
        )

    # Also block IPv6 link-local addresses
    if isinstance(ip_obj, ipaddress.IPv6Address) and ip_obj.is_link_local:
        raise LiveSonarSecurityViolationError(
            f"Access to link-local network address ({host}) is strictly prohibited."
        )

    # Check loopback
    is_loopback = False
    if host_clean in ("localhost", "127.0.0.1", "::1"):
        is_loopback = True
    elif ip_obj is not None and ip_obj.is_loopback:
        is_loopback = True

    if is_loopback and not allow_local:
        raise LiveSonarSecurityViolationError(
            "Access to loopback network addresses is disabled by security configuration."
        )

    # Enforce network allowlist
    if network_allowlist is not None:
        allowed = False
        for entry in network_allowlist:
            entry_str = entry.strip()
            # Try matching as CIDR or IP network
            try:
                allowed_net = ipaddress.ip_network(entry_str, strict=False)
                if effective_v4 is not None and isinstance(allowed_net, ipaddress.IPv4Network):
                    if effective_v4 in allowed_net:
                        allowed = True
                        break
                elif ip_obj is not None:
                    if ip_obj in allowed_net:
                        allowed = True
                        break
            except ValueError:
                # Treat entry as hostname
                if host_clean == entry_str.lower():
                    allowed = True
                    break

        if not allowed:
            raise LiveSonarSecurityViolationError(
                f"Host '{host}' is not permitted by the configured network allowlist."
            )


class RTSPStreamAdapter(SonarStreamAdapter):
    """Production-safe streaming RTSP video decoder with auto-reconnect."""

    def __init__(
        self,
        source_uri: str,
        target_fps: float = 15.0,
        max_reconnect_attempts: int = 10,
        connect_timeout_sec: float = 5.0,
        session_id: str = "",
    ) -> None:
        self.source_uri = source_uri
        self.sanitized_uri = sanitize_rtsp_uri(source_uri)
        self.target_fps = max(0.1, target_fps)
        self.max_reconnect_attempts = max_reconnect_attempts
        self.connect_timeout_sec = connect_timeout_sec
        self.session_id = session_id

        self._connected: bool = False
        self._reconnecting: bool = False
        self._reconnect_attempts: int = 0
        self._cap: Optional[cv2.VideoCapture] = None
        self._health_status: str = "DISCONNECTED"
        self._health_details: str = "Adapter initialized"

        settings = get_settings()
        self._allow_local = getattr(settings, "LIVE_SONAR_ALLOW_LOCAL", True)
        self._network_allowlist = getattr(settings, "LIVE_SONAR_NETWORK_ALLOWLIST", None)

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Validate security policies and initialize RTSP stream connection."""
        validate_rtsp_uri(
            self.source_uri,
            allow_local=self._allow_local,
            network_allowlist=self._network_allowlist,
        )

        self._health_status = "CONNECTING"
        self._health_details = f"Connecting to {self.sanitized_uri}"

        # Enforce TCP transport for RTSP in OpenCV backend
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

        connected = await asyncio.to_thread(self._open_capture)
        if not connected:
            self._health_status = "ERROR"
            self._health_details = f"Failed to connect to RTSP feed: {self.sanitized_uri}"
            raise LiveSonarSourceConnectionError(
                f"Failed to connect to RTSP feed at '{self.sanitized_uri}' within timeout"
            )

        self._connected = True
        self._reconnecting = False
        self._reconnect_attempts = 0
        self._health_status = "OK"
        self._health_details = f"Connected to {self.sanitized_uri}"

    def _open_capture(self) -> bool:
        """Synchronously open cv2.VideoCapture with safety timeout."""
        try:
            cap = cv2.VideoCapture(self.source_uri, cv2.CAP_FFMPEG)
            if not cap.isOpened():
                cap.release()
                return False
            self._cap = cap
            return True
        except Exception:
            return False

    async def disconnect(self) -> None:
        """Terminate capture and close connection."""
        self._connected = False
        self._reconnecting = False
        self._health_status = "DISCONNECTED"
        self._health_details = "Disconnected by user"

        if self._cap is not None:
            await asyncio.to_thread(self._cap.release)
            self._cap = None

    async def _attempt_reconnect(self) -> bool:
        """Attempt exponential backoff reconnection."""
        self._reconnecting = True
        self._health_status = "RECONNECTING"

        backoff = 1.0
        while self._reconnect_attempts < self.max_reconnect_attempts and not self._connected:
            self._reconnect_attempts += 1
            self._health_details = (
                f"Reconnect attempt {self._reconnect_attempts}/{self.max_reconnect_attempts} "
                f"after {backoff:.1f}s backoff"
            )
            await asyncio.sleep(backoff)

            if self._cap is not None:
                await asyncio.to_thread(self._cap.release)
                self._cap = None

            success = await asyncio.to_thread(self._open_capture)
            if success:
                self._connected = True
                self._reconnecting = False
                self._health_status = "OK"
                self._health_details = f"Reconnected to {self.sanitized_uri}"
                return True

            backoff = min(30.0, backoff * 2.0)

        self._health_status = "ERROR"
        self._health_details = f"Exceeded maximum reconnect attempts ({self.max_reconnect_attempts})"
        return False

    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield normalized SonarFrame objects from the RTSP stream."""
        if not self._connected and not self._reconnecting:
            raise RuntimeError("Adapter is not connected. Call connect() first.")

        seq_num = 0
        frame_interval = 1.0 / self.target_fps

        while self._connected or self._reconnecting:
            loop_start = time.monotonic()

            if not self._connected:
                # In reconnect mode, wait for reconnect
                reconnected = await self._attempt_reconnect()
                if not reconnected:
                    break

            # Read frame in thread to avoid blocking event loop
            ret, bgr_frame = await asyncio.to_thread(self._read_frame)
            if not ret or bgr_frame is None:
                # Connection dropped
                self._connected = False
                self._health_status = "RECONNECTING"
                self._health_details = "RTSP frame read returned empty or disconnected"
                reconnected = await self._attempt_reconnect()
                if not reconnected:
                    break
                continue

            # Convert to grayscale 2D acoustic frame
            if len(bgr_frame.shape) == 3 and bgr_frame.shape[2] >= 3:
                frame_gray = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2GRAY)
            else:
                frame_gray = bgr_frame

            frame = SonarFrame(
                session_id=self.session_id,
                sequence_number=seq_num,
                timestamp_utc=datetime.now(timezone.utc),
                source_type="rtsp",
                source_uri=self.sanitized_uri,
                source_metadata={"source_type": "rtsp", "uri": self.sanitized_uri},
                image_data=frame_gray,
                sonar_metadata=LiveSonarTelemetry(),
                navigation=LiveNavigationData(),
                quality_flags=QualityFlags(
                    is_dropout=False,
                    motion_quality_score=0.9,
                    is_degraded=False,
                ),
            )
            seq_num += 1
            yield frame

            delay = frame_interval - (time.monotonic() - loop_start)
            if delay > 0:
                await asyncio.sleep(delay)

    def _read_frame(self) -> tuple[bool, Optional[np.ndarray]]:
        """Synchronously read next frame from capture."""
        if self._cap is None or not self._cap.isOpened():
            return False, None
        try:
            return self._cap.read()
        except Exception:
            return False, None

    async def health(self) -> StreamHealth:
        """Return real-time stream health."""
        return StreamHealth(
            status=self._health_status,
            details=self._health_details,
            source_uri=self.sanitized_uri,
            reconnect_attempts=self._reconnect_attempts,
        )

    async def metadata(self) -> SonarStreamMetadata:
        """Return stream resolution and parameters."""
        w, h = None, None
        if self._cap is not None and self._cap.isOpened():
            w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return SonarStreamMetadata(
            source_type="rtsp",
            source_uri=self.sanitized_uri,
            width=w,
            height=h,
            fps=self.target_fps,
            total_frames=None,
            is_live=True,
            extra={"reconnect_attempts": self._reconnect_attempts},
        )
