"""
FactoryOS Structured Logging
==============================
Configures the Python logging stack for the application.

Development  → HumanFormatter: colorized, aligned, readable in a terminal.
Staging/Prod → JSONFormatter: machine-parseable JSON for Cloud Logging / Datadog.

Usage:
    import logging
    logger = logging.getLogger(__name__)

    logger.info("Incident created", extra={"incident_id": "INC-001", "severity": "HIGH"})
    # In production, `incident_id` and `severity` appear as top-level JSON fields,
    # making them searchable and filterable in any log management system.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# Fields that are internal to LogRecord and should not be forwarded
# as extra fields in JSON output.
_LOG_RECORD_INTERNAL_FIELDS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "id", "levelname", "levelno", "lineno", "module", "msecs",
    "message", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class JSONFormatter(logging.Formatter):
    """
    Formats log records as single-line JSON objects.

    Required for structured log ingestion by Cloud Logging, Datadog, Splunk, etc.
    Each log line is independently parseable — no multi-line log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Core fields present on every log line.
        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Forward any `extra={}` fields passed to the logger call.
        # These become first-class searchable fields in Cloud Logging.
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_INTERNAL_FIELDS:
                log_entry[key] = value

        # Include exception traceback as a string field, not a raw object.
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, default=str)


class HumanFormatter(logging.Formatter):
    """
    Human-readable formatter for local development.

    Produces colorized, aligned output optimized for terminal readability.
    Not suitable for production — use JSONFormatter instead.
    """

    _LEVEL_COLORS: dict[str, str] = {
        "DEBUG":    "\033[36m",   # Cyan
        "INFO":     "\033[32m",   # Green
        "WARNING":  "\033[33m",   # Yellow
        "ERROR":    "\033[31m",   # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    _RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self._LEVEL_COLORS.get(record.levelname, "")
        level = f"{color}{record.levelname:<8}{self._RESET}"
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        message = record.getMessage()

        # Append exception info on a new line if present.
        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return f"{timestamp} | {level} | {record.name:<40} | {message}"


def configure_logging(
    environment: str = "development",
    log_level: str = "INFO",
) -> None:
    """
    Configure the root logger for the application.

    Called once during application startup (inside the FastAPI lifespan context).
    Safe to call multiple times — clears existing handlers before adding new ones.

    Args:
        environment: Application environment name. Non-development environments
                     produce JSON log output.
        log_level:   Minimum log level. Must be a valid Python level name.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)

    if environment == "development":
        handler.setFormatter(HumanFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root = logging.getLogger()
    root.setLevel(numeric_level)

    # Clear existing handlers to prevent duplicate output if called more than once.
    root.handlers.clear()
    root.addHandler(handler)

    # ── Suppress noisy third-party loggers ───────────────────
    # These loggers produce significant volume at their default levels.
    # We surface them only at WARNING or above — genuine problems, not routine traffic.
    _suppress: dict[str, int] = {
        "uvicorn.access":   logging.WARNING,   # Access log — too verbose for most debugging
        "sqlalchemy.engine": logging.WARNING,  # SQL query log — enable DEBUG temporarily when needed
        "sqlalchemy.pool":  logging.WARNING,   # Connection pool events
        "asyncio":          logging.WARNING,   # Internal asyncio machinery
    }
    for logger_name, level in _suppress.items():
        logging.getLogger(logger_name).setLevel(level)
