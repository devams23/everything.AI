"""
app/services/llm_service/test_llm_service.py
Hardcoded fallback LLM service used when:
  1. OpenRouter returns HTTP 429 (rate limited) — avoids burning quota.
  2. During local testing without a live API key.

The cached response is intentionally generic so it is always structurally
valid regardless of the actual document content.  Callers are informed via
a structured log entry that this fallback was used.
"""

from __future__ import annotations

from app.models.response_models import SummaryDetail
from app.services.llm_service.base_llm_service import BaseLLMService
from app.services.logger_service import get_logger

log = get_logger(__name__)

# ── Cached payload ────────────────────────────────────────────────────────────
_CACHED_SUMMARY = SummaryDetail(
    title="Document Summary (Cached — Rate Limit Fallback)",
    summary=(
        "The live summarisation service is temporarily unavailable due to "
        "upstream rate limiting. This is a cached placeholder response. "
        "Please retry the request in a moment to obtain a real summary."
    ),
    key_points=[
        "Live summarisation was rate-limited by the upstream provider (HTTP 429).",
        "This cached response is returned to maintain API contract compliance.",
        "Retry the /summarize endpoint after a short delay to get a real summary.",
    ],
)


class TestLLMService(BaseLLMService):
    """
    Returns a hardcoded SummaryDetail without making any network calls.
    Used as the 429 fallback and for offline testing.
    """

    async def summarize(self, text: str) -> SummaryDetail:
        log.warning(
            "TestLLMService used — returning cached fallback response",
            extra={"reason": "rate_limit_fallback_or_test_mode"},
        )
        return _CACHED_SUMMARY
