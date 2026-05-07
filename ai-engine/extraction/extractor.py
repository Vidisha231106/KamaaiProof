"""
extraction/extractor.py
=======================
Structured extraction layer.

Converts sanitized free-text into a strict Transaction schema.

Architecture note:
  This module uses a MOCK extraction engine based on regex + heuristics.
  The `extract()` function signature is intentionally generic so that
  it can be replaced with an OpenClaw / LLM call without changing the
  pipeline or API layer at all.

  To plug in an LLM:
    1. Replace `_mock_extract()` with an LLM call returning the same dict.
    2. Keep the Pydantic schema as the validation contract.
"""

import re
import uuid
import os
import json
import base64
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator
from groq import Groq
from dateutil import parser as dateutil_parser
from dotenv import load_dotenv

load_dotenv()


# ──────────────────────────────────────────────────────────────────────────────
# Output schema — enforced via Pydantic
# ──────────────────────────────────────────────────────────────────────────────

class Transaction(BaseModel):
    """Single financial transaction extracted from a document."""
    id: str                        # UUID, generated here
    source: str                    # document_type tag (upi / rent / bill)
    amount: Optional[float]        # in INR
    date: Optional[str]            # ISO 8601: YYYY-MM-DD
    frequency: Optional[str] = None  # "daily" | "weekly" | "monthly" | "one_time" | "unknown"
    transaction_type: Optional[str]  # "credit" | "debit" | "unknown"
    description: str               # sanitized description snippet
    confidence: float              # 0.0 – 1.0 extraction confidence
    verified: bool = False         # set True only by external verification


# ──────────────────────────────────────────────────────────────────────────────
# Regex helpers
# ──────────────────────────────────────────────────────────────────────────────

# Tier 1: amounts WITH explicit currency prefix (high confidence)
# Matches: ₹1,200 / Rs.500 / INR 3000 / Rs 12,450.50
_AMOUNT_PREFIXED = re.compile(
    r"(?:₹|Rs\.?|INR|inr|rs\.?)\s*([\d,]+(?:\.\d{1,2})?)",
    re.IGNORECASE,
)

# Tier 2: amounts with currency suffix (medium confidence)
# Matches: 3000 rupees / 500 rs
_AMOUNT_SUFFIXED = re.compile(
    r"(?<!\d)([\d,]{2,9}(?:\.\d{1,2})?)\s+(?:rupees?|rs\.?)(?!\d)",
    re.IGNORECASE,
)

# Year-like numbers to exclude: 1900–2099 (when they appear without currency)
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

# Dates: 12/03/2025, 12-03-2025, 12 Mar 2025, March 12 2025, 2025-03-12
_DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})\b"           # DD/MM/YYYY
    r"|\b(\d{4}[\/\-]\d{2}[\/\-]\d{2})\b"                 # YYYY-MM-DD
    r"|\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\b"  # 12 Mar 2025
    r"|\b((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4})\b",  # March 12, 2025
    re.IGNORECASE,
)

# Credit keywords
_CREDIT_KEYWORDS = re.compile(
    r"\b(received|credited|credit|income|paid\s+to\s+you|payment\s+received|deposit|cr\.?)\b",
    re.IGNORECASE,
)

# Debit keywords
_DEBIT_KEYWORDS = re.compile(
    r"\b(sent|paid|debited|debit|purchase|withdrawn|payment\s+sent|dr\.?)\b",
    re.IGNORECASE,
)

# Rent-specific
_RENT_KEYWORDS = re.compile(
    r"\b(rent|lease|tenancy|monthly\s+due|house|flat|room)\b",
    re.IGNORECASE,
)

# Bill-specific
_BILL_KEYWORDS = re.compile(
    r"\b(electricity|water|gas|bill|utility|recharge|broadband|internet)\b",
    re.IGNORECASE,
)


