SPEC: Mini AI Document Summary API (OpenRouter-backed)

## 1. Overview
FastAPI service exposing a single core endpoint that accepts a .txt upload, cleans and optionally chunks the text, sends it to an OpenRouter-hosted open-source model for summarization, and returns a structured JSON summary. LLM inference is delegated to OpenRouter's OpenAI-compatible endpoint rather than a locally-hosted model.

## 2. Model & Provider Configuration
Model (fixed): meta-llama/llama-3.3-70b-instruct:free
Base URL: https://openrouter.ai/api/v1 (OpenAI-compatible).
Auth: Authorization: Bearer <OPENROUTER_API_KEY> header, key loaded from environment variable, never hardcoded, never logged.
Optional attribution headers: HTTP-Referer, X-OpenRouter-Title.
Context window: 131K tokens — this is the fixed number  chunking threshold, prompt budget, and output cap all derive from.
Rate limits: 20 requests/minute across free models combined; daily cap is 50 (or 1000 if $10+ credits have ever been added to the account). Service must treat HTTP 429 as an expected, handled case.
Timeout: explicit request timeout (30–60s) on every call.
Justification (for README): established/stable free model (live since Dec 2024, unlikely to be pulled mid-grading), general-purpose instruction-following fit for summarization (not a coding/agentic-specialized model), open-weight (Llama license), 131K context gives comfortable headroom over the 2MB input cap.
Data policy note: log in README that OpenRouter/providers may retain prompts for free-tier models — this is the stated reason for the PII redaction step upstream.

## 3. Input Validation (`file_service.py`)
- Reject empty files (0 bytes).
- Reject non-`.txt` extensions — check both extension and, ideally, a lightweight content-type/MIME sniff, since extension alone is spoofable.
- Reject files over 2 MB — check `Content-Length` / actual byte size, not just trust the client.
- Reject files that decode to non-UTF-8 garbage, or explicitly attempt a fallback decode (e.g. latin-1) and log that a fallback was used.
- Each validation failure maps to a distinct HTTP status: 422 for empty/malformed, 415 for wrong extension, 413 for oversized.
- Return the standard `{"status": "error", "message": "..."}` body regardless of status code.

## 4. Text Preprocessing
- Whitespace normalization (collapse repeated newlines/spaces).
- Strip control characters / non-printable bytes.
- Optional: strip obvious boilerplate (page numbers, repeated headers/footers) if present — mention this as a stretch item, not core.
- **PII handling (advanced addition, not in the original doc):**
  - Add a pre-LLM PII scan/redaction pass using a regex-based detector at minimum (emails, phone numbers, SSN-like patterns, credit card numbers) before the text is sent to the third-party OpenRouter endpoint.
  - This matters specifically *because* you're now sending data to an external API rather than a fully local model — data leaves  machine. Flag in the README that free OpenRouter models may log prompts/completions for provider-side improvement, so PII exposure is a real, not hypothetical, concern.
  - Redact or mask matches (e.g. replace with `[REDACTED_EMAIL]`) rather than silently dropping — preserves document structure for summarization while protecting sensitive content.
  - Log *that* redaction occurred and how many matches per category — never log the actual PII values.
  - Make this toggleable via config (`ENABLE_PII_REDACTION=true/false`) so you can demo both states.

## 5. Chunking
- Chunk only if token count exceeds a configured threshold (derive threshold from the chosen model's context window, leaving headroom for prompt template + expected output tokens — e.g. if context is 128K, don't casually assume you can use all of it; leave a comfortable margin).
- Use a token-aware splitter (approximate via a tokenizer library, not naive character count) so chunk boundaries respect the model's actual token accounting.
- Preserve paragraph boundaries where possible — don't split mid-sentence if avoidable.
- Map-reduce summarization: summarize each chunk individually, then run a second LLM call that synthesizes the per-chunk summaries into one final `title` / `summary` / `key_points` object. Deduplicate/merge overlapping key points at the synthesis step rather than concatenating raw lists.

