"""
Logging configuration for endpoint-level files and global error logs.
"""
from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from threading import Lock
from typing import Any

LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
LOG_BACKUP_COUNT = 10

BASE_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
ENDPOINT_LOG_DIR = BASE_LOG_DIR / "endpoints"
ERROR_LOG_DIR = BASE_LOG_DIR / "errors"
SERVICE_LOG_DIR = BASE_LOG_DIR / "services"
INGRESS_LOG_DIR = BASE_LOG_DIR / "ingress"

_ENDPOINT_LOGGERS: dict[str, logging.Logger] = {}
_ERROR_LOGGER: logging.Logger | None = None
_SERVICE_LOGGERS: dict[str, logging.Logger] = {}
_INGRESS_LOGGER: logging.Logger | None = None
_LOGGER_LOCK = Lock()


def _build_null_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Build a logger that silently discards logs."""
    null_logger = logging.getLogger(name)
    null_logger.setLevel(level)
    null_logger.propagate = False
    null_logger.handlers.clear()
    null_logger.addHandler(logging.NullHandler())
    return null_logger


def ensure_log_directories() -> None:
    """Create logs, endpoint logs, and error logs directories if missing."""
    ENDPOINT_LOG_DIR.mkdir(parents=True, exist_ok=True)
    ERROR_LOG_DIR.mkdir(parents=True, exist_ok=True)
    SERVICE_LOG_DIR.mkdir(parents=True, exist_ok=True)
    INGRESS_LOG_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_endpoint_to_filename(path: str, method: str) -> str:
    """Convert request path and method to a stable ASCII log filename."""
    clean_path = path.strip("/") or "root"
    clean_path = clean_path.replace("/", "_").replace("-", "_")
    clean_path = re.sub(r"[^a-zA-Z0-9_]", "_", clean_path)
    clean_path = re.sub(r"_+", "_", clean_path).strip("_") or "root"
    return f"{method.lower()}_{clean_path}.log"


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""

    _SKIP_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key not in self._SKIP_ATTRS and not key.startswith("_"):
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


def _build_rotating_handler(file_path: Path) -> RotatingFileHandler:
    handler = RotatingFileHandler(
        filename=file_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.setFormatter(JsonFormatter())
    return handler


def get_endpoint_logger(method: str, path: str) -> logging.Logger:
    """Get or create endpoint logger for method+path."""
    ensure_log_directories()
    filename = sanitize_endpoint_to_filename(path, method)
    logger_name = f"app.endpoint.{filename[:-4]}"

    with _LOGGER_LOCK:
        if logger_name in _ENDPOINT_LOGGERS:
            return _ENDPOINT_LOGGERS[logger_name]

        endpoint_logger = logging.getLogger(logger_name)
        endpoint_logger.setLevel(logging.INFO)
        endpoint_logger.propagate = False
        endpoint_logger.handlers.clear()
        try:
            endpoint_logger.addHandler(_build_rotating_handler(ENDPOINT_LOG_DIR / filename))
        except OSError:
            # Logging must never break endpoint execution.
            endpoint_logger = _build_null_logger(f"{logger_name}.null", level=logging.INFO)
        _ENDPOINT_LOGGERS[logger_name] = endpoint_logger
        return endpoint_logger


def get_error_logger() -> logging.Logger:
    """Get or create global application error logger."""
    global _ERROR_LOGGER
    ensure_log_directories()

    with _LOGGER_LOCK:
        if _ERROR_LOGGER is not None:
            return _ERROR_LOGGER

        error_logger = logging.getLogger("app.errors")
        error_logger.setLevel(logging.ERROR)
        error_logger.propagate = False
        error_logger.handlers.clear()
        try:
            error_logger.addHandler(_build_rotating_handler(ERROR_LOG_DIR / "app_errors.log"))
        except OSError:
            # Keep app alive even if error log file is temporarily unavailable.
            error_logger = _build_null_logger("app.errors.null", level=logging.ERROR)
        _ERROR_LOGGER = error_logger
        return error_logger


def get_service_logger(service_name: str) -> logging.Logger:
    """Get or create rotating JSON logger for a specific service."""
    ensure_log_directories()
    normalized = re.sub(r"[^a-zA-Z0-9_]", "_", service_name.strip().lower())
    normalized = re.sub(r"_+", "_", normalized).strip("_") or "service"
    logger_name = f"app.service.{normalized}"

    with _LOGGER_LOCK:
        if logger_name in _SERVICE_LOGGERS:
            return _SERVICE_LOGGERS[logger_name]

        service_logger = logging.getLogger(logger_name)
        service_logger.setLevel(logging.INFO)
        service_logger.propagate = False
        service_logger.handlers.clear()
        try:
            service_logger.addHandler(_build_rotating_handler(SERVICE_LOG_DIR / f"{normalized}.log"))
        except OSError:
            service_logger = _build_null_logger(f"{logger_name}.null", level=logging.INFO)
        _SERVICE_LOGGERS[logger_name] = service_logger
        return service_logger


def get_ingress_logger() -> logging.Logger:
    """Get or create global ingress request logger."""
    global _INGRESS_LOGGER
    ensure_log_directories()

    with _LOGGER_LOCK:
        if _INGRESS_LOGGER is not None:
            return _INGRESS_LOGGER

        ingress_logger = logging.getLogger("app.ingress")
        ingress_logger.setLevel(logging.INFO)
        ingress_logger.propagate = False
        ingress_logger.handlers.clear()
        try:
            ingress_logger.addHandler(_build_rotating_handler(INGRESS_LOG_DIR / "requests.log"))
        except OSError:
            ingress_logger = _build_null_logger("app.ingress.null", level=logging.INFO)
        _INGRESS_LOGGER = ingress_logger
        return ingress_logger


def configure_root_logging(debug: bool) -> None:
    """Configure console logging for app runtime."""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO if debug else logging.WARNING)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if debug else logging.WARNING)
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    root_logger.addHandler(console_handler)
