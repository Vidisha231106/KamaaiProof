"""
validation/validator.py
=======================
Validation layer — runs after extraction, before storage.

Rules enforced:
  1. amount must be present and > 0
  2. date must be present and valid ISO 8601
  3. date must not be in the future
  4. transaction_type must be one of the allowed values

Validation errors are returned as structured objects, NOT raised as
exceptions, so the pipeline never crashes on bad data.
"""

from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

from extraction.extractor import Transaction


# ──────────────────────────────────────────────────────────────────────────────
# Validation error schema
# ──────────────────────────────────────────────────────────────────────────────

class ValidationError(BaseModel):
    transaction_id: str
    field: str        # which field failed
    message: str      # human-readable description
    severity: str     # "error" | "warning"


ALLOWED_TX_TYPES = {"credit", "debit", "unknown"}
TODAY = date.today()


def validate(transaction: Transaction) -> list[ValidationError]:
    """
    Validate a single extracted transaction.

    Returns a (possibly empty) list of ValidationError objects.
    An empty list means the transaction passed all checks.
    """
    errors: list[ValidationError] = []
    tid = transaction.id

    # ── Rule 1: Amount must exist and be positive ──────────────────────────
    if transaction.amount is None:
        errors.append(ValidationError(
            transaction_id=tid,
            field="amount",
            message="Amount could not be extracted from document.",
            severity="error",
        ))
    elif transaction.amount <= 0:
        errors.append(ValidationError(
            transaction_id=tid,
            field="amount",
            message=f"Amount must be > 0. Got: {transaction.amount}",
            severity="error",
        ))

    # ── Rule 2: Date must exist ────────────────────────────────────────────
    if transaction.date is None:
        errors.append(ValidationError(
            transaction_id=tid,
            field="date",
            message="Date could not be extracted from document.",
            severity="warning",  # warning, not error — date-less records still useful
        ))
    else:
        # ── Rule 3: Date must not be in the future ─────────────────────────
        try:
            parsed_date = date.fromisoformat(transaction.date)
            if parsed_date > TODAY:
                errors.append(ValidationError(
                    transaction_id=tid,
                    field="date",
                    message=(
                        f"Date {transaction.date} is in the future. "
                        "Future-dated transactions are flagged for review."
                    ),
                    severity="error",
                ))
        except ValueError:
            errors.append(ValidationError(
                transaction_id=tid,
                field="date",
                message=f"Date '{transaction.date}' is not valid ISO 8601.",
                severity="error",
            ))

    # ── Rule 4: Transaction type must be known ─────────────────────────────
    if transaction.transaction_type not in ALLOWED_TX_TYPES:
        errors.append(ValidationError(
            transaction_id=tid,
            field="transaction_type",
            message=(
                f"Unknown transaction type: '{transaction.transaction_type}'. "
                f"Expected one of {ALLOWED_TX_TYPES}."
            ),
            severity="warning",
        ))

    # ── Rule 5: Low confidence warning ────────────────────────────────────
    if transaction.confidence < 0.4:
        errors.append(ValidationError(
            transaction_id=tid,
            field="confidence",
            message=(
                f"Extraction confidence is low ({transaction.confidence:.2f}). "
                "Manual review recommended."
            ),
            severity="warning",
        ))

    return errors
