"""
app/api/summarize_api.py
POST /summarize — thin orchestration layer.

Pipeline (in order)
-------------------
1. validate_upload()       — file_service:  extension, size, encoding
2. clean_text()            — text_processing_service: whitespace / control chars
3. redact_pii()            — text_processing_service: email/phone/SSN/CC masking
4. chunk_text()            — text_processing_service: token-aware splitting
5. LLM call(s)             — OpenRouterLLMService (single or map-reduce)
6. RateLimitError fallback — TestLLMService (cached response, no quota burn)
7. Return SuccessResponse

Rate limiting
-------------
slowapi limits this endpoint to RATE_LIMIT_PER_MINUTE requests per client IP,
enforced BEFORE the OpenRouter call to protect the daily quota.

This module contains NO business logic — every non-trivial step is delegated
to a service module.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, UploadFile
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings
from app.models.response_models import SuccessResponse
from app.services.file_service import validate_upload
from app.services.llm_service.base_llm_service import RateLimitError
from app.services.llm_service.openrouter_llm_service import OpenRouterLLMService
from app.services.llm_service.test_llm_service import TestLLMService
from app.services.logger_service import get_logger
from app.services.text_processing_service import chunk_text, clean_text, redact_pii

log = get_logger(__name__)

# ── Rate limiter instance ─────────────────────────────────────────────────────
# The Limiter is created here; it will be attached to the FastAPI app in main.py.
limiter = Limiter(key_func=get_remote_address)

router = APIRouter(tags=["Summarize"])

# ── Service instances (module-level singletons) ───────────────────────────────
_openrouter_svc = OpenRouterLLMService()
_test_svc = TestLLMService()


@router.post(
    "/summarize",
    response_model=SuccessResponse,
    summary="Summarise a .txt document using an LLM",
    response_description="Structured summary with title, summary, and key points",
)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def summarize(request: Request, file: UploadFile) -> SuccessResponse:
    """
    Upload a `.txt` file and receive a structured AI-generated summary.

    **Validation rules:**
    - File must have `.txt` extension (415 if wrong type)
    - File must not be empty (422 if empty)
    - File must not exceed 2 MB (413 if too large)
    - File must be valid text (UTF-8 or latin-1)

    **Processing:**
    - Text is cleaned (whitespace, control chars)
    - PII is redacted before sending to the external LLM (if enabled)
    - Long documents are automatically chunked and map-reduce summarised
    """
    # ── Step 1: Validate upload ───────────────────────────────────────────────
    raw_bytes, safe_filename = await validate_upload(file)
    text = raw_bytes.decode("utf-8", errors="replace")

    # ── Step 2: Clean ─────────────────────────────────────────────────────────
    cleaned = clean_text(text)
    log.info("text cleaned", extra={"original_len": len(text), "cleaned_len": len(cleaned)})

    # ── Step 3: PII redaction ─────────────────────────────────────────────────
    redacted, pii_counts = redact_pii(cleaned)
    if pii_counts:
        log.info("PII redacted before LLM call", extra={"counts": pii_counts})

    # ── Step 4: Chunk ─────────────────────────────────────────────────────────
    chunks = chunk_text(redacted)
    use_map_reduce = len(chunks) > 1
    log.info(
        "chunking complete",
        extra={"chunk_count": len(chunks), "map_reduce": use_map_reduce},
    )

    # ── Step 5 & 6: LLM call with 429 fallback ───────────────────────────────
    try:
        if use_map_reduce:
            summary_detail = await _openrouter_svc.summarize_chunks(chunks)
        else:
            summary_detail = await _openrouter_svc.summarize(redacted)

    except RateLimitError:
        log.warning(
            "OpenRouter rate limited — falling back to TestLLMService",
            extra={"filename": safe_filename},
        )
        summary_detail = await _test_svc.summarize(redacted)

    # ── Step 7: Return structured response ────────────────────────────────────
    log.info("summarisation complete", extra={"filename": safe_filename})
    return SuccessResponse(filename=safe_filename, summary=summary_detail)
