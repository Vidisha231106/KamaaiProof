# Services Layer

This folder contains backend business logic that should not live inside HTTP routes.

## Responsibilities

- Consistency scoring logic
- Flag generation logic
- Firebase persistence helpers
- Data sanitization utilities
- Shared helpers for date grouping and amount calculations

## Core Service Modules (Planned)

1. `scoringService`
2. `flagService`
3. `firebaseService`
4. `sanitizationService`

## Scoring Baseline (Expected)

- Group records by calendar month.
- Evaluate last 6 months for activity coverage.
- Compute base score out of 100.
- Apply deductions for suspicious patterns (for example round-number dominance).
- Apply deductions for cross-document mismatches (for example address mismatches).
- Return both score and plain-language flags.

## Service Output Contract

```json
{
	"consistencyScore": 78,
	"totalIncome": 12000,
	"months": ["2025-10", "2025-11"],
	"transactions": [],
	"flags": ["Address mismatch detected"]
}
```

## Privacy Requirements

- Do not store sensitive personal identifiers in persisted score summaries.
- Persist only required operational fields such as amounts, dates, categories, score, and flags.
- Keep provenance labels (verified or unverified) intact.

## Guidance for AI Agents

1. Keep services pure where practical and isolate side effects.
2. Write deterministic scoring logic and avoid hidden random behavior.
3. Ensure date handling is timezone-aware and documented.
4. Add unit tests before adjusting scoring rules.