import json
import sys
from pathlib import Path

# Add ai-engine root for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from pipeline.orchestrator import run_pipeline_batch


def main() -> None:
    repo_root = PROJECT_ROOT.parent
    docs_dir = repo_root / "backend" / "src" / "Python_engine" / "Documents"

    documents = [
        {"document_type": "rent", "content": str(docs_dir / "rentreceipt_jan26.png")},
        {"document_type": "upi", "content": str(docs_dir / "payment_mar26.jpeg")},
        {"document_type": "upi", "content": str(docs_dir / "payment_apr26.jpeg")},
        {"document_type": "upi", "content": str(docs_dir / "payment_may26.jpeg")},
        {"document_type": "bill", "content": str(docs_dir / "Elecbill_feb26.jpeg")},
        {"document_type": "bill", "content": str(docs_dir / "Elecbill_mar26.jpeg")},
        {"document_type": "bill", "content": str(docs_dir / "Elecbill_apr26.jpeg")},
        {"document_type": "bill", "content": str(docs_dir / "waterbill_feb26.png")},
        {"document_type": "bill", "content": str(docs_dir / "waterbill_apr26.png")},
        {"document_type": "bill", "content": str(docs_dir / "waterbill_may26.png")},
    ]

    result = run_pipeline_batch(user_id="demo_user_001", documents=documents)

    print("\n=== DEMO SCORING OUTPUT ===")
    print(json.dumps(result["summary"], indent=2))
    print(f"\nTransactions parsed: {len(result.get('transactions', []))}")


if __name__ == "__main__":
    main()
