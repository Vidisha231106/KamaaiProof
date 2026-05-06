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

## OpenClaw Gateway: Features & Testing Guide

### Features

- **Dynamic Skill Discovery:** Auto-detects all skills in `skills/` (e.g., KamaaiProof).
- **Skill Metadata & Manifest Loading:** Reads each skill’s manifest for capabilities and entry points.
- **Dynamic Skill Invocation:** Loads and runs skill code on demand via Python module import.
- **HTTP API Endpoints:** Exposes `/openclaw/skills`, `/openclaw/skills/{skill_name}`, and `/openclaw/invoke` for skill management and execution.
- **Integration with Pipeline:** Can be used directly in the pipeline or via API for document extraction, scoring, and validation.

### What Can Be Tested

- **Skill Listing:** See all available skills via API or CLI.
- **Skill Metadata:** Fetch manifest and config for any skill.
- **Skill Invocation:** Run a skill (e.g., KamaaiProof) on a document and get structured results.
- **End-to-End Pipeline:** Process a document from upload to extraction, validation, and summary via API.

### How to Test End-to-End

1. **Start the Backend:**
   ```bash
   cd ai-engine
   source venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

2. **List Skills:**
   ```bash
   curl http://localhost:8000/openclaw/skills
   # or
   python3 ai-engine/list_openclaw_skills.py
   ```

3. **Get Skill Info:**
   ```bash
   curl http://localhost:8000/openclaw/skills/KamaaiProof
   ```

4. **Invoke a Skill:**
   ```bash
   curl -X POST http://localhost:8000/openclaw/invoke \
     -H "Content-Type: application/json" \
     -d '{
       "skill": "KamaaiProof",
       "input": {"image_path": "path/to/image.jpg"}
     }'
   ```

5. **Run Automated API Tests:**
   ```bash
   python3 ai-engine/test_gateway_api.py
   ```

6. **Validate Results:**
   - Check for `"status": "success"` and review the `"result"` field for extracted transactions, summary, and validation.
   - For errors, review the `"error"` field for missing dependencies or misconfigurations.

### Validation

- **Manual:** Inspect API responses for expected fields and values.
- **Automated:** Use `test_gateway_api.py` for regression and integration checks.
- **Pipeline:** Use `OpenClawExtractor` in your pipeline code to invoke skills programmatically.

---