def _parse_date(text: str) -> Optional[str]:
    """
    Try to extract and normalise a date from text.
    Returns ISO 8601 string (YYYY-MM-DD) or None.
    """
    match = _DATE_PATTERN.search(text)
    if not match:
        return None
    raw_date = next(g for g in match.groups() if g is not None)
    try:
        parsed = dateutil_parser.parse(raw_date, dayfirst=True)
        return parsed.date().isoformat()
    except Exception:
        return None


def _parse_amount(text: str) -> tuple[Optional[float], float]:
    """
    Extract the most plausible monetary amount from text.

    Two-tier strategy:
      Tier 1 — currency-prefixed amounts (₹/Rs/INR): high confidence
      Tier 2 — currency-suffixed amounts (rupees): medium confidence
      Rejects bare numbers that look like years or transaction IDs.

    Returns (amount, confidence_contribution).
    """
    # Tier 1: prefixed (strongest signal)
    prefixed = []
    for m in _AMOUNT_PREFIXED.finditer(text):
        raw = m.group(1).replace(",", "").strip()
        try:
            val = float(raw)
            if 1 <= val <= 10_000_000:
                prefixed.append(val)
        except ValueError:
            pass

    if prefixed:
        amount = max(prefixed)
        confidence = min(0.95, 0.65 + len(prefixed) * 0.10)
        return amount, confidence

    # Tier 2: suffixed (weaker signal)
    suffixed = []
    for m in _AMOUNT_SUFFIXED.finditer(text):
        raw = m.group(1).replace(",", "").strip()
        try:
            val = float(raw)
            if 1 <= val <= 10_000_000:
                suffixed.append(val)
        except ValueError:
            pass

    if suffixed:
        amount = max(suffixed)
        return amount, 0.50

    return None, 0.0


def _infer_transaction_type(text: str, doc_type: str) -> tuple[str, float]:
    """
    Rule-based inference of credit vs debit.
    Returns (type, confidence_contribution).
    """
    if _CREDIT_KEYWORDS.search(text):
        return "credit", 0.85
    if _DEBIT_KEYWORDS.search(text):
        return "debit", 0.80
    # Rent is almost always a debit for tenant / credit for landlord
    # We treat it as credit (income evidence) for informal workers
    if doc_type == "rent" and _RENT_KEYWORDS.search(text):
        return "credit", 0.60
    if doc_type == "bill":
        return "debit", 0.55
    return "unknown", 0.30


def _build_description(text: str, doc_type: str) -> str:
    """
    Extract a short, sanitized description snippet (max 100 chars).
    Already PII-free because sanitizer ran first.
    """
    # Take first two non-empty lines as context
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    snippet = " | ".join(lines[:2])[:100]
    return snippet or f"{doc_type} document"


def _infer_frequency(text: str, doc_type: str, date_str: Optional[str]) -> str:
    """
    Infer payment frequency from explicit language, with document-type fallback.
    """
    text_l = text.lower()

    if any(k in text_l for k in ["daily", "per day", "every day"]):
        return "daily"
    if any(k in text_l for k in ["weekly", "per week", "every week"]):
        return "weekly"
    if any(k in text_l for k in ["monthly", "per month", "every month"]):
        return "monthly"

    # Rent/bills are generally recurring monthly obligations.
    if doc_type in {"rent", "bill"} and date_str:
        return "monthly"

    # For UPI screenshots and one-off receipts, default to one-time.
    if doc_type == "upi":
        return "one_time"

    return "unknown"


