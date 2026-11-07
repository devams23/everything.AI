"""
app/services/text_processing_service.py
Three-stage text pipeline: clean → PII redaction → chunking.

Stages:
  1. clean_text(text)  — normalise whitespace, strip control chars
  2. redact_pii(text)  — regex-based PII masking (toggleable via config)
  3. chunk_text(text)  — token-aware paragraph-boundary splitting
"""

from __future__ import annotations

import re
import unicodedata

import tiktoken

from app.config import settings
from app.services.logger_service import get_logger

log = get_logger(__name__)

_enc = tiktoken.get_encoding("cl100k_base")

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+?1[-.\\s]?)?(?:\(?\d{3}\)?[-.\\s]?)\d{3}[-.\\s]?\d{4}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"), "[REDACTED_CC]"),
]

_PII_CATEGORY_NAMES = ["email", "phone", "ssn", "credit_card"]


def clean_text(text: str) -> str:
    """
    Normalise whitespace and strip non-printable characters.
    - NFKC unicode normalisation
    - Strip control characters (keep \\n and \\t)
    - Collapse repeated spaces/tabs and excess blank lines
    """
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[^\S\n\t ]+", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def redact_pii(text: str) -> tuple[str, dict[str, int]]:
    """
    Scan text for PII patterns and replace matches with labelled tokens.
    Returns (redacted_text, counts_per_category).
    Only counts are logged — actual PII values are never written to logs.
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
        log.info(f"PII redaction complete: {counts}")
    else:
        log.debug("PII scan: no matches found")

    return text, counts


def count_tokens(text: str) -> int:
    """Return an approximate token count using the cl100k_base tokenizer."""
    return len(_enc.encode(text))


def chunk_text(text: str) -> list[str]:
    """
    Split text into chunks that each stay under CHUNK_TOKEN_THRESHOLD.
    Splits on paragraph boundaries; falls back to sentence boundaries for
    oversized paragraphs. Returns [text] unchanged if no chunking needed.
    """
    threshold = settings.chunk_token_threshold
    total_tokens = count_tokens(text)
    log.info(f"Token count: {total_tokens} (threshold: {threshold})")

    if total_tokens <= threshold:
        return [text]

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current_parts: list[str] = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = count_tokens(para)

        if para_tokens > threshold:
            if current_parts:
                chunks.append("\n\n".join(current_parts))
                current_parts = []
                current_tokens = 0
            chunks.extend(_split_paragraph(para, threshold))
            continue

        if current_tokens + para_tokens > threshold:
            chunks.append("\n\n".join(current_parts))
            current_parts = [para]
            current_tokens = para_tokens
        else:
            current_parts.append(para)
            current_tokens += para_tokens

    if current_parts:
        chunks.append("\n\n".join(current_parts))

    log.info(f"Text split into {len(chunks)} chunks")
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
