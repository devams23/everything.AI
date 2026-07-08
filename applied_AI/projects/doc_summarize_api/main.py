"""
main.py
FastAPI application factory.

Registers (in order):
  1. RequestIDMiddleware  — per-request UUID correlation for all log lines
  2. ContentSizeLimitMiddleware — ASGI-level upload size cap (second enforcement
     layer; file_service.py is the first layer)
  3. SlowAPI state / 429 handler  — per-client rate limiting on /summarize
  4. Global exception handler  — catches ANY unhandled error and returns the
     standard {"status": "error", "message": "..."} body instead of a raw 500
  5. HTTPException handler  — ensures FastAPI HTTPExceptions also use the
     standard error body shape (not FastAPI's default {"detail": ...} wrapper)
  6. Routers  — health and summarize
"""

from __future__ import annotations

import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.health_api import router as health_router
from app.api.summarize_api import limiter, router as summarize_router
from app.services.logger_service import RequestIDMiddleware, get_logger

log = get_logger(__name__)

# ── App instance ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Mini AI Document Summary API",
    version="1.0.0",
    description=(
        "Accepts a .txt file, preprocesses the text (including optional PII "
        "redaction), and returns a structured summary using "
        "meta-llama/llama-3.3-70b-instruct:free via OpenRouter."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters — outermost registered last) ────────────────────

# 1. Request ID — must be first so every subsequent log carries the request_id
app.add_middleware(RequestIDMiddleware)

# 2. ASGI-level content size limit (second enforcement layer after file_service)
from app.config import settings  # noqa: E402

_MAX_UPLOAD_BYTES = settings.max_file_size_mb * 1024 * 1024


class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests whose Content-Length exceeds the upload cap."""

    async def dispatch(self, request: Request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > _MAX_UPLOAD_BYTES:
            return JSONResponse(
                status_code=413,
                content={"status": "error", "message": f"File size must not exceed {settings.max_file_size_mb} MB"},
            )
        return await call_next(request)


app.add_middleware(ContentSizeLimitMiddleware)

# 3. SlowAPI rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"status": "error", "message": "Too many requests — please slow down and retry."},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Normalise FastAPI HTTPExceptions to the standard error body shape.
    file_service raises HTTPException(detail={"status": "error", ...}),
    so we pass detail through if it's already a dict.
    """
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"status": "error", "message": str(exc.detail)}

    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all: ensures unhandled exceptions return the standard error shape
    rather than a raw FastAPI 500 traceback.
    Never includes exception details in the response (security).
    """
    log.error(
        "unhandled exception",
        extra={
            "exc_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected error occurred. Please try again later.",
        },
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(summarize_router)

log.info("application startup complete", extra={"version": "1.0.0"})