"""Structured logging configuration for KnowledgeOps services."""

import logging
import sys
from typing import Any

from shared.config import BaseServiceSettings


def configure_logging(settings: BaseServiceSettings) -> logging.Logger:
    """Configure structured logging for a service.

    Args:
        settings: Service configuration with log_level and log_format.

    Returns:
        Configured logger instance for the calling service.
    """
    logger = logging.getLogger("knowledgeops")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JsonFormatter() if settings.log_format == "json" else logging.Formatter("%(message)s"))
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


class _JsonFormatter(logging.Formatter):
    """Minimal JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, Any] = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "service": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1] is not None:
            data["exception"] = self.formatException(record.exc_info)
        return str(data)
