"""NativeSonarStubAdapter: Integration boundary for ARIS/DIDSON/Blueprint acoustic heads.

Reports NOT_CONFIGURED when native hardware or SDK drivers are unavailable.
Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

from typing import AsyncIterator

from backend.live_sonar.adapters.base import SonarStreamAdapter
from backend.live_sonar.models import (
    LiveSonarSourceConnectionError,
    SonarFrame,
    SonarStreamMetadata,
    StreamHealth,
)


class NativeSonarStubAdapter(SonarStreamAdapter):
    """Hardware adapter boundary for native forward-looking sonars (e.g. ARIS 3000)."""

    def __init__(
        self,
        source_uri: str = "native://aris3000",
        target_fps: float = 15.0,
        session_id: str = "",
    ) -> None:
        self.source_uri = source_uri
        self.target_fps = target_fps
        self.session_id = session_id
        self._connected: bool = False

    @property
    def is_connected(self) -> bool:
        return self._connected

    async def connect(self) -> None:
        """Attempt connection to native sonar SDK.
        
        Raises LiveSonarSourceConnectionError reporting NOT_CONFIGURED when hardware absent.
        """
        self._connected = False
        raise LiveSonarSourceConnectionError(
            message="Native sonar SDK/driver not configured on host (status: NOT_CONFIGURED)",
            error_code="NATIVE_SONAR_UNAVAILABLE",
            details={
                "status": "NOT_CONFIGURED",
                "source_uri": self.source_uri,
                "supported_hardware": ["ARIS Explorer 3000", "DIDSON", "Blueprint Oculus"],
            },
        )

    async def disconnect(self) -> None:
        """Gracefully release native handles if any."""
        self._connected = False

    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield acoustic frames from native hardware (empty generator when not configured)."""
        # Because connect() raises when unconfigured, if called directly without connect:
        return
        yield  # type: ignore

    async def health(self) -> StreamHealth:
        """Return NOT_CONFIGURED status without crashing."""
        return StreamHealth(
            status="NOT_CONFIGURED",
            details="Native sonar SDK/driver not configured on host",
            source_uri=self.source_uri,
            reconnect_attempts=0,
        )

    async def metadata(self) -> SonarStreamMetadata:
        """Return static hardware specification metadata."""
        return SonarStreamMetadata(
            source_type="native_stub",
            source_uri=self.source_uri,
            width=None,
            height=None,
            fps=self.target_fps,
            total_frames=None,
            is_live=True,
            extra={
                "status": "NOT_CONFIGURED",
                "driver_linked": False,
            },
        )
