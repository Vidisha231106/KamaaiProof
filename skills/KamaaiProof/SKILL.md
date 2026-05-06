---
name: kamaaiproof
description: Financial document parsing and Work Passport generation for informal workers.
metadata:
  {
    "openclaw":
      {
        "emoji": "🧾",
        "requires": { "env": ["GROQ_API_KEY"] },
        "install": [],
      },
  }
---

# KamaaiProof

Advanced financial extraction and consistency scoring for informal sector workers.

## When to use (trigger phrases)

Use this skill immediately when the user asks any of:

- “generate a work passport for this user”
- “extract financial data from this receipt/bill”
- “calculate consistency score for [user]”
- “analyze my income/spend patterns”

## Usage

Run the internal Python engine to process documents and generate reports.

```bash
python3 backend/src/Python_engine/pi_engine.py --image [path] --user [id]
```

## Schema

Returns a structured Work Passport including:
- Total Income
- Total Spend
- Consistency Score (0-100)
- Flags for missing data or anomalies
