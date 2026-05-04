import re
import json


def extract_amount(text: str):
    # Priority 1 — ₹ symbol
    match = re.search(r'₹\s*([\d,]+(?:\.\d{1,2})?)', text)
    if match:
        return float(match.group(1).replace(",", ""))
    
    # Priority 2 — Rs or INR prefix
    match = re.search(r'(?:Rs\.?|INR)\s*([\d,]+(?:\.\d{1,2})?)', text, re.IGNORECASE)
    if match:
        return float(match.group(1).replace(",", ""))
    
    # Priority 3 — number after garbled rupee indicators like 'raiaz', 'rajz', 'riaz'
    match = re.search(r'(?:raiaz|rajz|riaz|ray|raz)\s*(\d{2,6})', text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Priority 4 — number appearing after "Paid" keyword
    match = re.search(r'(?:Paid|paid)\s+(?:₹|Rs\.?)?\s*(\d{2,6})', text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Priority 5 — fallback, grab all 3-5 digit numbers and return smallest
    # smallest is more likely the actual amount, larger ones are usually IDs
    matches = re.findall(r'\b(\d{3,5})\b', text)
    if matches:
        amounts = [float(m) for m in matches]
        return min(amounts)
    
    return None


def extract_date(text: str):
    patterns = [
        # Standard: DD/MM/YYYY or DD-MM-YYYY
        r'\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}',
        # DD Mon YYYY: Jul 4, 2020
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
        # Mon DD, YYYY: Apr 21, 2026
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
        # BHIM format: 21st Apr 26 or 3rd Mar 25
        r'\d{1,2}(?:st|nd|rd|th)\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).strip()
    return None


def extract_upi_id(text: str):
    """
    Finds UPI IDs — always follow pattern: something@bankname
    Example: raaginipriya@okaxis, rahul@ybl, user@oksbi
    """
    match = re.search(r'[\w.\-]+@[\w]+', text)
    return match.group(0) if match else None


def extract_transaction_id(text: str):
    """
    Finds transaction/reference IDs.
    Looks for them after keywords first, then falls back to long numeric strings.
    """
    # First try with keyword prefix
    match = re.search(
        r'(?:UPI\s*Ref|Transaction\s*ID|Txn\s*ID|Ref\s*No|transaction\s*id)[:\s#]*([A-Z0-9]{8,})',
        text, re.IGNORECASE
    )
    if match:
        return match.group(1)
    
    # Fallback — long numeric string like 018600621034
    match = re.search(r'\b(\d{10,})\b', text)
    return match.group(1) if match else None


def extract_status(text: str):
    """
    Finds payment status.
    Includes garbled OCR variants like 'raiaz' won't match,
    but 'Paid' in clean OCR will.
    Returns SUCCESS, FAILED, or PENDING.
    """
    if re.search(r'\b(?:SUCCESS|PAID|COMPLETED|DONE|DEBITED|Paid)\b', text, re.IGNORECASE):
        return "SUCCESS"
    if re.search(r'\b(?:FAILED|DECLINED|REJECTED|CANCELLED)\b', text, re.IGNORECASE):
        return "FAILED"
    if re.search(r'\b(?:PENDING|PROCESSING|INITIATED)\b', text, re.IGNORECASE):
        return "PENDING"
    return None


def extract_bank_name(text: str):
    """
    Finds Indian bank names.
    Uses fuzzy patterns to handle garbled OCR like 'cavaa Bark' → Canara Bank.
    """
    bank_patterns = [
        (r'canara|cavaa|cnara', "Canara Bank"),
        (r'hdfc', "HDFC Bank"),
        (r'sbi|state\s*bank', "SBI"),
        (r'axis\s*bank', "Axis Bank"),
        (r'icici', "ICICI Bank"),
        (r'kotak', "Kotak Bank"),
        (r'punjab\s*national|pnb', "Punjab National Bank"),
        (r'bank\s*of\s*baroda|bob', "Bank of Baroda"),
        (r'union\s*bank', "Union Bank"),
        (r'yes\s*bank', "Yes Bank"),
        (r'indusind', "IndusInd Bank"),
    ]
    for pattern, name in bank_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return name
    return None


def extract_receiver_name(text: str):
    """
    Finds receiver/merchant name.
    Usually appears after 'To', 'Paid to', 'Sent to' keywords.
    """
    match = re.search(r'(?:To|Paid to|Sent to|Pay to)[:\s]+([A-Za-z\s]+?)(?:\n|UPI|@|\d)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def extract_consumer_number(text: str):
    """
    Finds consumer/account numbers in utility bills.
    """
    match = re.search(
        r'(?:Consumer No|Account No|CA No|Consumer Number)[:\s]*([A-Z0-9]{6,})',
        text, re.IGNORECASE
    )
    return match.group(1) if match else None


def extract_units(text: str):
    """
    Finds electricity units consumed.
    Handles: 245 units, 245 kWh, 245 Unit
    """
    match = re.search(r'(\d+(?:\.\d+)?)\s*(?:units|kWh|Unit)', text, re.IGNORECASE)
    return float(match.group(1)) if match else None


def extract_billing_period(text: str):
    """
    Finds billing period in utility bills.
    Handles: Jan 2025, March 2025
    """
    match = re.search(
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',
        text, re.IGNORECASE
    )
    return match.group(0) if match else None


def calculate_confidence(fields: dict) -> float:
    """
    Scores how complete the extraction was.
    1.0 means all fields found, 0.0 means nothing found.
    Member 3 uses this in the consistency scoring algorithm.
    """
    total = len(fields)
    filled = sum(1 for v in fields.values() if v is not None)
    return round(filled / total, 2)


def fill_schema_with_regex(schema: dict, ocr_text: str) -> dict:
    """
    Master function — takes a retrieved schema and raw OCR text.
    Fills in all null fields using extractor functions above.
    Returns complete result dict ready for Member 3.
    """
    doc_type = schema["document_type"]
    fields = schema["fields"].copy()

    # Fields common to UPI documents
    if doc_type in ["phonePe_upi", "gpay_upi"]:
        fields["amount"] = extract_amount(ocr_text)
        fields["date"] = extract_date(ocr_text)
        fields["receiver_name"] = extract_receiver_name(ocr_text)
        fields["upi_id"] = extract_upi_id(ocr_text)
        fields["transaction_id"] = extract_transaction_id(ocr_text)
        fields["bank_name"] = extract_bank_name(ocr_text)
        fields["status"] = extract_status(ocr_text)

    elif doc_type == "electricity_bill":
        fields["amount_due"] = extract_amount(ocr_text)
        fields["due_date"] = extract_date(ocr_text)
        fields["consumer_number"] = extract_consumer_number(ocr_text)
        fields["units_consumed"] = extract_units(ocr_text)
        fields["billing_period"] = extract_billing_period(ocr_text)

    elif doc_type == "water_bill":
        fields["amount_due"] = extract_amount(ocr_text)
        fields["due_date"] = extract_date(ocr_text)
        fields["consumer_number"] = extract_consumer_number(ocr_text)
        fields["billing_period"] = extract_billing_period(ocr_text)

    elif doc_type == "rent_receipt":
        fields["rent_amount"] = extract_amount(ocr_text)
        fields["payment_date"] = extract_date(ocr_text)
        fields["month_covered"] = extract_billing_period(ocr_text)

    return {
        "document_type": doc_type,
        "fields": fields,
        "confidence_score": calculate_confidence(fields)
    }


# Test directly with your actual OCR output
if __name__ == "__main__":
    sample_ocr = """
    7900
    Google Ads (gipinsgxmced)
    raiaz 500
    UPL ea wsactKn td
    018600621034
    Trap RLSHIALAPON cavaa Bark
    raaginipriya@okaxis
    Google uate
    """

    sample_schema = {
        "document_type": "gpay_upi",
        "fields": {
            "amount": None,
            "date": None,
            "receiver_name": None,
            "upi_id": None,
            "transaction_id": None,
            "bank_name": None,
            "status": None
        }
    }

    result = fill_schema_with_regex(sample_schema, sample_ocr)
    print(json.dumps(result, indent=2))