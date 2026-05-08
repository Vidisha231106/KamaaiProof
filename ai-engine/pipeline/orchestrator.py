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

import os
import statistics
from datetime import date, datetime

from sanitization.sanitizer import sanitize
from extraction.extractor import Transaction
from extraction.base_extractor import MockExtractor, OpenClawExtractor, FallbackExtractor
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

    # Strict 6-month rolling window scoring
    dated_credit_txns = []
    future_dated = []
    today = date.today()
    for t in credit_txns:
        if not t.date:
            continue
        try:
            parsed = datetime.fromisoformat(t.date).date()
            if parsed > today:
                future_dated.append(t)
                continue
            dated_credit_txns.append((t, parsed))
        except ValueError:
            continue

    anchor_date = max((d for _, d in dated_credit_txns), default=today)

    def month_start(d: date) -> date:
        return d.replace(day=1)

    def shift_month(d: date, delta: int) -> date:
        month_idx = (d.year * 12 + (d.month - 1)) + delta
        y = month_idx // 12
        m = (month_idx % 12) + 1
        return date(y, m, 1)

    anchor_month = month_start(anchor_date)
    window_starts = [shift_month(anchor_month, -i) for i in range(5, -1, -1)]
    window_months = [m.strftime("%Y-%m") for m in window_starts]

    monthly_income: dict[str, float] = {m: 0.0 for m in window_months}
    for t, parsed in dated_credit_txns:
        bucket = parsed.strftime("%Y-%m")
        if bucket in monthly_income:
            monthly_income[bucket] += float(t.amount or 0.0)

    covered_months = [m for m, amount in monthly_income.items() if amount > 0]
    missing_months = [m for m in window_months if m not in covered_months]

    # Score out of 100
    # - 70 points for month coverage across 6 months
    # - 30 points for stability of monthly income across covered months
    coverage_score = (len(covered_months) / 6) * 70

    incomes = [monthly_income[m] for m in covered_months]
    if len(incomes) >= 2:
        mean_income = statistics.mean(incomes)
        if mean_income > 0:
            std_income = statistics.pstdev(incomes)
            coeff_var = std_income / mean_income
            stability_score = max(0.0, 30 * (1 - min(coeff_var, 1.0)))
        else:
            stability_score = 0.0
    elif len(incomes) == 1:
        stability_score = 10.0
    else:
        stability_score = 0.0

    consistency_score = int(round(min(100.0, coverage_score + stability_score)))

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
    if future_dated:
        flags.append(
            f"{len(future_dated)} transaction(s) have future dates and were excluded from scoring."
        )
    if not covered_months:
        flags.append("No dated credit transactions found — income period cannot be determined.")
    if missing_months:
        flags.append(
            f"Income evidence missing in {len(missing_months)} month(s) within the 6-month window."
        )

    # Average monthly income across covered months in the scoring window
    window_income = sum(monthly_income[m] for m in covered_months)
    avg_monthly_income = round(window_income / max(len(covered_months), 1), 2) if covered_months else 0.0

    return {
        "user_id": user_id,
        "total_income": round(total_income, 2),
        "average_monthly_income": avg_monthly_income,
        "total_spend": round(total_spend, 2),
        "consistency_score": consistency_score,
        "months": covered_months,
        "window_months": window_months,
        "monthly_income": {k: round(v, 2) for k, v in monthly_income.items()},
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
    use_openclaw: bool = True
) -> dict:
    """
    Execute the full AI pipeline for a single document submission.

    Steps
    -----
    1. Sanitize  — strip PII from raw_content
    2. Extract   — parse structured fields from sanitized text (using OpenClaw or Mock)
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
    # Initialize Extractor with Fallback
    mock = MockExtractor(document_type=document_type)
    
    if use_openclaw:
        claw = OpenClawExtractor()
        extractor = FallbackExtractor(claw, mock)
    else:
        extractor = mock

    extraction_result = extractor.run(sanitized_text)
    
    # Adapt to Transaction objects for the rest of the pipeline
    extracted_txns = extraction_result.get("transactions", [])
    if not extracted_txns:
        # Create an empty transaction if none found, to satisfy downstream types
        transaction = Transaction(
            id="error-tx",
            source=document_type,
            amount=None,
            date=None,
            frequency="unknown",
            transaction_type="unknown",
            description="Extraction failed or returned no data",
            confidence=0.0
        )
    else:
        # For single document pipeline, we take the first transaction
        data = extracted_txns[0]
        # Handle cases where OpenClaw might not return all fields
        transaction = Transaction(
            id=data.get("id", f"tx-{os.urandom(4).hex()}"),
            source=data.get("source", document_type),
            amount=data.get("amount"),
            date=data.get("date"),
            frequency=data.get("frequency", "unknown"),
            transaction_type=data.get("transaction_type", "unknown"),
            description=data.get("description", f"Extracted from {document_type}"),
            confidence=data.get("confidence", 0.7)
        )

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
    documents: list[dict],  # list of {"document_type": ..., "content": ..., "document_url": ...}
    session_id: str | None = None,
) -> dict:
    """
    Process multiple documents for one user in sequence.

    Aggregates transactions and summaries across all documents.
    Useful when frontend sends multiple files at once.
    """
    all_transactions: list[Transaction] = []
    all_errors: list[ValidationError] = []
    all_document_urls: list[str | None] = []

    for doc in documents:
        is_binary = bool(doc.get("is_binary"))
        if is_binary:
            sanitized_text = doc["content"]
        else:
            san_result = sanitize(doc["content"])
            sanitized_text = san_result.sanitized_text

        # Skip slow OpenClaw/Groq path for plain text content — use MockExtractor directly.
        # OpenClaw (Vision LLM) is only meaningful for binary image/pdf files.
        mock = MockExtractor(document_type=doc["document_type"])
        if is_binary:
            claw = OpenClawExtractor()
            extractor = FallbackExtractor(claw, mock)
        else:
            extractor = mock

        extraction_result = extractor.run(sanitized_text)
        extracted_txns = extraction_result.get("transactions", [])
        
        if not extracted_txns:
            continue
            
        # Convert dict to Transaction model
        for data in extracted_txns:
            txn = Transaction(
                id=data.get("id", f"tx-{os.urandom(4).hex()}"),
                source=data.get("source", doc["document_type"]),
                amount=data.get("amount"),
                date=data.get("date"),
                frequency=data.get("frequency", "unknown"),
                transaction_type=data.get("transaction_type", "unknown"),
                description=data.get("description", "Extracted transaction"),
                confidence=data.get("confidence", 0.7)
            )
            errors = validate(txn)
            all_transactions.append(txn)
            all_errors.extend(errors)
            all_document_urls.append(doc.get("document_url"))

            # Index each document individually
            summary_text = (
                f"{doc['document_type']} | amount={txn.amount} | "
                f"date={txn.date} | type={txn.transaction_type}"
            )
            vector_store.index_summary(user_id, summary_text, {"doc_type": doc["document_type"]})

    summary = _build_summary(all_transactions, user_id)
    saved_session_id = store.save(
        user_id,
        all_transactions,
        summary,
        all_errors,
        session_id=session_id,
        document_urls=all_document_urls,
    )

    return {
        "session_id": saved_session_id,
        "transactions": [t.model_dump() for t in all_transactions],
        "summary": summary,
        "validation_errors": [e.model_dump() for e in all_errors],
    }
