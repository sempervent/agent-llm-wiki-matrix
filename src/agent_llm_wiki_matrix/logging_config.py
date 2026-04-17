"""Structured logging configuration (structlog + stdlib)."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

import structlog


def configure_logging(level_name: str | None = None) -> None:
    """Configure structlog and stdlib logging for CLI and pipelines."""
    raw = (level_name or os.environ.get("ALWM_LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, raw, logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stderr, level=level)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger."""
    return structlog.get_logger(name)
