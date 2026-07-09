"""
app/services/llm_service/base_llm_service.py
Abstract base class for all LLM service implementations.

Any concrete service (OpenRouter, test/mock, future alternatives) must
implement the `summarize` method.  The map-reduce coordinator lives in
OpenRouterLLMService because it issues the real LLM calls, but the base
contract is intentionally minimal so test/mock implementations remain simple.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models.response_models import SummaryDetail


class BaseLLMService(ABC):
    """Minimal contract every LLM backend must satisfy."""

    @abstractmethod
    async def summarize(self, text: str) -> SummaryDetail:
        """
        Summarise `text` and return a structured SummaryDetail.

        Parameters
        ----------
        text:
            Pre-processed, (optionally PII-redacted) text ready for the LLM.

        Returns
        -------
        SummaryDetail with title, summary, and key_points.

        Raises
        ------
        LLMParseError  — if the LLM response cannot be parsed/validated after
                         one repair attempt.
        RateLimitError — if the provider returns HTTP 429.
        """


# ── Custom exceptions ─────────────────────────────────────────────────────────
class LLMParseError(Exception):
    """Raised when the LLM response cannot be parsed into SummaryDetail."""


class RateLimitError(Exception):
    """Raised when the upstream provider returns HTTP 429 (rate limited)."""
