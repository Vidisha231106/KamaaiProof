# Frontend Services

This folder contains API utilities and response transformation logic.

## Current Modules

- `api.js`
- `transformResult.js`

## Responsibilities

### api.js

- Creates axios client using environment-driven backend base URL.
- Defines API-facing helper methods.
- Sends multipart form payload to parse endpoint.

### transformResult.js

- Normalizes backend responses into stable UI shape.
- Handles variants in key names while backend contract stabilizes.
- Provides demo fallback result for resilience during backend downtime.

## Frontend Internal Result Shape

The UI should consume this normalized shape:

```json
{
	"estimatedMonthlyIncome": 12000,
	"consistencyScore": 78,
	"monthsCovered": 5,
	"documents": [],
	"flags": [],
	"whatsappProvided": true
}
```

## Guidance for AI Agents

1. Do not bypass normalization in page components.
2. Keep parse request method backward compatible.
3. If backend contract is finalized, update normalizer and page assumptions together.
4. Keep timeout and user-facing errors clear and safe.