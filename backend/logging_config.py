"""Structured logging configuration for the backend application."""

import logging
import sys
from typing import Any, Dict


def setup_logging(debug: bool = False) -> None:
    """Configure structured logging for standard library and structlog."""
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
        level=log_level,
        stream=sys.stdout,
        force=True,
    )
    # Quiet overly noisy external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)


def get_logger(name: str = "marine_debris_sonar") -> logging.Logger:
    """Return configured logger instance."""
    return logging.getLogger(name)
