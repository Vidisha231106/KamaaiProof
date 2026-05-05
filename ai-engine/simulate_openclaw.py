import sys
import os
import json
from pathlib import Path

# Add paths to sys for imports
PROJECT_ROOT = "/Users/shash/Downloads/KamaiProof-ref/KamaaiProof"
sys.path.append(str(Path(PROJECT_ROOT) / "backend" / "src" / "Python_engine"))
sys.path.append(str(Path(PROJECT_ROOT) / "ai-engine"))

from pi_engine import PiEngine
from sanitization.sanitizer import sanitize
from validation.validator import validate
from extraction.extractor import Transaction

def simulate_openclaw(image_path):
    print(f"\n[OpenClaw Simulation] Initializing for: {os.path.basename(image_path)}")
    
    # Step 1: Vision Extraction (The 'OpenClaw' part)
    engine = PiEngine()
    print("  → Running Vision-First Extraction...")
    raw_extraction = engine.extract_single(image_path)
    
    if "error" in raw_extraction:
        print(f"  ✗ Extraction failed: {raw_extraction['error']}")
        return
    
    # Step 2: Sanitization (Privacy Layer)
    print("  → Running Privacy Sanitization...")
    # Simulate sanitizing the description or any text-heavy fields
    description = raw_extraction.get("description", f"Transaction from {raw_extraction.get('document_type')}")
    san_result = sanitize(description)
    
    # Step 3: Validate & Structure
    print("  → Validating against Business Rules...")
    # Convert to ai-engine's Transaction schema
    fields = raw_extraction.get("fields", {})
    txn = Transaction(
        id=f"tx-{os.path.basename(image_path)[:8]}",
        source=raw_extraction.get("document_type", "unknown"),
        amount=fields.get("amount") or fields.get("rent_amount") or fields.get("amount_due"),
        date=fields.get("date") or fields.get("payment_date") or fields.get("due_date"),
        transaction_type="credit" if raw_extraction.get("document_type") in ["rent_receipt", "bhim_upi"] else "debit",
        description=san_result.sanitized_text,
        confidence=raw_extraction.get("confidence_score", 0.0),
        verified=True
    )
    
    errors = validate(txn)
    
    # Step 4: Final Output
    print("\n[Simulation Results]")
    print(json.dumps({
        "status": "PROCESSED",
        "pii_filtered": san_result.pii_found,
        "transaction": txn.model_dump(),
        "validation_issues": [e.model_dump() for e in errors]
    }, indent=2))

if __name__ == "__main__":
    test_doc = "/Users/shash/Downloads/KamaiProof-ref/KamaaiProof/backend/src/Python_engine/Documents/rent_receipt_1.jpeg"
    simulate_openclaw(test_doc)
