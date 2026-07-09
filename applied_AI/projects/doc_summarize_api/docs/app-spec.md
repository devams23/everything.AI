# SPEC: Mini AI Document Summary API (OpenRouter-backed)

## 1. Overview
FastAPI service exposing a single core endpoint that accepts a `.txt` upload, cleans and optionally chunks the text, sends it to an OpenRouter-hosted open-source model for summarization, and returns a structured JSON summary. LLM inference is delegated to OpenRouter's OpenAI-compatible endpoint rather than a locally-hosted model.

## 2. Model & Provider Configuration
* **Model (fixed):** `meta-llama/llama-3.3-70b-instruct:free`
* **Base URL:** `https://openrouter.ai/api/v1` (OpenAI-compatible).
* **Auth:** `Authorization: Bearer <OPENROUTER_API_KEY>` header; key loaded from environment variable, never hardcoded, never logged.
* **Optional attribution headers:** `HTTP-Referer`, `X-OpenRouter-Title`.
* **Context window:** 131K tokens — this is the fixed number chunking threshold, prompt budget, and output cap all derive from.
* **Rate limits:** 20 requests/minute across free models combined; daily cap is 50 (or 1000 if $10+ credits have ever been added to the account). Service must treat HTTP 429 as an expected, handled case.
* **Timeout:** explicit request timeout (30–60s) on every call.
* **Justification:** Established/stable free model, general-purpose instruction-following fit for summarization, open-weight (Llama license), and a 131K context gives comfortable headroom over the 2MB input cap.
* **Data policy note:** Log in README that OpenRouter/providers may retain prompts for free-tier models, justifying the upstream PII redaction step.

## 3. Input Validation (`file_service.py`)
* Reject empty files (0 bytes).
* Reject non-`.txt` extensions — check both extension and a lightweight content-type/MIME sniff.
* Reject files over 2 MB — check `Content-Length` / actual byte size.
* Reject files that decode to non-UTF-8 garbage, or explicitly attempt a fallback decode (e.g., latin-1) and log that a fallback was used.
* Map validation failures to distinct HTTP statuses: 422 for empty/malformed, 415 for wrong extension, 413 for oversized.
* Return the standard `{"status": "error", "message": "..."}` body regardless of status code.

## 4. Text Preprocessing
* **Normalization:** Collapse repeated newlines/spaces and strip control characters / non-printable bytes.
* **Boilerplate Stripping (Optional/Stretch):** Strip obvious boilerplate like page numbers and repeated headers/footers.
* **PII Handling:**
    * Execute a pre-LLM PII scan/redaction pass using a regex-based detector (emails, phone numbers, SSN-like patterns, credit card numbers) before data leaves the machine.
    * Redact or mask matches (e.g., replace with `[REDACTED_EMAIL]`) to preserve document structure while protecting sensitive content.
    * Log that redaction occurred and match counts per category, but never log the actual PII values.
    * Make toggleable via config (`ENABLE_PII_REDACTION=true/false`).

## 5. Chunking & Tokenization (`file_service.py`)
* **Execution Location:** Token-counting and splitting logic belongs entirely inside `file_service.py` (or a dedicated chunking module). The LLM service (`llm_service.py`) should only receive pre-verified, correctly sized chunks and never handle token counting.
* **Token-Aware Splitting:** * Utilize the official Llama 3.3 tokenizer files from Hugging Face to obtain exact token ID counts, avoiding estimations.
    * Walk through the cleaned text paragraph by paragraph (or sentence by sentence).
    * After each addition, run the accumulated chunk-so-far through the Llama tokenizer to check the exact token count against the threshold.
    * Once adding the next segment pushes the token count over the threshold, close the current chunk, start a new one, and continue.
* **Map-Reduce Summarization:** Summarize each verified chunk individually, then run a secondary LLM call to synthesize the per-chunk summaries into a final JSON object (`title`, `summary`, `key_points`). Deduplicate/merge overlapping key points during this synthesis step.

## 6. LLM Interaction (`llm_service.py`)
* **Prompt Design:** System prompt fixes the exact output contract (field names, types, no prose outside JSON). Explicitly instruct: "respond with valid JSON only, no markdown fences, no commentary".
* **Structured Output:** Use provider-side JSON mode / schema constraints if supported by the OpenRouter model, but always validate the returned text through a Pydantic model after parsing.
* **Retry/Repair Logic:** On JSON parse or schema validation failure, issue exactly one repair retry with an explicit follow-up prompt. If that fails, return a clean error response.
* **429 Handling:** On rate-limit response, gracefully fall back to `test_llm_service.py`, which returns a cached valid response without hitting the OpenRouter API to save quota during testing.
* **Parameters:** Cap max output tokens explicitly and set temperature lower than default (e.g., 0.2–0.4) for summarization determinism.

## 7. API Layer (`main.py`)
* `POST /summarize`: Orchestrates validation → PII redaction → cleaning → chunk decision → LLM call(s) → response assembly. This endpoint must remain thin and defer to services for business logic.
* `GET /health`: Returns service status and performs a lightweight check that the OpenRouter API key is present (without making a round-trip call).
* **Data Validation:** Response models defined as Pydantic classes for both success and error shapes.
* **Exception Handling:** A global exception handler catches unhandled errors and returns the standard JSON error shape rather than a raw FastAPI 500 traceback.

## 8. Logging & Observability
* **Structured Logs:** JSON or key=value logs at each pipeline stage (upload received, validation result, PII redaction summary, chunk count, LLM call start/end with latency, final response status).
* **Correlation:** Tie all log lines for one request together via a request ID.
* **Exclusions:** Never log file contents, PII matches, API keys, or full LLM payloads unless gated behind an explicitly disabled debug flag.

## 9. Security Considerations
* **API Key Handling:** Configured via `.env` (excluded via `.gitignore`), loaded via settings object, never logged or returned.
* **Rate Limiting:** Implement an in-memory or middleware-based limiter on the `/summarize` endpoint to prevent a single client from exhausting the OpenRouter quota.
* **Redundant Size Checks:** Enforce file upload size at both the ASGI server config level and the application level.
* **Sanitization:** Sanitize filenames before inclusion in logs or responses to prevent path traversal.

## 10. Testing
* **Unit Tests:** Cover validation edge cases, PII redaction regex matches, chunking boundary logic (using the Llama tokenizer), and Pydantic schema validation of malformed LLM outputs.
* **Mocking:** Mock the OpenRouter call in tests to preserve API quota and allow the test suite to run offline.

## 11. README Contents
* **Setup:** Environment variables (`OPENROUTER_API_KEY`, model slug, PII toggle), install steps, and run commands.
* **Design Decisions:** * Why OpenRouter over local inference (accessibility, hardware constraints, easy model swapping).
    * The trade-off of external API usage (data leaves the machine, necessitating PII redaction and external uptime dependencies).
    * The deliberate architectural choice to utilize the official gated Llama tokenizer files from Hugging Face for mathematically exact token chunking, ensuring robust adherence to the context window rather than relying on library approximations.
* **Known Limitations:** Free-tier model quality ceiling, rate limit behavior under load, and the lack of a persistent job queue (synchronous only).
* **Production Upgrades:** Async job handling for long documents, paid tier/self-hosting for reliability, and advanced NER-based PII detection.