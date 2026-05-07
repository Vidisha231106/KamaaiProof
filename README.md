# KamaaiProof

Work Passport for India's Invisible Workforce.

KamaaiProof helps informal workers convert everyday evidence of work into a lender-readable proof packet. The system focuses on workers who earn consistently but do not have formal salary slips, employer letters, or traditional credit history.

## Problem Context

India has a very large informal workforce (domestic workers, auto drivers, street vendors, daily wage laborers, and related groups). Income exists, but proof is fragmented across:

- UPI screenshots
- Utility bills
- Receipts
- Employer messages (often WhatsApp)

The core gap is not income creation, but evidence assembly and presentation quality.

## Product Summary

KamaaiProof collects user-submitted records, parses them into structured fields, applies consistency checks, and returns a Work Passport summary that can be used as supporting evidence during loan review.

Primary outputs:

- Estimated monthly income
- Consistency score out of 100
- Parsed document list with dates and amounts
- Plain-language warning or fraud flags
- Downloadable Work Passport PDF (planned in next phase)

## Personas (Operational Focus)

1. Informal worker (primary beneficiary)
2. SHG leader (assists document collection and onboarding)
3. MFI field officer (uses summary to reduce manual verification time)

## Repository Status

This repository currently contains:

- A complete frontend foundation (React + routing + upload/result UX + theming)
- Backend structural scaffolding and detailed implementation specs
- Team role execution docs in the docs folder

This repository does not yet contain:

- Full backend parser implementation
- Full scoring and Firebase persistence logic
- Production-ready PDF export integration path

## High-Level Architecture

1. Frontend gathers files and user tags.
2. Frontend sends multipart payload to backend parse endpoint.
3. Backend parses each document category with chain-specific extraction.
4. Backend computes scoring and warning flags.
5. Frontend renders score, transactions, and warnings.
6. PDF layer generates browser-side Work Passport document.

## Directory Map

```
KamaaiProof/
	backend/
		src/
			api/
			chains/
			services/
	docs/
		01-Frontend-Spec.md
		02-LangChain-Parsing-Spec.md
		03-Scoring-Firebase-PDF-Spec.md
		04-DevOps-QA-Spec.md
	frontend/
		src/
			components/
			pages/
			services/
```

## Contract Between Frontend and Backend

Frontend currently posts to:

- Endpoint: `POST /parse`
- Content-Type: `multipart/form-data`

Expected form fields:

- `files`: repeated file entries
- `metadata`: JSON string array with per-file tag and metadata
- `whatsappText`: optional plain text string

Frontend can normalize multiple backend response shapes, but target response shape should be:

```json
{
	"consistencyScore": 78,
	"totalIncome": 12000,
	"months": ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02"],
	"transactions": [
		{
			"id": "tx-1",
			"source": "gpay_screenshot_1.jpg",
			"category": "UPI Screenshot",
			"date": "2026-02-06",
			"amount": 2500,
			"verified": true
		}
	],
	"flags": ["Address mismatch detected across utility bills"]
}
```

## Privacy and Data Safety Guardrails

Mandatory guidance for all future contributors and AI agents:

- Do not persist raw personally identifiable identifiers in scored records.
- Avoid storing names, phone numbers, or UPI IDs in Firestore session summaries.
- Keep WhatsApp-derived records explicitly labeled unverified.
- Preserve user-controlled flow: this output is supporting evidence, not loan approval logic.

## How AI Agents Should Use This Repository

When asking an AI coding agent to continue implementation, include:

1. The folder target (frontend, backend, or docs)
2. The specific role context from docs (Person 1/2/3/4)
3. The expected API contract or UI acceptance criteria
4. Any constraints (no schema changes, preserve response shape, etc.)

Recommended order for backend completion:

1. Build parse endpoint and upload handling
2. Implement chain extraction modules
3. Implement scoring service and flags
4. Add Firebase persistence
5. Integrate PDF payload support

## Quick Start

### Frontend

1. Go to `frontend`
2. Install dependencies: `npm install`
3. Configure environment file from `.env.example`
4. Run: `npm run dev`

### Backend

Backend implementation is scaffolded. See:

