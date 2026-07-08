"""
app/services/text_processing_service.py
Three-stage text pipeline: clean → PII redaction → chunking.

Stages
------
1. clean_text(text)     — normalise whitespace, strip control chars
2. redact_pii(text)     — regex-based PII masking (toggleable via config)
3. chunk_text(text)     — token-aware paragraph-boundary splitting

Security / privacy notes:
  - Actual PII values are NEVER logged; only per-category match counts are.
  - Redaction is done BEFORE the text is sent to OpenRouter, because free-tier
    providers may log prompts for model improvement.
"""

from __future__ import annotations

import re
import unicodedata

import tiktoken

from app.config import settings
from app.services.logger_service import get_logger

log = get_logger(__name__)

# ── Tokenizer (approximation — cl100k_base is close for Llama 3) ──────────────
_enc = tiktoken.get_encoding("cl100k_base")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Cleaning
# ─────────────────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    """
    Normalise whitespace and strip non-printable characters.

    Steps:
      - NFKC unicode normalisation (collapse look-alikes)
      - Strip control characters (keep \\n and \\t as semantic whitespace)
      - Collapse runs of spaces/tabs to a single space
      - Collapse runs of 3+ blank lines to 2 blank lines (paragraph breaks)
      - Strip leading/trailing whitespace
    """
    # Unicode normalisation
    text = unicodedata.normalize("NFKC", text)

    # Remove control characters except newline (0x0A) and tab (0x09)
    text = re.sub(r"[^\S\n\t ]+", " ", text)  # non-newline invisible whitespace → space
    text = "".join(
        ch for ch in text
        if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t")
    )

    # Collapse multiple spaces/tabs on a single line
    text = re.sub(r"[ \t]+", " ", text)

    # Collapse 3+ consecutive blank lines to 2 (preserve paragraph structure)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ─────────────────────────────────────────────────────────────────────────────
# 2. PII Redaction
# ─────────────────────────────────────────────────────────────────────────────
# Pattern → replacement token
_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # Email addresses
    (
        re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    # US phone numbers (various formats)
    (
        re.compile(
            r"\b(?:\+?1[-.\s]?)?"
            r"(?:\(?\d{3}\)?[-.\s]?)"
            r"\d{3}[-.\s]?\d{4}\b"
        ),
        "[REDACTED_PHONE]",
    ),
    # SSN-like patterns (NNN-NN-NNNN)
    (
        re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
        "[REDACTED_SSN]",
    ),
    # Credit card numbers (groups of 4 digits, with common separators)
    (
        re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
        "[REDACTED_CC]",
    ),
]

_PII_CATEGORY_NAMES = ["email", "phone", "ssn", "credit_card"]


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """
    Scan `text` for PII patterns and replace matches with labelled tokens.

    Returns
    -------
    (redacted_text, counts)
        counts is a dict mapping category name → number of redactions made.
        Log counts (never the matched values) after calling this function.

    Behaviour
    ---------
    - When ENABLE_PII_REDACTION=false the text is returned unchanged and
      counts will be empty.
    - Matches are replaced (not deleted) to preserve document structure for
      the summarisation prompt.
    """
    if not settings.enable_pii_redaction:
        log.debug("PII redaction disabled via config")
        return text, {}

    counts: dict[str, int] = {}
    for (pattern, replacement), name in zip(_PII_PATTERNS, _PII_CATEGORY_NAMES):
        matches = pattern.findall(text)
        if matches:
            counts[name] = len(matches)
            text = pattern.sub(replacement, text)

    if counts:
        log.info(
            "PII redaction complete",
            extra={"redaction_counts": counts},  # counts only — no actual values
        )
    else:
        log.debug("PII scan complete: no matches found")

    return text, counts


# ─────────────────────────────────────────────────────────────────────────────
# 3. Chunking
# ─────────────────────────────────────────────────────────────────────────────
def count_tokens(text: str) -> int:
    """Return an approximate token count using the cl100k_base tokenizer."""
    return len(_enc.encode(text))


def chunk_text(text: str) -> list[str]:
    """
    Split `text` into chunks that each stay under CHUNK_TOKEN_THRESHOLD.

    Strategy
    --------
    - If total tokens ≤ threshold → return [text] (single chunk, no LLM overhead).
    - Otherwise split on paragraph boundaries (\\n\\n), accumulating paragraphs
      into chunks. A paragraph that alone exceeds the threshold is split at
      sentence boundaries as a last resort (no mid-sentence splits).

    Returns
    -------
    List of text chunks.  Each chunk is a standalone piece of text suitable
    for direct LLM summarisation.
    """
    threshold = settings.chunk_token_threshold

    total_tokens = count_tokens(text)
    log.info("token count computed", extra={"total_tokens": total_tokens, "threshold": threshold})

    if total_tokens <= threshold:
        log.debug("text fits in single chunk — no splitting required")
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        # Paragraph alone exceeds threshold — split at sentence boundaries
        if para_tokens > threshold:
            # Flush whatever we have first
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0
            chunks.extend(_split_paragraph(para, threshold))
            continue

        if current_tokens + para_tokens > threshold:
            # Start a new chunk
            chunks.append("\n\n".join(current_parts))
            current_parts = [para]
            current_tokens = para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    log.info("text split into chunks", extra={"chunk_count": len(chunks)})
    return chunks


def _split_paragraph(para: str, threshold: int) -> list[str]:
    """Split an oversized paragraph at sentence boundaries."""
    sentences = re.split(r"(?<=[.!?])\s+", para)
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for sent in sentences:
        sent_tokens = count_tokens(sent)
        if current_tokens + sent_tokens > threshold:
            if current_parts:
                chunks.append(" ".join(current_parts))
            current_parts = [sent]
            current_tokens = sent_tokens
        else:
            current_parts.append(sent)
            current_tokens += sent_tokens

    if current_parts:
        chunks.append(" ".join(current_parts))

    return chunks
