"""Custom application exceptions and error codes conforming to API_SPEC.md."""

from typing import Any, Dict, Optional


class AppException(Exception):
    """Base exception for all application errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An internal server error occurred."

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class ValidationError(AppException):
    """Request payload or parameter validation error."""

    status_code: int = 400
    error_code: str = "VALIDATION_ERROR"
    message: str = "Request validation failed."


class NotFoundError(AppException):
    """Resource does not exist."""

    status_code: int = 404
    error_code: str = "NOT_FOUND"
    message: str = "Requested resource was not found."


class SurveyNotFoundError(NotFoundError):
    """Specific survey not found."""

    def __init__(self, survey_id: Any) -> None:
        super().__init__(
            message=f"Survey with ID '{survey_id}' not found.",
            details={"survey_id": str(survey_id)},
        )


class DetectionNotFoundError(NotFoundError):
    """Specific detection not found."""

    def __init__(self, detection_id: Any) -> None:
        super().__init__(
            message=f"Detection with ID '{detection_id}' not found.",
            details={"detection_id": str(detection_id)},
        )


class JobNotFoundError(NotFoundError):
    """Specific processing job not found."""

    def __init__(self, job_id: Any) -> None:
        super().__init__(
            message=f"Processing job with ID '{job_id}' not found.",
            details={"job_id": str(job_id)},
        )


class ConflictError(AppException):
    """Resource already exists or state conflict."""

    status_code: int = 409
    error_code: str = "CONFLICT"
    message: str = "Resource conflict."


class FileTooLargeError(AppException):
    """Uploaded file exceeds configured maximum limit."""

    status_code: int = 413
    error_code: str = "FILE_TOO_LARGE"
    message: str = "File size exceeds the allowed limit."


class UnsupportedFileTypeError(AppException):
    """Uploaded file type or MIME type is not supported."""

    status_code: int = 415
    error_code: str = "UNSUPPORTED_FILE_TYPE"
    message: str = "Unsupported file type."


class UnprocessableEntityError(AppException):
    """Semantically invalid input."""

    status_code: int = 422
    error_code: str = "UNPROCESSABLE_ENTITY"
    message: str = "Unprocessable entity."


class WorkerUnavailableError(AppException):
    """Celery background worker is not reachable."""

    status_code: int = 503
    error_code: str = "WORKER_UNAVAILABLE"
    message: str = "Background processing worker is currently unavailable."
