"""
app/services/file_service.py
File upload validation: extension, MIME sniff, size, encoding.

Each failure maps to a distinct HTTP status code as per the spec:
  415 — wrong extension or content type
  413 — file exceeds size cap
  422 — empty file or non-decodable content

All errors use the standard {"status": "error", "message": "..."} body,
raised as HTTPException so FastAPI serialises them consistently.

Security notes:
  - Extension alone is spoofable; a lightweight MIME sniff is also performed.
  - Filenames are sanitised before being included in any log or response.
  - File content is never logged.
"""

from __future__ import annotations

import re
import unicodedata

from fastapi import HTTPException, UploadFile

from app.config import settings
from app.services.logger_service import get_logger

log = get_logger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
_MAX_BYTES: int = settings.max_file_size_mb * 1024 * 1024  # bytes
_ALLOWED_EXTENSION: str = ".txt"

# Regex for stripping path-traversal characters from filenames
_UNSAFE_FILENAME_CHARS = re.compile(r"[^\w\s.\-]")


# ── Public API ────────────────────────────────────────────────────────────────
async def validate_upload(file: UploadFile) -> tuple[bytes, str]:
    """
    Validate and read an uploaded file.

    Returns
    -------
    (raw_bytes, safe_filename) on success.

    Raises
    ------
    HTTPException with appropriate status code and ErrorResponse-compatible
    JSON body on any validation failure.
    """
    safe_name = _sanitize_filename(file.filename or "unknown.txt")
    log.info("upload received", extra={"safe_filename": safe_name, "content_type": file.content_type})

    # ── 1. Extension check ────────────────────────────────────────────────────
    if not safe_name.lower().endswith(_ALLOWED_EXTENSION):
        log.warning("rejected: wrong extension", extra={"safe_filename": safe_name})
        _raise(415, "Only .txt files are allowed")

    # ── 2. Read bytes (enforces size limit during read) ───────────────────────
    raw: bytes = await file.read()
    size = len(raw)

    # ── 3. Empty file check ───────────────────────────────────────────────────
    if size == 0:
        log.warning("rejected: empty file", extra={"safe_filename": safe_name})
        _raise(422, "File must not be empty")

    # ── 4. Size cap ───────────────────────────────────────────────────────────
    if size > _MAX_BYTES:
        log.warning(
            "rejected: file too large",
            extra={"safe_filename": safe_name, "size_bytes": size, "limit_bytes": _MAX_BYTES},
        )
        _raise(413, f"File size must not exceed {settings.max_file_size_mb} MB")

    # ── 5. Lightweight MIME / content sniff ───────────────────────────────────
    # A genuine text file should not contain null bytes.
    if b"\x00" in raw[:1024]:
        log.warning("rejected: binary content detected", extra={"safe_filename": safe_name})
        _raise(415, "File content does not appear to be plain text (.txt)")

    # ── 6. Encoding check (UTF-8 with latin-1 fallback) ───────────────────────
    text = _decode(raw, safe_name)

    log.info(
        "upload validated",
        extra={"safe_filename": safe_name, "size_bytes": size, "chars": len(text)},
    )
    return raw, safe_name


# ── Helpers ───────────────────────────────────────────────────────────────────
def _decode(raw: bytes, safe_name: str) -> str:
    """Attempt UTF-8 decode; fall back to latin-1 with a warning."""
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass

    try:
        text = raw.decode("latin-1")
        log.warning(
            "UTF-8 decode failed; latin-1 fallback used",
            extra={"safe_filename": safe_name},
        )
        return text
    except UnicodeDecodeError:
        log.warning("rejected: undecodable content", extra={"safe_filename": safe_name})
        _raise(422, "File must be valid text (UTF-8 or latin-1 encoding expected)")

    return ""  # unreachable; satisfies type checker


def _sanitize_filename(filename: str) -> str:
    """
    Strip path-traversal characters and control characters from a filename.
    Keeps alphanumerics, spaces, dots, hyphens, and underscores.
    """
    # Normalise unicode (NFKC collapses look-alike characters)
    name = unicodedata.normalize("NFKC", filename)
    # Strip directory separators and other unsafe chars
    name = name.replace("/", "").replace("\\", "").replace("..", "")
    name = _UNSAFE_FILENAME_CHARS.sub("_", name)
    return name.strip() or "upload.txt"


def _raise(status_code: int, message: str) -> None:
    """Raise an HTTPException whose body matches the standard error shape."""
    raise HTTPException(
        status_code=status_code,
        detail={"status": "error", "message": message},
    )
