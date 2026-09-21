"""Abstract Base Class for all Sonar Stream Adapters.

Conforms to Requirement R1 of ORIGINAL_REQUEST.md and spec_backend.md.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncIterator

from backend.live_sonar.models import (
    SonarFrame,
    SonarStreamMetadata,
    StreamHealth,
)


class SonarStreamAdapter(ABC):
    """Abstract Base Class defining the source adapter interface."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the sonar hardware, stream, or file source.
        
        Raises:
            LiveSonarSourceConnectionError: If connection fails.
            LiveSonarSourceInvalidError: If URI or path is invalid.
            LiveSonarSecurityViolationError: If URI violates security allowlists.
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Gracefully terminate stream connection and release underlying resources."""
        pass

    @abstractmethod
    async def frames(self) -> AsyncIterator[SonarFrame]:
        """Yield normalized SonarFrame instances from the source."""
        pass

    @abstractmethod
    async def health(self) -> StreamHealth:
        """Return real-time health telemetry of the source connection."""
        pass

    @abstractmethod
    async def metadata(self) -> SonarStreamMetadata:
        """Return static or session-level sonar stream metadata."""
        pass

    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the adapter is currently connected to its source."""
        pass
