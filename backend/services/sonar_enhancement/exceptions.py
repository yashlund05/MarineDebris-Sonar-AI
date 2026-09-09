"""
Custom structured domain exceptions for the Sonar Enhancement pipeline.
Ensures informative, user-facing error reporting without raw Python tracebacks.
"""

from typing import Optional, Dict, Any


class SonarEnhancementError(Exception):
    """Base exception for all sonar enhancement errors."""
    def __init__(self, message: str, error_code: str = "ENHANCEMENT_FAILED", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class UnsupportedFormatError(SonarEnhancementError):
    """Raised when an unparseable or unsupported file format is provided."""
    def __init__(self, format_name: str, supported: list):
        super().__init__(
            message=f"Unsupported sonar format '{format_name}'. Supported formats: {', '.join(supported)}.",
            error_code="UNSUPPORTED_FORMAT",
            details={"format": format_name, "supported_formats": supported},
        )


class MetadataMissingError(SonarEnhancementError):
    """Raised when an operation requiring physical sonar metadata (altitude/angles) lacks metadata."""
    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Operation '{operation}' cannot be performed: {reason}",
            error_code="METADATA_MISSING",
            details={"operation": operation, "reason": reason},
        )


class CorruptImageError(SonarEnhancementError):
    """Raised when an image payload cannot be decoded or has 0 bytes."""
    def __init__(self, filename: str, reason: str = "Image payload is corrupt or unreadable"):
        super().__init__(
            message=f"Failed to decode image '{filename}': {reason}",
            error_code="CORRUPT_IMAGE",
            details={"filename": filename, "reason": reason},
        )


class ProcessingTimeoutError(SonarEnhancementError):
    """Raised when processing exceeds the maximum execution deadline."""
    def __init__(self, duration_ms: float, timeout_ms: float):
        super().__init__(
            message=f"Processing timed out after {duration_ms:.1f}ms (limit: {timeout_ms:.1f}ms)",
            error_code="PROCESSING_TIMEOUT",
            details={"duration_ms": duration_ms, "timeout_ms": timeout_ms},
        )
