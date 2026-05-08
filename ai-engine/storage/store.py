"""
storage/store.py
================
Persistence layer — Supabase Postgres when configured, in-memory fallback otherwise.

Public API (signatures unchanged from original):
  save()         — persist a processed batch result
  get_results()  — retrieve all sessions for a user (legacy, uses in-memory)
  get_session()  — retrieve a single session by session_id (Supabase-aware)
  all_users()    — list known user_ids
  clear_user()   — delete user data

Architecture note:
  When SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set in .env,
  save() writes to Supabase `sessions` + `transactions` tables.
  get_session() reads them back.
  Without those vars, everything stays in the in-memory dict (original behaviour).
"""

import time
import uuid as _uuid_mod
from collections import defaultdict

from extraction.extractor import Transaction
from validation.validator import ValidationError
from storage.supabase_client import get_client


# ──────────────────────────────────────────────────────────────────────────────
# In-memory fallback store
# ──────────────────────────────────────────────────────────────────────────────

_store: dict[str, list[dict]] = defaultdict(list)


# ──────────────────────────────────────────────────────────────────────────────
# save()
# ──────────────────────────────────────────────────────────────────────────────

def save(
    user_id: str,
    transactions: list[Transaction],
    summary: dict,
    validation_errors: list[ValidationError],
    session_id: str | None = None,
    document_urls: list[str | None] | None = None,
) -> str:
    """
    Persist a processed document batch.

    Parameters
    ----------
    user_id          : opaque user identifier
    transactions     : list of extracted Transaction objects
    summary          : dict produced by _build_summary()
    validation_errors: list of ValidationError objects
    session_id       : pre-generated UUID string (generated here if None)
    document_urls    : list of Supabase Storage paths, parallel to transactions

    Returns
    -------
    session_id : str  — the UUID used for this session
    """
    sid = session_id or str(_uuid_mod.uuid4())
    urls = document_urls or []

    client = get_client()

    if client is None:
        # ── In-memory fallback ────────────────────────────────────────────────
        record = {
            "session_id": sid,
            "timestamp": time.time(),
            "transactions": [t.model_dump() for t in transactions],
            "summary": summary,
            "validation_errors": [e.model_dump() for e in validation_errors],
        }
        _store[user_id].append(record)
        return sid

    # ── Supabase path ─────────────────────────────────────────────────────────
    try:
        client.table("sessions").insert({
            "id": sid,
            "consistency_score":  int(summary.get("consistency_score", 0)),
            "total_income":       float(summary.get("total_income", 0)),
            "avg_monthly_income": float(summary.get("average_monthly_income", 0)),
            "months_covered":     summary.get("months", []),
            "window_months":      summary.get("window_months", []),
            "monthly_income":     summary.get("monthly_income", {}),
            "flags":              summary.get("flags", []),
            "avg_confidence":     float(summary.get("avg_confidence", 0)),
            "transaction_count":  int(summary.get("transaction_count", 0)),
        }).execute()
    except Exception as exc:
        print(f"[Supabase] sessions insert failed: {exc}")
        return sid

    for i, txn in enumerate(transactions):
        data = txn.model_dump()
        try:
            client.table("transactions").insert({
                "session_id":       sid,
                "source":           data.get("source"),
                "amount":           data.get("amount"),
                "date":             data.get("date"),
                "frequency":        data.get("frequency"),
                "transaction_type": data.get("transaction_type"),
                "description":      data.get("description"),
                "confidence":       data.get("confidence"),
                "verified":         data.get("verified", False),
                "document_url":     urls[i] if i < len(urls) else None,
            }).execute()
        except Exception as exc:
            print(f"[Supabase] transactions insert failed (row {i}): {exc}")

    return sid


# ──────────────────────────────────────────────────────────────────────────────
# get_session()  — primary retrieval by session_id
# ──────────────────────────────────────────────────────────────────────────────

def get_session(session_id: str) -> dict | None:
    """
    Retrieve a single session and its transactions by session_id.

    Returns a dict shaped like the /parse response so normalizeParseResponse
    on the frontend can consume it unchanged, or None if not found.
    """
    client = get_client()

    if client is None:
        # Search in-memory fallback
        for records in _store.values():
            for record in records:
                if record.get("session_id") == session_id:
                    return _format_session_response(session_id, record["summary"], record["transactions"])
        return None

    try:
        s_res = client.table("sessions").select("*").eq("id", session_id).maybe_single().execute()
        session = s_res.data
        if not session:
            return None

        t_res = client.table("transactions").select("*").eq("session_id", session_id).execute()
        txns = t_res.data or []

        summary = {
            "consistency_score":    session.get("consistency_score", 0),
            "total_income":         float(session.get("total_income", 0)),
            "average_monthly_income": float(session.get("avg_monthly_income", 0)),
            "months":               session.get("months_covered", []),
            "window_months":        session.get("window_months", []),
            "monthly_income":       session.get("monthly_income", {}),
            "flags":                session.get("flags", []),
            "avg_confidence":       float(session.get("avg_confidence", 0)),
            "transaction_count":    session.get("transaction_count", 0),
        }
        # Normalise transactions: add category alias so frontend transformer works
        normalised_txns = [
            {**t, "category": t.get("source", "Unknown")}
            for t in txns
        ]
        return _format_session_response(session_id, summary, normalised_txns)

    except Exception as exc:
        print(f"[Supabase] get_session failed: {exc}")
        return None


def _format_session_response(session_id: str, summary: dict, transactions: list) -> dict:
    """Shape a session into the same JSON the /parse endpoint returns."""
    return {
        "session_id":          session_id,
        "consistencyScore":    summary.get("consistency_score", 0),
        "totalIncome":         summary.get("total_income", 0),
        "averageMonthlyIncome": summary.get("average_monthly_income", 0),
        "months":              summary.get("months", []),
        "transactions":        transactions,
        "flags":               summary.get("flags", []),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Legacy helpers (in-memory only — used by /results/{user_id} endpoint)
# ──────────────────────────────────────────────────────────────────────────────

def get_results(user_id: str) -> list[dict]:
    """Return all in-memory records for a user (legacy endpoint support)."""
    return _store.get(user_id, [])


def all_users() -> list[str]:
    """List all user_ids with in-memory data (admin use only)."""
    return list(_store.keys())


def clear_user(user_id: str) -> None:
    """Remove all in-memory data for a user."""
    _store.pop(user_id, None)
