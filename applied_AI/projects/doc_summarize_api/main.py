from __future__ import annotations

import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.health_api import router as health_router
from app.api.summarize_api import router as summarize_router
from app.services.logger_service import RequestIDMiddleware, get_logger

log = get_logger(__name__)

app = FastAPI(
    title="Mini AI Document Summary API",
    version="1.0.0",
    description="Accepts a .txt file and returns a structured summary using meta-llama/llama-3.3-70b-instruct:free via OpenRouter.",
    docs_url="/docs",
)

app.add_middleware(RequestIDMiddleware)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if isinstance(exc.detail, dict):
        content = exc.detail
    else:
        content = {"status": "error", "message": str(exc.detail)}
    return JSONResponse(status_code=exc.status_code, content=content)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Unhandled exception: {type(exc).__name__}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "An unexpected error occurred. Please try again later."},
    )


app.include_router(health_router)
app.include_router(summarize_router)

log.info("Application startup complete")