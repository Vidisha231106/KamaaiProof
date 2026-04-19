# KamaaiProof Backend

This folder will hold all server-side logic for document parsing, extraction orchestration, consistency scoring, and persistence.

## Backend Scope

The backend is responsible for:

- Receiving uploads from frontend
- Running extraction chains by document type
- Returning structured records for each source
- Computing reliability and consistency scoring
- Producing warning flags in plain language
- Persisting safe session summaries (without sensitive raw identifiers)

The backend is not responsible for:

- Visual styling and UI interactions
- Frontend route logic

## Planned Stack

Either of the following is valid based on team preference:

- Python: FastAPI + LangChain + Anthropic SDK + firebase-admin
- Node: Express + LangChain + Anthropic SDK + firebase-admin

Choose one stack and keep it consistent across all backend folders.

## Folder Layout

```
backend/
	src/
		api/       # HTTP route handlers
		chains/    # LangChain prompts, schemas, orchestration
		services/  # scoring, persistence, shared utilities
```

## Required Endpoint Contract

Primary endpoint expected by frontend:

- `POST /parse`

Incoming payload:

- multipart form-data
- repeated `files`
- `metadata` as JSON string array containing tags
- optional `whatsappText`

Target response shape:

```json
{
	"consistencyScore": 0,
	"totalIncome": 0,
	"months": [],
	"transactions": [],
	"flags": []
}
```

## Data and Privacy Guardrails

Mandatory rules for all implementations:

- Do not store full personal identifiers in final scored records.
- Avoid persisting names, phone numbers, and UPI IDs in Firestore score summaries.
- Keep WhatsApp-derived entries marked as unverified.
- Return plain-language flags that are understandable by non-technical users.

## Suggested Implementation Sequence

1. Add health route and parse route skeleton in api layer.
2. Implement upload parsing and metadata binding.
3. Implement chain-level extraction per document type.
4. Implement orchestration and normalization to common transaction shape.
5. Implement scoring and flag generation.
6. Add persistence service to Firebase.
7. Harden error handling and timeout behavior.

## Testing Priorities

- Route-level request validation
- Schema conformance for extraction output
- Scoring edge cases (missing months, round numbers, mixed categories)
- Backend timeout and malformed input behavior
- CORS compatibility for localhost and deployed frontend domain

## Guidance for AI Agents Editing Backend

1. Read the READMEs in api, chains, and services before editing.
2. Preserve the parse response contract used by frontend.
3. Keep extraction output structured and machine-parseable.
4. Never leak secrets into committed files.
5. Add small, composable modules instead of large monolithic handlers.