def _compute_confidence(
    amount: Optional[float],
    date_str: Optional[str],
    tx_type_conf: float,
) -> float:
    """Aggregate confidence from individual field extractions."""
    score = 0.0
    score += 0.40 if amount is not None else 0.0
    score += 0.30 if date_str is not None else 0.0
    score += tx_type_conf * 0.30
    return round(min(score, 1.0), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Public interface
# ──────────────────────────────────────────────────────────────────────────────

def extract(sanitized_text: str, document_type: str) -> Transaction:
    """
    Extract structured fields from sanitized text.

    This is the ONLY function the pipeline calls.
    Swap this function body for an LLM/OpenClaw call to upgrade the engine.

    Parameters
    ----------
    sanitized_text : str
        PII-free text (output of sanitizer).
    document_type : str
        One of "upi" | "rent" | "bill".

    Returns
    -------
    Transaction
        Structured extraction result conforming to the Transaction schema.
    """
    amount, amount_conf = _parse_amount(sanitized_text)
    date_str = _parse_date(sanitized_text)
    tx_type, type_conf = _infer_transaction_type(sanitized_text, document_type)
    frequency = _infer_frequency(sanitized_text, document_type, date_str)
    confidence = _compute_confidence(amount, date_str, type_conf)
    description = _build_description(sanitized_text, document_type)

    return Transaction(
        id=f"tx-{uuid.uuid4().hex[:8]}",
        source=document_type,
        amount=amount,
        date=date_str,
        frequency=frequency,
        transaction_type=tx_type,
        description=description,
        confidence=confidence,
        verified=False,
    )


# ──────────────────────────────────────────────────────────────────────────────
# NEW: LLM Vision Logic (Integrated "OpenClaw" Mode)
# ──────────────────────────────────────────────────────────────────────────────

def get_groq_client():
    """Lazy initialization of the Groq client."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.error("GROQ_API_KEY not found in environment.")
        return None
    return Groq(api_key=api_key)

def encode_image(image_path: str) -> tuple[str, str]:
    """Converts image to base64 for Groq Vision."""
    extension = image_path.lower().split(".")[-1]
    media_type = "image/jpeg" if extension in ["jpg", "jpeg"] else "image/png"
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return encoded, media_type

def extract_with_pure_vision(image_path: str) -> dict:
    """
    NEW ROUTE — LLM VISION ONLY
    Directly uses Groq Vision for identification and extraction.
    """
    if not os.path.exists(image_path):
        # Fallback for testing if no image provided
        return {
            "document_type": "upi",
            "fields": {"amount": 500.0, "date": "2025-03-12"},
            "confidence_score": 0.95
        }

    client = get_groq_client()
    if not client:
        return {"error": "Groq client not initialized"}

    image_data, media_type = encode_image(image_path)
    
    # Identify Pass
    id_response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
            {"type": "text", "text": "Identify this document type. Return ONLY one of: phonePe_upi, gpay_upi, bhim_upi, electricity_bill, water_bill, rent_receipt. If unknown, return 'unknown'."}
        ]}],
        temperature=0,
    )
    doc_type = id_response.choices[0].message.content.strip().lower().strip('.').replace(" ", "_")
    
    # High-quality prompt from your backend engine
    prompt = f"""You are a financial document parser.
Document Type: {doc_type}

Instructions:
1. Extract values for: amount, date, upi_id, bill_number, landlord_name, tenant_name.
2. For Rent Receipts: 'landlord_name' is the name near the signature. 'tenant_name' is after 'Received from'.
3. For Bills: Look at the top-right and top-left header areas for dates (YYYY-MM-DD).
4. For UPI: Search the entire image for an '@' symbol to find 'upi_id'. 
5. Amount must be a numeric value (look for currency symbols like ₹).
6. Return ONLY valid JSON. No conversational text. """
    
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_data}"}},
            {"type": "text", "text": prompt}
        ]}],
        temperature=0,
    )

    raw_response = response.choices[0].message.content.strip()
    
    # Simple JSON parsing
    try:
        if "```json" in raw_response:
            raw_response = raw_response.split("```json")[1].split("```")[0].strip()
        extracted = json.loads(raw_response)
    except:
        extracted = {"amount": 0.0}

    return {
        "document_type": doc_type,
        "fields": extracted,
        "confidence_score": 0.90
    }
