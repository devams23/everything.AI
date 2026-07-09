"""
app/services/file_service.py
File upload validation: extension, MIME sniff, size, encoding.

Each failure maps to a distinct HTTP status code:
  415 — wrong extension or binary content
  413 — file exceeds size cap
  422 — empty file or undecodable content
"""

from __future__ import annotations

import re
import unicodedata

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.logger_service import get_logger

log = get_logger(__name__)

_MAX_BYTES: int = settings.max_file_size_mb * 1024 * 1024
_ALLOWED_EXTENSION: str = ".txt"
_UNSAFE_FILENAME_CHARS = re.compile(r"[^\w\s.\-]")


async def validate_upload(file: UploadFile) -> tuple[bytes, str]:
    """
    Validate and read an uploaded file.
    Returns (raw_bytes, safe_filename) on success.
    Raises HTTPException with appropriate status code on failure.
    """
    safe_name = _sanitize_filename(file.filename or "unknown.txt")
    log.info(f"Upload received: {safe_name}")

    if not safe_name.lower().endswith(_ALLOWED_EXTENSION):
        log.warning(f"Rejected — wrong extension: {safe_name}")
        _raise(415, "Only .txt files are allowed")

    raw: bytes = await file.read()
    size = len(raw)

    if size == 0:
        log.warning(f"Rejected — empty file: {safe_name}")
        _raise(422, "File must not be empty")

    if size > _MAX_BYTES:
        log.warning(f"Rejected — file too large: {safe_name} ({size} bytes)")
        _raise(413, f"File size must not exceed {settings.max_file_size_mb} MB")

    if b"\x00" in raw[:1024]:
        log.warning(f"Rejected — binary content detected: {safe_name}")
        _raise(415, "File content does not appear to be plain text (.txt)")

    text = _decode(raw, safe_name)

    log.info(f"Upload validated: {safe_name} ({size} bytes, {len(text)} chars)")
    return raw, safe_name


def _decode(raw: bytes, safe_name: str) -> str:
    """Attempt UTF-8 decode; fall back to latin-1 with a warning."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    try:
        text = raw.decode("latin-1")
        log.warning(f"UTF-8 decode failed, latin-1 fallback used: {safe_name}")
        return text
    except UnicodeDecodeError:
        log.warning(f"Rejected — undecodable content: {safe_name}")
        _raise(422, "File must be valid text (UTF-8 or latin-1 encoding expected)")

    return ""


def _sanitize_filename(filename: str) -> str:
    """Strip path-traversal characters from a filename."""
    name = unicodedata.normalize("NFKC", filename)
    name = name.replace("/", "").replace("\\", "").replace("..", "")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name)
    return name.strip() or "upload.txt"


def _raise(status_code: int, message: str) -> None:
    raise HTTPException(
        status_code=status_code,
        detail={"status": "error", "message": message},
    )
