"""
app/api/health_api.py
GET /health — lightweight liveness probe.

Design decisions:
  - Does NOT make a live call to OpenRouter on every health check.
    A round-trip call would burn rate-limit budget on every liveness probe,
    which is unacceptable given the 20 req/min free-tier cap.
  - Instead, just confirms the API key env var is non-empty (key is present)
    and reports the configured model slug.
"""

from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Service liveness check",
    response_description="Service status and basic configuration info",
)
async def health() -> dict:
    """
    Returns service status.
    - `status`: always 'ok' if the service is running.
    - `model`: the configured OpenRouter model slug.
    - `api_key_configured`: true if OPENROUTER_API_KEY is set (non-empty).
    - `pii_redaction_enabled`: reflects current ENABLE_PII_REDACTION setting.
    """
    return {
        "status": "ok",
        "model": settings.model_slug,
        "api_key_configured": bool(settings.openrouter_api_key),
        "pii_redaction_enabled": settings.enable_pii_redaction,
    }