## 6. LLM Interaction (`llm_service.py`)
- Prompt design: system prompt fixes the exact output contract (field names, types, no prose outside JSON). Explicitly instruct "respond with valid JSON only, no markdown fences, no commentary."
- Structured output enforcement:
  - If the chosen model/provider supports OpenAI-style `response_format: json_object` or JSON schema constraints via OpenRouter, use it — check the specific model's tool/structured-output support first, since not all OpenRouter models support this equally well.
  - Regardless, still validate the returned text through a Pydantic model after parsing — treat provider-side JSON mode as a strong hint, not a guarantee.
- Retry/repair logic: on JSON parse failure or schema validation failure, issue exactly one repair retry with an explicit " last response was invalid JSON, return only valid JSON matching this schema" follow-up. If that also fails, return a clean error response rather than surfacing a raw parse exception.
- 429 handling: on rate-limit response, run a different fallback llm call, for now i have a test_llm_service.py that directly returns the response so call this, and assume that this is an llm call only but i have the response cached in the test file, so you can call this and get a valid response without hitting the OpenRouter API. This is to avoid burning  quota during testing.

- Cap max output tokens explicitly in the request — don't rely on model defaults.
- Temperature: lower than default (e.g. 0.2–0.4) for summarization determinism; state this choice explicitly rather than using conversational defaults.

## 7. API Layer (`main.py`)
- `POST /summarize`: orchestrates validation → PII redaction → cleaning → chunk decision → LLM call(s) → response assembly. Keep this endpoint thin — it should call into services, not contain business logic itself.
- `GET /health`: returns service status; optionally also do a lightweight check that the OpenRouter API key is present/valid (not a full round-trip call on every health check — that would burn rate limit budget for a liveness probe).
- Response models defined as Pydantic classes for both success and error shapes, matching the doc's exact JSON structure.
- Exception handling: a global exception handler that catches unhandled errors and still returns the standard `{"status": "error", "message": "..."}` shape rather than a raw FastAPI 500 traceback.

## 8. Logging & Observability
- Structured logs (JSON or key=value) at each pipeline stage: upload received, validation result, PII redaction summary, chunk count, LLM call start/end with latency, final response status.
- Correlate all log lines for one request via a request ID.
- Never log: file contents, PII matches, API key, full LLM prompts/responses (log lengths/hashes instead if you need to debug, or gate full-payload logging behind a debug flag that's off by default).

## 9. Security Considerations (advanced, not in original doc)
- API key handling: `.env` file excluded via `.gitignore`, loaded via a settings/config object, never committed, never returned in any response or error message.
- Rate limiting  own `/summarize` endpoint (not just relying on OpenRouter's limits) — a simple in-memory or middleware-based limiter, to avoid a single client exhausting  daily OpenRouter quota.
- File upload size enforced at two levels: reverse-proxy/ASGI server config (if applicable) and application-level check, since relying on only one is fragile.
- Sanitize filenames before including them in logs or responses (avoid path traversal characters ending up in log output).

## 10. Testing (mention even though not explicit in original doc)
- Unit tests for: validation edge cases (empty, oversized, wrong extension), PII redaction regex matches, chunking boundary logic, Pydantic schema validation of malformed LLM output.
- Mock the OpenRouter call in tests — don't burn real API quota / require network access for the test suite to pass.

## 11. README Contents
- Setup: env vars needed (`OPENROUTER_API_KEY`, model slug, PII toggle), install steps, run command.
- Design decisions section: why OpenRouter over local inference (accessibility, no local hardware constraint, easy model swapping) vs. the tradeoff (data leaves the machine, hence the PII redaction step, plus dependency on an external service's uptime/rate limits).
- Known limitations: free-tier model quality ceiling, rate limit behavior under load, no persistent job queue (synchronous request/response only).
- What you'd change for production: async job handling for long documents, paid tier or self-hosted fallback for reliability, more robust PII detection (NER-based, not just regex).