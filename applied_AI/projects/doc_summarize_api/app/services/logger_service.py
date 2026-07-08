"""
app/services/logger_service.py
Structured JSON logging with per-request correlation via a context variable.

Usage
-----
    from app.services.logger_service import get_logger

    log = get_logger(__name__)
    log.info("upload received", extra={"filename": safe_name, "size_bytes": size})

The RequestIDMiddleware (also defined here) must be registered on the FastAPI
app BEFORE any routes so that every log line carries the same request_id.

Security rules (enforced by caller discipline, not this module):
  - Never pass file contents, PII values, API keys, or raw LLM payloads to `extra`.
  - Log lengths / hashes instead of values when debugging payloads.
"""

from __future__ import annotations

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# ── Context variable ──────────────────────────────────────────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="no-request")


def get_request_id() -> str:
    return _request_id_var.get()


# ── Custom JSON formatter ─────────────────────────────────────────────────────
class _JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "request_id": get_request_id(),
            "message": record.getMessage(),
        }

        # Merge any `extra` fields passed by the caller
        for key, value in record.__dict__.items():
            if key not in {
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "module", "exc_info", "exc_text", "stack_info",
                "lineno", "funcName", "created", "msecs", "relativeCreated",
                "thread", "threadName", "processName", "process", "message",
                "taskName",
            }:
                log_obj[key] = value

        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_obj, default=str)


# ── Logger factory ────────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """
    Return a logger that writes structured JSON to stdout.
    Calling this multiple times with the same name is safe (handlers are
    attached only once).
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(_JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


# ── Request-ID middleware ─────────────────────────────────────────────────────
class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generates a UUID4 request ID for every incoming request and stores it in
    the _request_id_var context variable so all log lines for that request
    share the same ID.

    The ID is also returned in the X-Request-ID response header for
    client-side correlation.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        token = _request_id_var.set(request_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            _request_id_var.reset(token)
