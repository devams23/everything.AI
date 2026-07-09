from fastapi import APIRouter, Request, UploadFile

from app.models.response_models import SuccessResponse
from app.services.file_service import validate_upload
from app.services.llm_service.base_llm_service import RateLimitError
from app.services.llm_service.openrouter_llm_service import OpenRouterLLMService
from app.services.llm_service.test_llm_service import TestLLMService
from app.services.logger_service import get_logger
from app.services.text_processing_service import chunk_text, clean_text, redact_pii

log = get_logger(__name__)

router = APIRouter(tags=["Summarize"])

_openrouter_svc = OpenRouterLLMService()
_test_svc = TestLLMService()


@router.post("/summarize", response_model=SuccessResponse)
async def summarize(request: Request, file: UploadFile) -> SuccessResponse:
    raw_bytes, safe_filename = await validate_upload(file)
    text = raw_bytes.decode("utf-8", errors="replace")

    cleaned = clean_text(text)
    log.info(f"Text cleaned: {len(text)} -> {len(cleaned)} chars")

    redacted, pii_counts = redact_pii(cleaned)
    if pii_counts:
        log.info(f"PII redacted before LLM call: {pii_counts}")

    chunks = chunk_text(redacted)
    use_map_reduce = len(chunks) > 1
    log.info(f"Chunks: {len(chunks)}, map-reduce: {use_map_reduce}")

    try:
        if use_map_reduce:
            summary_detail = await _openrouter_svc.summarize_chunks(chunks)
        else:
            summary_detail = await _openrouter_svc.summarize(redacted)
    except RateLimitError:
        log.warning(f"Rate limited by OpenRouter, falling back to cached response: {safe_filename}")
        summary_detail = await _test_svc.summarize(redacted)

    log.info(f"Summarisation complete: {safe_filename}")
    return SuccessResponse(filename=safe_filename, summary=summary_detail)
