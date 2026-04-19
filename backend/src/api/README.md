# API Layer

This folder owns HTTP route handlers and request/response contracts.

## Responsibilities

- Define backend routes and route-level middleware.
- Validate incoming request shape and required form fields.
- Forward clean input to chain and scoring services.
- Return stable JSON responses expected by frontend.
- Convert exceptions into plain-language error messages.

## Required Routes

1. `GET /health`
2. `POST /parse`

Optional future routes:

- `POST /score` if parsing and scoring are separated
- `GET /session/:id` for retrieval of stored summaries

## Parse Route Input Contract

- Content type: multipart form-data
- Keys:
	- `files` (repeated)
	- `metadata` (JSON string with per-file tags)
	- `whatsappText` (optional plain text)

## Parse Route Output Contract

Target stable shape:

```json
{
	"consistencyScore": 78,
	"totalIncome": 12000,
	"months": ["2025-10", "2025-11"],
	"transactions": [],
	"flags": []
}
```

## Error Handling Rules

- Return user-safe messages.
- Do not leak stack traces in production responses.
- Include status code classes:
	- 400 for malformed input
	- 422 for parseable request but invalid payload semantics
	- 500 for unhandled server failures

## Guidance for AI Agents

Before adding new endpoints:

1. Check frontend service contract in `frontend/src/services/api.js`.
2. Preserve backward compatibility unless a coordinated frontend change exists.
3. Keep routes thin; business logic should live in services or chain modules.