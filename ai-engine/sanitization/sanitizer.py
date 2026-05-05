"""
sanitization/sanitizer.py
=========================
Privacy-first sanitization layer.

All PII (names, phone numbers, UPI IDs, account numbers) is masked
BEFORE any data reaches the extraction or storage layers.

Designed to be drop-in replaceable: swap out regex rules for a
dedicated NER model or OpenClaw's privacy filter in the future.
"""

import re
from typing import NamedTuple


class SanitizationResult(NamedTuple):
    sanitized_text: str
    pii_found: list[str]  # categories of PII that were detected


# ──────────────────────────────────────────────────────────────────────────────
# Regex patterns (ordered by specificity — more specific first)
# ──────────────────────────────────────────────────────────────────────────────

# UPI ID: user@bank or user.name@upi (case-insensitive)
_UPI_PATTERN = re.compile(
    r"\b[a-zA-Z0-9.\-_+]{2,}@[a-zA-Z]{2,}\b"
)

# Indian mobile: 10 digits starting with 6-9, optionally prefixed with +91 / 0
_PHONE_PATTERN = re.compile(
    r"(?:\+91|91|0)?[\s\-]?[6-9]\d{9}\b"
)

# Account numbers: 9-18 consecutive digits (not inside a date/amount context)
# We match only standalone digit sequences that look like account numbers
_ACCOUNT_PATTERN = re.compile(
    r"(?<!\d)(?<!\.)(?<!\/)(\d{9,18})(?!\d)(?!\.)(?!\/)"
)

# Names: Very heuristic — capitalised words preceded by "paid by", "from",
# "received from", "to", "hi", "dear" etc.
_NAME_CONTEXT_PATTERN = re.compile(
    r"(?:paid\s+by|from|received\s+from|to|hi|dear|sender|payee|payer)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3})",
    re.IGNORECASE,
)

# Email addresses
_EMAIL_PATTERN = re.compile(
    r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b"
)

# IFSC codes (for bank routing — 11 chars, first 4 alpha + 0 + 6 alphanum)
_IFSC_PATTERN = re.compile(
    r"\b[A-Z]{4}0[A-Z0-9]{6}\b"
)


def sanitize(raw_text: str) -> SanitizationResult:
    """
    Remove or mask all detected PII from raw_text.

    Returns the cleaned text and a list of PII categories found.
    The sanitized text is what flows into extraction — never the raw input.

    Replacement strategy:
      - UPI IDs   → [UPI_ID]
      - Phones    → [PHONE]
      - Accounts  → [ACCOUNT]
      - Names     → [NAME]
      - Emails    → [EMAIL]
      - IFSC      → [IFSC]
    """
    text = raw_text
    pii_found: list[str] = []

    # 1. UPI IDs (before phone/email so @-patterns don't conflict)
    if _UPI_PATTERN.search(text):
        pii_found.append("upi_id")
        text = _UPI_PATTERN.sub("[UPI_ID]", text)

    # 2. Email (generic, after UPI so UPI-specific ones are already masked)
    if _EMAIL_PATTERN.search(text):
        pii_found.append("email")
        text = _EMAIL_PATTERN.sub("[EMAIL]", text)

    # 3. Phone numbers
    if _PHONE_PATTERN.search(text):
        pii_found.append("phone")
        text = _PHONE_PATTERN.sub("[PHONE]", text)

    # 4. IFSC codes
    if _IFSC_PATTERN.search(text):
        pii_found.append("ifsc")
        text = _IFSC_PATTERN.sub("[IFSC]", text)

    # 5. Account numbers (must come after phone to avoid partial overlap)
    if _ACCOUNT_PATTERN.search(text):
        pii_found.append("account_number")
        text = _ACCOUNT_PATTERN.sub("[ACCOUNT]", text)

    # 6. Names (context-based heuristic — lowest confidence, last pass)
    if _NAME_CONTEXT_PATTERN.search(text):
        pii_found.append("name")
        def _replace_name(m: re.Match) -> str:
            # Keep the context keyword, replace only the captured name
            return m.group(0).replace(m.group(1), "[NAME]")
        text = _NAME_CONTEXT_PATTERN.sub(_replace_name, text)

    return SanitizationResult(sanitized_text=text, pii_found=pii_found)
