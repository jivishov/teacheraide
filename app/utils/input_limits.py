"""Shared input and upload size limits."""

from typing import Tuple


MAX_PDF_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_IMAGE_UPLOAD_BYTES = 3 * 1024 * 1024
MAX_LONG_TEXT_CHARS = 10_000


def exceeds_upload_limit(size_bytes: int, limit_bytes: int) -> bool:
    """Return True when payload size exceeds a byte limit."""
    return int(size_bytes) > int(limit_bytes)


def upload_limit_error(file_label: str, limit_bytes: int) -> str:
    """Build a user-facing upload size error message."""
    limit_mb = int(limit_bytes / (1024 * 1024))
    return f"{file_label} exceeds the {limit_mb}MB limit. Please upload a smaller file."


def enforce_text_limit(value: str, limit_chars: int = MAX_LONG_TEXT_CHARS) -> Tuple[str, bool]:
    """
    Enforce max text length.

    Returns:
        (normalized_text, was_truncated)
    """
    text = value or ""
    if len(text) <= limit_chars:
        return text, False
    return text[:limit_chars], True


def text_limit_error(field_label: str, limit_chars: int = MAX_LONG_TEXT_CHARS) -> str:
    """Build a user-facing text length limit message."""
    return (
        f"{field_label} exceeds the {limit_chars} character limit. "
        "Extra text was removed."
    )
