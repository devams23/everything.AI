# Mini AI Document Summary API — Implementation Plan

Brief: Build a FastAPI service that accepts a `.txt` file upload, validates it, preprocesses the text (including PII redaction), optionally chunks it, sends it to `meta-llama/llama-3.3-70b-instruct:free` via OpenRouter, and returns a structured JSON summary. All skeleton files exist but are currently empty stubs.

---


## Proposed Changes

Build order follows dependency graph: config → logger → models → file_service → text_processing_service → llm_service/* → api/* → main.py → requirements.txt → README.md.

---

### 1. Configuration (`app/config.py`) — [NEW]

#### [NEW] [config.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/config.py)

A `pydantic-settings` `BaseSettings` class that loads from `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `OPENROUTER_API_KEY` | — (required) | Bearer token for OpenRouter |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Base URL |
| `MODEL_SLUG` | `meta-llama/llama-3.3-70b-instruct:free` | Model identifier |
| `ENABLE_PII_REDACTION` | `true` | Toggle PII pass |
| `MAX_FILE_SIZE_MB` | `2` | Upload cap |
| `CHUNK_TOKEN_THRESHOLD` | `100000` | Tokens before chunking triggers |
| `LLM_TIMEOUT_SECONDS` | `45` | HTTP timeout per call |
| `LLM_MAX_OUTPUT_TOKENS` | `1024` | Cap on generated tokens |
| `LLM_TEMPERATURE` | `0.3` | Low temp for determinism |
| `RATE_LIMIT_RPM` | `10` | Per-client rate limit on `/summarize` |
| `HTTP_REFERER` | `""` | Optional OpenRouter attribution header |
| `X_OPENROUTER_TITLE` | `""` | Optional OpenRouter attribution header |

---

### 2. Logging (`app/services/logger_service.py`) — [MODIFY]

#### [MODIFY] [logger_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/logger_service.py)

- Structured JSON logger using Python `logging` + `python-json-logger` (or stdlib with `json` formatter).
- `get_logger(name)` factory that attaches a `request_id` context var via `contextvars.ContextVar`.
- A `RequestIDMiddleware` (Starlette `BaseHTTPMiddleware`) that sets a UUID4 `request_id` per request and injects it into the context var.
- **Never logs**: file contents, PII values, API key, full prompts/responses.

---

### 3. Pydantic Response Models (`app/models/`) — [NEW files]

#### [NEW] [app/models/\_\_init\_\_.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/models/__init__.py)

#### [NEW] [app/models/response_models.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/models/response_models.py)

```python
class SummaryDetail(BaseModel):
    title: str
    summary: str
    key_points: list[str]

class SuccessResponse(BaseModel):
    status: Literal["success"]
    filename: str
    summary: SummaryDetail

class ErrorResponse(BaseModel):
    status: Literal["error"]
    message: str
```

---

### 4. File Validation Service (`app/services/file_service.py`) — [MODIFY]

#### [MODIFY] [file_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/file_service.py)

`validate_upload(file: UploadFile) -> bytes` — raises `HTTPException` with correct status codes:

| Condition | HTTP Status | Message |
|---|---|---|
| Wrong extension | `415` | `"Only .txt files are allowed"` |
| Wrong MIME (content sniff) | `415` | `"File content does not match .txt format"` |
| Empty file (0 bytes) | `422` | `"File must not be empty"` |
| Over 2 MB | `413` | `"File size must not exceed 2 MB"` |
| Non-UTF-8 (no latin-1 fallback) | `422` | `"File must be valid text (UTF-8)"` |
| latin-1 fallback used | logs a warning, proceeds | — |

Also sanitizes the uploaded filename before any log/response use (strips path traversal chars).

---

### 5. Text Processing Service (`app/services/text_processing_service.py`) — [MODIFY]

#### [MODIFY] [text_processing_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/text_processing_service.py)

Three logical sections:

**A. Cleaning** (`clean_text(text: str) -> str`)
- Collapse repeated newlines/spaces (regex).
- Strip non-printable / control characters (keep `\n`, `\t`).
- Strip obvious page-number patterns (stretch, marked with `# STRETCH` comment).

**B. PII Redaction** (`redact_pii(text: str) -> tuple[str, dict[str, int]]`)
- Regex patterns for: email, US phone, SSN-like (`\d{3}-\d{2}-\d{4}`), credit card (Luhn-group pattern).
- Returns redacted text + count-per-category dict (logged, never the values).
- Respects `ENABLE_PII_REDACTION` config flag — if `false`, returns text unchanged.
- Replacements: `[REDACTED_EMAIL]`, `[REDACTED_PHONE]`, `[REDACTED_SSN]`, `[REDACTED_CC]`.

**C. Chunking** (`chunk_text(text: str) -> list[str]`)
- Approximate token count via `tiktoken` (`cl100k_base` encoding — close enough for Llama 3 token accounting).
- If total tokens ≤ `CHUNK_TOKEN_THRESHOLD` → return `[text]` (no chunking).
- Otherwise split on paragraph boundaries (`\n\n`) accumulating into chunks that stay under threshold.
- Never splits mid-sentence where paragraph boundaries exist.

---

### 6. LLM Service Layer (`app/services/llm_service/`) — [MODIFY all 3 files]

#### [MODIFY] [base_llm_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/llm_service/base_llm_service.py)

Abstract base class:
```python
class BaseLLMService(ABC):
    @abstractmethod
    async def summarize(self, text: str) -> SummaryDetail: ...
```

#### [MODIFY] [openrouter_llm_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/llm_service/openrouter_llm_service.py)

`OpenRouterLLMService(BaseLLMService)`:
- Uses `httpx.AsyncClient` (not `openai` SDK, to avoid heavy dep) with `Authorization: Bearer` header.
- **Prompt design**: system prompt locks output to pure JSON `{"title": "...", "summary": "...", "key_points": [...]}` — no markdown fences, no commentary.
- **Structured output**: sets `response_format: {"type": "json_object"}` in the request body.
- **Validation**: parses response → `SummaryDetail` Pydantic model.
- **Retry/repair**: on parse/validation failure → one repair call with explicit schema reminder. If that fails → raises `LLMParseError`.
- **429 handling**: raises `RateLimitError` — caller (`summarize_api.py`) catches and delegates to `TestLLMService`.
- **Map-reduce**: `summarize_chunks(chunks: list[str]) -> SummaryDetail`:
  - Phase 1: call `summarize()` on each chunk (sequential to respect rate limits).
  - Phase 2: single synthesis call that merges per-chunk summaries, deduplicates key_points.
- Temperature `0.3`, max output tokens from config, explicit `timeout` on every `httpx` call.

#### [MODIFY] [test_llm_service.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/services/llm_service/test_llm_service.py)

`TestLLMService(BaseLLMService)`:
- Returns a **hardcoded** `SummaryDetail` — no network call, no API key needed.
- Used as the 429 fallback during testing to avoid burning quota.
- Logs that the cached fallback was used.

---

### 7. API Routes (`app/api/`) — [MODIFY both files]

#### [MODIFY] [summarize_api.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/api/summarize_api.py)

`POST /summarize` — thin orchestrator:
1. `validate_upload(file)` → raw bytes + safe filename
2. `clean_text(text)`
3. `redact_pii(text)` if enabled → log redaction summary
4. `chunk_text(text)` → decide single vs map-reduce
5. `llm_service.summarize()` or `llm_service.summarize_chunks()` — catch `RateLimitError` → fallback to `TestLLMService`
6. Return `SuccessResponse`

In-memory rate limiting via `slowapi` (or a simple `collections.deque` + `asyncio.Lock` counter) keyed by client IP — rejects with `429` if over `RATE_LIMIT_RPM` before hitting OpenRouter.

#### [MODIFY] [health_api.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/app/api/health_api.py)

`GET /health`:
- Returns `{"status": "ok", "model": MODEL_SLUG, "api_key_configured": bool(API_KEY)}`.
- **No live OpenRouter call** — just checks that the key env var is non-empty.

---

### 8. Application Entry Point (`main.py`) — [MODIFY]

#### [MODIFY] [main.py](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/main.py)

- Create `FastAPI` app with title, version, description.
- Register `RequestIDMiddleware`.
- Register global exception handler → always returns `ErrorResponse` JSON shape.
- Include routers from `summarize_api` and `health_api`.
- Add upload size guard at ASGI level (`ContentSizeLimitMiddleware` or equivalent) as a second enforcement layer.

---

### 9. Dependencies (`requirements.txt`) — [MODIFY]

#### [MODIFY] [requirements.txt](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/requirements.txt)

Packages to **add** (pinned):

| Package | Purpose |
|---|---|
| `tiktoken` | Token counting for chunking |
| `python-json-logger` | Structured JSON logging |
| `slowapi` | Per-client rate limiting middleware |

> [!NOTE]
> `httpx`, `pydantic-settings`, `python-dotenv` are already in `requirements.txt` — no duplicates needed.

---

### 10. README (`README.md`) — [MODIFY]

#### [MODIFY] [README.md](file:///d:/everything_ai/everything.AI/applied_AI/projects/doc_summarize_api/README.md)

Sections per spec §11:
- **Setup**: env vars, `pip install -r requirements.txt`, `uvicorn main:app --reload`
- **Env vars reference table**
- **Design decisions**: OpenRouter vs local inference, tradeoffs, PII redaction rationale
- **Data policy notice**: free-tier models may log prompts
- **Known limitations**: rate limits, no job queue, free model quality ceiling
- **Production roadmap**: async jobs, paid tier fallback, NER-based PII detection

---

## File Change Summary

| File | Status | Key Work |
|---|---|---|
| `app/config.py` | **NEW** | Pydantic `BaseSettings` |
| `app/models/__init__.py` | **NEW** | package init |
| `app/models/response_models.py` | **NEW** | `SuccessResponse`, `ErrorResponse`, `SummaryDetail` |
| `app/services/logger_service.py` | **MODIFY** | JSON structured logger + request-ID middleware |
| `app/services/file_service.py` | **MODIFY** | Full validation with distinct HTTP codes |
| `app/services/text_processing_service.py` | **MODIFY** | Cleaning + PII redaction + chunking |
| `app/services/llm_service/base_llm_service.py` | **MODIFY** | Abstract base |
| `app/services/llm_service/openrouter_llm_service.py` | **MODIFY** | OpenRouter client + map-reduce + retry/repair |
| `app/services/llm_service/test_llm_service.py` | **MODIFY** | Cached fallback for 429 / testing |
| `app/api/summarize_api.py` | **MODIFY** | `POST /summarize` orchestration + rate limit |
| `app/api/health_api.py` | **MODIFY** | `GET /health` |
| `main.py` | **MODIFY** | App factory, middleware, global error handler |
| `requirements.txt` | **MODIFY** | Add `tiktoken`, `python-json-logger`, `slowapi` |
| `README.md` | **MODIFY** | Full spec §11 content |
| `.env.example` | **NEW** | Template for required env vars |

---

## Verification Plan

### Automated smoke tests (manual run, no pytest required unless you confirm)
```bash
# Start server
uvicorn main:app --reload

# Health check
curl http://localhost:8000/health

# Happy path
curl -X POST http://localhost:8000/summarize -F "file=@sample.txt"

# Wrong extension → 415
curl -X POST http://localhost:8000/summarize -F "file=@sample.pdf"

# Empty file → 422
curl -X POST http://localhost:8000/summarize -F "file=@empty.txt"

# Oversized → 413 (need a >2MB file)
```

### Manual checks
- Confirm `request_id` appears in all log lines for a single request.
- Confirm PII strings are replaced (not logged) when `ENABLE_PII_REDACTION=true`.
- Confirm API key never appears in any log output or response body.
- Confirm 429 fallback returns a valid `SuccessResponse` (not an error).
