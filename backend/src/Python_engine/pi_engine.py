import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PiEngine")

try:
    from .extractor import extract_with_pure_vision as extract_data
except ImportError:
    # Handle direct execution
    from extractor import extract_with_pure_vision as extract_data


class PiEngine:
    """
    The main agent loop for KamaaiProof document processing.
    Orchestrates the RAG-enhanced extraction flow.
    """
    
    def __init__(self):
        logger.info("Initializing Pi Engine Agent Loop...")
        self.results = []
        self.errors = []

    def process_batch(self, image_paths: List[str]) -> Dict[str, Any]:
        """
        Processes a collection of documents and aggregates them into a Work Passport shape.
        """
        logger.info(f"Starting batch process for {len(image_paths)} documents.")
        self.results = []
        self.errors = []

        for path in image_paths:
            if not os.path.exists(path):
                logger.warning(f"File not found: {path}")
                self.errors.append({"path": path, "error": "File not found"})
                continue

            try:
                result = extract_data(path)
                result["image_path"] = path
                self.results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {path}: {str(e)}")
                self.errors.append({"path": path, "error": str(e)})

        return self.generate_passport_summary()

    def generate_passport_summary(self) -> Dict[str, Any]:
        """
        Computes the final Work Passport statistics.
        """
        total_income = 0.0
        months = set()
        transactions = []
        
        # Categorize results
        for r in self.results:
            fields = r.get("fields", {})
            doc_type = r.get("document_type", "unknown")
            
            # Flexible extraction of amount and date
            amount = fields.get("amount") or fields.get("amount_due") or fields.get("rent_amount") or fields.get("total_amount")
            date = fields.get("date") or fields.get("due_date") or fields.get("payment_date") or fields.get("date_and_time")
            
            # Fallback: scan all fields for keywords
            if not amount or not date:
                for k, v in fields.items():
                    key_lower = k.lower()
                    if not amount and ("amount" in key_lower or "total" in key_lower or "due" in key_lower):
                        amount = v
                    if not date and ("date" in key_lower or "time" in key_lower or "period" in key_lower):
                        date = v

            if amount:
                try:
                    # Clean the amount string if it's not already a number
                    if isinstance(amount, str):
                        amount = float(amount.replace("₹", "").replace(",", "").strip())
                    
                    if doc_type in ["phonePe_upi", "gpay_upi", "bhim_upi", "rent_receipt"]:
                        total_income += float(amount)
                except:
                    pass
            
            if date:
                # Try to extract YYYY-MM
                try:
                    # Very basic date parsing for summary
                    months.add(date[:7] if len(date) >= 7 else "Unknown")
                except:
                    pass

            transactions.append({
                "source": os.path.basename(r.get("image_path", "unknown")),
                "category": doc_type,
                "date": date,
                "amount": amount,
                "confidence": r.get("confidence_score", 0.0),
                "verified": r.get("confidence_score", 0.0) > 0.7
            })

        # Calculate consistency score (simplified logic)
        avg_confidence = sum(t["confidence"] for t in transactions) / len(transactions) if transactions else 0
        consistency_score = int(avg_confidence * 100)

        summary = {
            "consistencyScore": consistency_score,
            "totalIncome": round(total_income, 2),
            "months": sorted(list(months)),
            "transactions": transactions,
            "flags": self.generate_flags(transactions),
            "errors": self.errors
        }

        return summary

    def generate_flags(self, transactions: List[Dict]) -> List[str]:
        flags = []
        low_conf = [t for t in transactions if t["confidence"] < 0.5]
        if low_conf:
            flags.append(f"Low confidence extraction in {len(low_conf)} files. Please verify manually.")
        
        if not transactions:
            flags.append("No valid transactions found.")
            
        return flags

if __name__ == "__main__":
    # Test script
    engine = PiEngine()
    
    # Resolve Documents directory relative to this file
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOCS_DIR = os.path.join(BASE_DIR, "Documents")
    
    if not os.path.exists(DOCS_DIR):
        print(f"Test documents directory missing at {DOCS_DIR}. Creating it...")
        os.makedirs(DOCS_DIR, exist_ok=True)
        test_docs = []
    else:
        # Filter for existing files
        test_docs = [os.path.join(DOCS_DIR, f) 
                     for f in os.listdir(DOCS_DIR) 
                     if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if test_docs:
        print(f"Processing {len(test_docs)} test documents...")
        final_output = engine.process_batch(test_docs)
        print("\n=== AGENT LOOP FINAL OUTPUT ===")
        print(json.dumps(final_output, indent=2))
    else:
        print(f"No test documents found in {DOCS_DIR}")

