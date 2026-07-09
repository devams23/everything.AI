"""
app/services/llm_service/openrouter_llm_service.py
OpenRouter LLM client for document summarisation.

- Sends structured prompts to OpenRouter's OpenAI-compatible endpoint.
- Validates response into a SummaryDetail Pydantic model.
- On parse failure: one repair retry before raising LLMParseError.
- On HTTP 429: raises RateLimitError for the caller to handle.
- summarize_chunks(): map-reduce for long documents (per-chunk + synthesis).
"""

from __future__ import annotations

import time
import json
import re
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import settings
from app.models.response_models import SummaryDetail
from app.services.llm_service.base_llm_service import BaseLLMService, LLMParseError, RateLimitError
from app.services.logger_service import get_logger

log = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are a precise document summarisation assistant.
Your ONLY output must be a single valid JSON object — no markdown fences, \
no code blocks, no commentary, no prose before or after the JSON.

The JSON object must have exactly these three keys:
  "title"      : string — a short, descriptive title for the document
  "summary"    : string — a concise paragraph summarising the document
  "key_points" : array of strings — the most important points (3-7 items)

Example of correct output:
{"title":"...","summary":"...","key_points":["...","...","..."]}
"""

_REPAIR_PROMPT = (
    "Your previous response was not valid JSON or did not match the required schema. "
    "Respond with ONLY a valid JSON object matching this exact schema:\n"
    '{"title": string, "summary": string, "key_points": [string, ...]}\n'
    "No markdown, no code fences, no explanation — JSON only."
)

_SYNTHESIS_SYSTEM_PROMPT = """\
You are a document summarisation assistant performing a synthesis step.
You will receive several partial summaries of sections of a longer document.
Produce ONE unified summary that covers the whole document.

Rules:
  - Deduplicate overlapping key points — do not repeat similar items.
  - Write a single coherent summary paragraph, not a concatenation.
  - Output ONLY valid JSON, no markdown, no code fences, no commentary.

Required JSON schema:
{"title": string, "summary": string, "key_points": [string, ...]}
"""


class OpenRouterLLMService(BaseLLMService):
    """Calls OpenRouter's OpenAI-compatible chat completions endpoint."""

    def __init__(self) -> None:
        self._base_url = settings.openrouter_base_url.rstrip("/")
        self._model = settings.model_slug
        self._timeout = httpx.Timeout(settings.llm_timeout_seconds)
        self._headers: dict[str, str] = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
        }
        if settings.http_referer:
            self._headers["HTTP-Referer"] = settings.http_referer
        if settings.x_openrouter_title:
            self._headers["X-OpenRouter-Title"] = settings.x_openrouter_title

    async def summarize(self, text: str) -> SummaryDetail:
        """Summarise a single text chunk."""
        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": f"Document to summarise:\n\n{text}"},
        ]
        return await self._call_with_retry(messages)

    async def summarize_chunks(self, chunks: list[str]) -> SummaryDetail:
        """
        Map-reduce summarisation for multi-chunk documents.
        Phase 1 — summarise each chunk individually.
        Phase 2 — synthesise all per-chunk summaries into one final summary.
        """
        log.info(f"Map-reduce: summarising {len(chunks)} chunks")

        partial_summaries: list[SummaryDetail] = []
        for idx, chunk in enumerate(chunks, start=1):
            log.info(f"Summarising chunk {idx}/{len(chunks)}")
            partial = await self.summarize(chunk)
            partial_summaries.append(partial)

        log.info("Synthesising chunk summaries")
        messages = [
            {"role": "system", "content": _SYNTHESIS_SYSTEM_PROMPT},
            {"role": "user", "content": self._format_partials(partial_summaries)},
        ]
        return await self._call_with_retry(messages)

    async def _call_with_retry(self, messages: list[dict[str, str]]) -> SummaryDetail:
        """
        Make one LLM call; on parse/schema failure issue one repair retry.
        Raises LLMParseError if both attempts fail.
        Raises RateLimitError on HTTP 429.
        """
        raw_response = await self._chat_completion(messages)

        try:
            return self._parse(raw_response)
        except (LLMParseError, ValidationError) as err:
            log.warning(f"LLM response invalid, attempting repair: {err}")

        repair_messages = messages + [
            {"role": "assistant", "content": raw_response},
            {"role": "user", "content": _REPAIR_PROMPT},
        ]
        repaired_response = await self._chat_completion(repair_messages)

        try:
            return self._parse(repaired_response)
        except (LLMParseError, ValidationError) as err:
            log.error(f"LLM repair attempt also failed: {err}")
            raise LLMParseError(
                "LLM returned invalid JSON after one repair attempt."
            ) from err

    async def _chat_completion(self, messages: list[dict[str, str]]) -> str:
        """
        POST to the OpenRouter chat completions endpoint.
        Returns the raw assistant message string.
        Raises RateLimitError on 429.
        """
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": settings.llm_temperature,
            "max_tokens": settings.llm_max_output_tokens,
            "response_format": {"type": "json_object"},
        }

        log.info(f"LLM call start — model: {self._model}, messages: {len(messages)}")
        t0 = time.perf_counter()

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions",
                headers=self._headers,
                json=payload,
            )

        latency_ms = int((time.perf_counter() - t0) * 1000)

        if response.status_code == 429:
            log.warning("OpenRouter rate limit hit (HTTP 429)")
            raise RateLimitError("OpenRouter returned HTTP 429 — rate limited")

        response.raise_for_status()

        data = response.json()
        log.info(f"LLM call complete <==DATA==> {data}")

        content: str = data["choices"][0]["message"]["content"]

        log.info(f"LLM call complete — latency: {latency_ms}ms, response length: {len(content)}")
        return content

    def _parse(self, raw: str) -> SummaryDetail:
        """Parse a raw LLM response string into a SummaryDetail."""
        raw = raw.strip()
        if raw.startswith("```"):
            raw = re.sub(r"^```[a-z]*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise LLMParseError(f"JSON parse error: {exc}") from exc

        return SummaryDetail.model_validate(data)

    @staticmethod
    def _format_partials(partials: list[SummaryDetail]) -> str:
        """Format per-chunk summaries as a numbered list for the synthesis prompt."""
        lines = ["Below are summaries of individual sections of a longer document:\n"]
        for i, p in enumerate(partials, start=1):
            lines.append(f"--- Section {i} ---")
            lines.append(f"Title: {p.title}")
            lines.append(f"Summary: {p.summary}")
            lines.append("Key points:")
            for kp in p.key_points:
                lines.append(f"  - {kp}")
            lines.append("")
        lines.append("Produce a single unified summary of the WHOLE document.")
        return "\n".join(lines)
