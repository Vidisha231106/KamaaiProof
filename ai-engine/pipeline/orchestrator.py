"""
pipeline/orchestrator.py
========================
Master pipeline orchestrator.

Execution order:
  Input → Sanitize → Extract → Validate → Store → Index (Retrieval)

Each step is a discrete function call — easy to test, swap, or disable.
The pipeline never raises uncaught exceptions; errors are captured in
the returned validation_errors list.

Architecture note:
  To add an OpenClaw step, insert it between Extract and Validate:
    ... → Extract → OpenClaw_Enrich → Validate → ...
"""

import statistics
from datetime import date

from sanitization.sanitizer import sanitize
from extraction.extractor import extract, Transaction
from validation.validator import validate, ValidationError
import storage.store as store
import retrieval.vector_store as vector_store


# ──────────────────────────────────────────────────────────────────────────────
# Summary builder
# ──────────────────────────────────────────────────────────────────────────────

def _build_summary(transactions: list[Transaction], user_id: str) -> dict:
    """
    Compute a high-level summary from a list of transactions.

    Matches the frontend-expected shape:
      consistencyScore, totalIncome, months, flags
    """
    credit_txns = [t for t in transactions if t.transaction_type == "credit" and t.amount]
    debit_txns  = [t for t in transactions if t.transaction_type == "debit" and t.amount]

    total_income = sum(t.amount for t in credit_txns)
    total_spend  = sum(t.amount for t in debit_txns)

    # Months with at least one credit transaction
    months: set[str] = set()
    for t in credit_txns:
        if t.date:
            months.add(t.date[:7])  # YYYY-MM

    # Consistency score: proportion of transactions with both amount + date
    complete = [t for t in transactions if t.amount and t.date]
    consistency_score = (
        int(len(complete) / len(transactions) * 100) if transactions else 0
    )

    # Average confidence
    confidences = [t.confidence for t in transactions]
    avg_confidence = round(statistics.mean(confidences), 2) if confidences else 0.0

    # Plain-language flags
    flags: list[str] = []
    low_conf = [t for t in transactions if t.confidence < 0.4]
    if low_conf:
        flags.append(
            f"{len(low_conf)} transaction(s) have low extraction confidence and need review."
        )
    unknown_type = [t for t in transactions if t.transaction_type == "unknown"]
    if unknown_type:
        flags.append(
            f"{len(unknown_type)} transaction(s) could not be classified as credit or debit."
        )
    if not months:
        flags.append("No dated credit transactions found — income period cannot be determined.")

    return {
        "user_id": user_id,
        "total_income": round(total_income, 2),
        "total_spend": round(total_spend, 2),
        "consistency_score": consistency_score,
        "months": sorted(months),
        "transaction_count": len(transactions),
        "avg_confidence": avg_confidence,
        "flags": flags,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ──────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    user_id: str,
    document_type: str,
    raw_content: str,
) -> dict:
    """
    Execute the full AI pipeline for a single document submission.

    Steps
    -----
    1. Sanitize  — strip PII from raw_content
    2. Extract   — parse structured fields from sanitized text
    3. Validate  — apply business rules, collect errors
    4. Store     — persist structured result (no raw text)
    5. Index     — embed sanitized summary into vector store

    Returns
    -------
    dict with keys: transactions, summary, validation_errors
    """

    # ── Step 1: Sanitize ──────────────────────────────────────────────────
    san_result = sanitize(raw_content)
    sanitized_text = san_result.sanitized_text
    # pii_found is logged here but NOT returned to the API caller
    pii_categories = san_result.pii_found

    # ── Step 2: Extract ───────────────────────────────────────────────────
    transaction: Transaction = extract(sanitized_text, document_type)

    # ── Step 3: Validate ──────────────────────────────────────────────────
    errors: list[ValidationError] = validate(transaction)

    # ── Step 4: Build summary ─────────────────────────────────────────────
    summary = _build_summary([transaction], user_id)

    # ── Step 5: Store (structured only — no raw text) ────────────────────
    store.save(user_id, [transaction], summary, errors)

    # ── Step 6: Index summary into vector store ───────────────────────────
    summary_text = (
        f"{document_type} | amount={transaction.amount} | "
        f"date={transaction.date} | type={transaction.transaction_type}"
    )
    vector_store.index_summary(
        user_id=user_id,
        summary_text=summary_text,
        metadata={"doc_type": document_type, "confidence": transaction.confidence},
    )

    return {
        "transactions": [transaction.model_dump()],
        "summary": summary,
        "validation_errors": [e.model_dump() for e in errors],
    }


def run_pipeline_batch(
    user_id: str,
    documents: list[dict],  # list of {"document_type": ..., "content": ...}
) -> dict:
    """
    Process multiple documents for one user in sequence.

    Aggregates transactions and summaries across all documents.
    Useful when frontend sends multiple files at once.
    """
    all_transactions: list[Transaction] = []
    all_errors: list[ValidationError] = []

    for doc in documents:
        san_result = sanitize(doc["content"])
        txn = extract(san_result.sanitized_text, doc["document_type"])
        errors = validate(txn)
        all_transactions.append(txn)
        all_errors.extend(errors)

        # Index each document individually
        summary_text = (
            f"{doc['document_type']} | amount={txn.amount} | "
            f"date={txn.date} | type={txn.transaction_type}"
        )
        vector_store.index_summary(user_id, summary_text, {"doc_type": doc["document_type"]})

    summary = _build_summary(all_transactions, user_id)
    store.save(user_id, all_transactions, summary, all_errors)

    return {
        "transactions": [t.model_dump() for t in all_transactions],
        "summary": summary,
        "validation_errors": [e.model_dump() for e in all_errors],
    }
