from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "model": settings.model_slug,
        "api_key_configured": bool(settings.openrouter_api_key),
        "pii_redaction_enabled": settings.enable_pii_redaction,
    }
