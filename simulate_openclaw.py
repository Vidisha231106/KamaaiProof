import sys
import os
import json
from pathlib import Path

# Add paths to sys for imports
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.append(str(Path(PROJECT_ROOT) / "backend" / "src" / "Python_engine"))
sys.path.append(str(Path(PROJECT_ROOT) / "ai-engine"))

from extractor import extract_with_pure_vision as extract_data
from sanitization.sanitizer import sanitize
from validation.validator import validate
from extraction.extractor import Transaction

def simulate_openclaw(image_path):
    print(f"\n[OpenClaw Simulation] Initializing for: {os.path.basename(image_path)}")
    
    # Step 1: Vision Extraction (The 'OpenClaw' part)
    print("  → Running Vision-First Extraction...")
    try:
        raw_extraction = extract_data(image_path)
    except Exception as e:
        print(f"  ✗ Extraction failed: {str(e)}")
        return
    
    if "error" in raw_extraction:
        print(f"  ✗ Extraction failed: {raw_extraction['error']}")
        return
    
    # Step 2: Sanitization (Privacy Layer)
    print("  → Running Privacy Sanitization...")
    # Extract fields
    fields = raw_extraction.get("fields", {})
    
    # Simulate sanitizing the description
    description_raw = f"{raw_extraction.get('document_type')} transaction. Amount: {fields.get('amount') or fields.get('rent_amount')} Date: {fields.get('date') or fields.get('payment_date')}"
    san_result = sanitize(description_raw)
    
    # Step 3: Validate & Structure
    print("  → Validating against Business Rules...")
    # Convert to ai-engine's Transaction schema
    amount = fields.get("amount") or fields.get("rent_amount") or fields.get("amount_due") or fields.get("total_amount")
    # Clean amount if string
    if isinstance(amount, str):
        try:
            amount = float(amount.replace("₹", "").replace(",", "").strip())
        except:
            amount = None

    date_str = fields.get("date") or fields.get("payment_date") or fields.get("due_date")
    
    txn = Transaction(
        id=f"tx-{os.path.basename(image_path)[:8]}",
        source=raw_extraction.get("document_type", "unknown"),
        amount=amount,
        date=date_str,
        transaction_type="credit" if raw_extraction.get("document_type") in ["rent_receipt", "bhim_upi"] else "debit",
        description=san_result.sanitized_text,
        confidence=raw_extraction.get("confidence_score", 0.0),
        verified=True
    )
    
    errors = validate(txn)
    
    # Step 4: Final Output
    print("\n" + "="*60)
    print("  FINAL WORK PASSPORT PAYLOAD (SIMULATED OPENCLAW)")
    print("="*60)
    print(json.dumps({
        "status": "PROCESSED",
        "privacy_metrics": {
            "pii_detected": san_result.pii_found,
            "masking_applied": True
        },
        "extracted_data": txn.model_dump(),
        "validation": {
            "is_valid": len([e for e in errors if e.severity == "error"]) == 0,
            "issues": [e.model_dump() for e in errors]
        }
    }, indent=2))
    print("="*60)

if __name__ == "__main__":
    test_doc = os.path.join(PROJECT_ROOT, "backend/src/Python_engine/Documents/bhim_upi_1.jpeg")
    simulate_openclaw(test_doc)
