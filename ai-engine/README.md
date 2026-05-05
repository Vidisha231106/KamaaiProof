# KamaaiProof AI Engine

Modular AI backend for processing informal worker financial documents.

## Architecture

```
ai-engine/
├── main.py                  # FastAPI app entry point
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
│
├── api/
│   └── routes.py            # HTTP route handlers (thin layer)
│
├── pipeline/
│   └── orchestrator.py      # Master pipeline: Input→Sanitize→Extract→Validate→Store→Index
│
├── sanitization/
│   └── sanitizer.py         # PII removal (phone, UPI, names, IFSC, accounts)
│
├── extraction/
│   └── extractor.py         # Structured field extraction (mock regex engine)
│
├── validation/
│   └── validator.py         # Business rule validation (amount, date, type)
│
├── storage/
│   └── store.py             # In-memory store keyed by user_id
│
├── retrieval/
│   └── vector_store.py      # Mock vector store + cosine similarity retrieval
│
├── security/
│   └── rbac.py              # RBAC (worker/mfi_officer/admin) + encryption stubs
│
└── tests/
    └── test_pipeline.py     # 12 test cases + unit tests
```

## Quick Start

```bash
cd ai-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server (port 8000 matches frontend default)
uvicorn main:app --reload --port 8000
```

API docs auto-generated at: http://localhost:8000/docs

## API Endpoints

### POST /process-document
Process a single document through the full AI pipeline.

**Request:**
```json
{
  "user_id": "worker_001",
  "document_type": "upi",
  "content": "Google Pay\n₹2,500 received from someone\nDate: 15/03/2025"
}
```

**Response:**
```json
{
  "transactions": [
    {
      "id": "tx-a1b2c3d4",
      "source": "upi",
      "amount": 2500.0,
      "date": "2025-03-15",
      "transaction_type": "credit",
      "description": "Google Pay | ₹2,500 received from someone",
      "confidence": 0.85,
      "verified": false
    }
  ],
  "summary": {
    "user_id": "worker_001",
    "total_income": 2500.0,
    "total_spend": 0.0,
    "consistency_score": 100,
    "months": ["2025-03"],
    "transaction_count": 1,
    "avg_confidence": 0.85,
    "flags": []
  },
  "validation_errors": []
}
```

### POST /parse (Frontend-Compatible)
Accepts `multipart/form-data` exactly matching the frontend's existing POST contract.

Fields: `files[]`, `metadata` (JSON string), `whatsappText`

Returns:
```json
{
  "consistencyScore": 85,
  "totalIncome": 12000,
  "months": ["2025-01", "2025-02", "2025-03"],
  "transactions": [...],
  "flags": []
}
```

### GET /results/{user_id}
Returns stored structured results for a user.

Query param: `requesting_user` (default: `worker_001`) — used for RBAC.

- Workers see full transactions for their own data
- MFI officers see summaries only

### POST /retrieve
Similarity search across indexed summaries.

**Request:**
```json
{
  "query": "monthly rent payment 4000",
  "top_k": 3
}
```

### GET /health
Liveness probe.

## Running Tests

```bash
# From the ai-engine/ directory
python tests/test_pipeline.py
```

Covers:
- 12 diverse document inputs (UPI, rent, bills, noisy, malformed, future-dated, zero-amount)
- Sanitization unit tests (PII masking)
- RBAC unit tests (role enforcement)
- Encryption stub roundtrip
- Vector store retrieval

## Replacing Mock Components with OpenClaw

The engine is designed for drop-in replacement:

| Component | File | What to replace |
|---|---|---|
| Extraction | `extraction/extractor.py` | `extract()` body → LLM/OpenClaw API call |
| Embedding | `retrieval/vector_store.py` | `_mock_embed()` → OpenClaw embedding endpoint |
| Encryption | `security/rbac.py` | `encrypt_field()` → AES-GCM with KMS |
| Storage | `storage/store.py` | `_store` dict → Firebase Firestore client |

All public function signatures remain stable across these replacements.

## Privacy Guardrails

- Raw input text is NEVER stored or logged
- PII is stripped in the sanitization step before extraction
- Only structured, PII-free data reaches the storage layer
- WhatsApp-derived entries are flagged as unverified
- RBAC prevents data leakage between roles
