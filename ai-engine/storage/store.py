"""
storage/store.py
================
In-memory storage layer.

Stores ONLY structured, PII-free transaction data keyed by user_id.
Raw input text is NEVER stored.

Architecture note:
  Replace `_store` (dict) with a Firebase/Firestore client to persist
  across sessions. The `save()` and `get_results()` function signatures
  stay identical — only the implementation changes.
"""

import time
from collections import defaultdict
from typing import Any

from extraction.extractor import Transaction
from validation.validator import ValidationError


# ──────────────────────────────────────────────────────────────────────────────
# In-memory store
# Key: user_id (str)
# Value: list of session records
# ──────────────────────────────────────────────────────────────────────────────

_store: dict[str, list[dict]] = defaultdict(list)


def save(
    user_id: str,
    transactions: list[Transaction],
    summary: dict,
    validation_errors: list[ValidationError],
) -> None:
    """
    Persist a processed document result for user_id.

    Only structured fields are stored — no raw text, no PII.
    """
    record = {
        "timestamp": time.time(),
        "transactions": [t.model_dump() for t in transactions],
        "summary": summary,
        "validation_errors": [e.model_dump() for e in validation_errors],
    }
    _store[user_id].append(record)


def get_results(user_id: str) -> list[dict]:
    """
    Retrieve all stored processing results for a user.

    Returns an empty list if no results exist for this user_id.
    """
    return _store.get(user_id, [])


def all_users() -> list[str]:
    """List all user_ids that have stored data (admin use only)."""
    return list(_store.keys())


def clear_user(user_id: str) -> None:
    """Remove all stored data for a user (e.g., on account deletion)."""
    _store.pop(user_id, None)
