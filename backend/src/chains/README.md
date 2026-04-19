# Chains Layer

This folder owns all LangChain extraction logic.

## Responsibilities

- Build prompt templates for each document category.
- Define structured output schemas and parsers.
- Run extraction chains by category.
- Orchestrate parallel execution for mixed uploads.
- Normalize extracted records into a common transaction format.

## Expected Chain Modules

- `upiChain` for UPI screenshots
- `billChain` for utility bills
- `receiptChain` for receipts
- `whatsappChain` for plain text payment references
- `orchestrator` for routing documents to chains and combining output

## Output Normalization Target

Every chain should eventually map to a unified object shape:

```json
{
	"id": "record-1",
	"source": "filename_or_text",
	"category": "UPI Screenshot",
	"date": "2026-01-10",
	"amount": 2500,
	"verified": true
}
```

For WhatsApp-derived records:

- `verified` should be false
- category should clearly indicate WhatsApp source

## Prompting Rules

- Use extraction-specific prompts, not general-purpose prompts.
- Force strict schema output.
- Set low temperature for consistency.
- Include explicit instructions to avoid extra prose around JSON.

## Quality and Safety Notes

- Handle blurry or partial documents gracefully.
- Return best-effort extraction with confidence hints if needed.
- Avoid hallucinated fields when evidence is missing.
- Prefer null or empty values to fabricated values.

## Guidance for AI Agents

1. Keep each chain in a separate module.
2. Keep schemas versioned or clearly documented when changed.
3. Add tests for each chain parser output shape.
4. Keep orchestration deterministic and easy to trace.