"""Structured JSON logging with request-ID injection."""

from __future__ import annotations

import json
import logging
import sys
from typing import Any


class _JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        obj: dict[str, Any] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "module": record.module,
            "fn": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            obj["exc"] = self.formatException(record.exc_info)
        # Propagate any extra fields attached to the record
        for key, val in record.__dict__.items():
            if key.startswith("_extra_"):
                obj[key[7:]] = val
        return json.dumps(obj, default=str)


def configure_logging(
    name: str = "app",
    level: int | str = logging.INFO,
) -> logging.Logger:
    """Return a logger emitting JSON to stdout."""
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()
    logger.propagate = False

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_JSONFormatter())
    logger.addHandler(handler)
    return logger