- `backend/README.md`
- `backend/src/api/README.md`
- `backend/src/chains/README.md`
- `backend/src/services/README.md`

## Documentation Index

- `docs/01-Frontend-Spec.md`: frontend execution guide
- `docs/02-LangChain-Parsing-Spec.md`: parsing and chain workflow guide
- `docs/03-Scoring-Firebase-PDF-Spec.md`: scoring, Firebase, and PDF guide
- `docs/04-DevOps-QA-Spec.md`: infra, QA, and release guide

---

## OpenClaw Gateway: Features, Integration, and Full Test Guide

### Features

- **Dynamic Skill Discovery:** Auto-detects all skills in `skills/` (e.g., `KamaaiProof`).
- **Skill Manifest Loading:** Reads skill metadata, entry points, and capabilities.
- **Dynamic Invocation:** Runs skill entry points through the OpenClaw gateway.
- **HTTP API Endpoints:** Exposes `/openclaw/skills`, `/openclaw/skills/{skill_name}`, and `/openclaw/invoke`.
- **Pipeline Integration:** `OpenClawExtractor` is wired into `run_pipeline()` and `run_pipeline_batch()`.
- **6-Month Scoring Output:** Summary includes `consistency_score`, `window_months`, and `monthly_income`.
- **Demo Override Mode:** Optional deterministic extraction map for demo docs in `ai-engine/extraction/demo_overrides.json`.

### Current Integration Points

- OpenClaw routes: `ai-engine/api/routes.py`
- Gateway implementation: `ai-engine/extraction/openclaw_gateway.py`
- Extractor integration + fallback: `ai-engine/extraction/base_extractor.py`
- 6-month scoring logic: `ai-engine/pipeline/orchestrator.py`
- Demo scoring runner: `ai-engine/tests/test_demo_scoring.py`

### One-Time Setup

Use Python dependencies from both `ai-engine` and `backend`.

```bash
python -m pip install -r ai-engine/requirements.txt
python -m pip install -r backend/requirements.txt
```

Important compatibility pin:
- `httpx` must be `<0.28.0` for current Groq/OpenClaw path.

Verify:
```bash
python -c "import httpx; print(httpx.__version__)"
```

### End-to-End Test (OpenClaw + API + Pipeline)

1. **Start API server**
   ```bash
   cd ai-engine
   python -m uvicorn main:app --port 8000
   ```

2. **Run OpenClaw API integration tests**
   ```bash
   cd ..
   python ai-engine/test_gateway_api.py
   python ai-engine/test_openclaw_gateway.py
   python ai-engine/tests/test_openclaw.py
   ```

3. **What to expect**
   - Skill listing and skill info should pass.
   - Pipeline tests should complete and print summary output.
   - If Groq rate-limits or runtime deps fail, fallback path should still keep pipeline functional.

### Demo Scoring Test (Recommended for handoff)

For the mixed demo documents in `backend/src/Python_engine/Documents`, run:

```bash
python ai-engine/tests/test_demo_scoring.py
```

This prints:
- `total_income`
- `total_spend`
- `consistency_score`
- `months`
- `window_months` (strict 6-month window)
- `monthly_income`
- `flags`

Use this summary JSON as the contract for PDF work.

### OpenClaw Invocation Example

```bash
python -c "import httpx, json; payload={'skill':'KamaaiProof','input':{'image_path':'backend/src/Python_engine/Documents/payment_may26.jpeg','document_type':'upi'}}; r=httpx.post('http://127.0.0.1:8000/openclaw/invoke', json=payload, timeout=30); print(r.status_code); print(json.dumps(r.json(), indent=2))"
```

### Troubleshooting

- **`Client.__init__() got an unexpected keyword argument 'proxies'`**
  - Ensure `httpx` is pinned to `<0.28.0`, then reinstall requirements.
- **Skill not found**
  - Verify `skills/KamaaiProof/manifest.json` exists and skill name matches.
- **Invocation returns rate-limit / transient API errors**
  - Re-run the request; demo scoring can continue via fallback/override path.
- **Need deterministic demo outputs**
  - Edit `ai-engine/extraction/demo_overrides.json` for filename-level date/amount control.

---
