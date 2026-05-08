# AI Disclosure

This document describes how AI tools and models were used in the development and operation of KamaaiProof.

---

## AI Models Used in the Product

### Groq — Vision Extraction (Core Feature)
- **Model:** `meta-llama/llama-4-scout-17b-16e-instruct` (via Groq API)
- **Purpose:** Extracts structured financial data from uploaded documents — UPI screenshots, rent receipts, utility bills, and similar informal records
- **How it works:** Images are sent to Groq Vision which returns structured JSON containing transaction date, amount, category, and confidence level
- **Location in codebase:** `ai-engine/extraction/extractor.py` → `extract_with_pure_vision()`

---

## AI Tools Used During Development

### Claude (Anthropic)
- Used to scaffold the FastAPI backend structure, route definitions, and pipeline orchestration logic
- Used to write and debug the Supabase RLS policies and auth integration
- Used to generate the OpenClaw gateway integration and skill loader
- Used to review and improve the scoring algorithm in `pipeline/orchestrator.py`
- Used to assist with deployment configuration (Render + Vercel setup)

### GitHub Copilot
- Used for inline code completion during frontend React component development
- Assisted with `@react-pdf/renderer` layout for the Work Passport PDF

---

## What AI Did Not Do

- AI did not define the product concept, target personas, or problem framing — these came from the team's research into India's informal workforce
- AI did not make decisions about privacy guardrails or data handling policy — these were defined by the team
- All AI-generated code was reviewed, tested, and modified by the development team before use
- The Work Passport output is AI-assisted evidence assembly — it is **not** a credit scoring or loan approval decision

---

## Data Privacy in AI Calls

- Document images are sent to Groq's API for processing; no raw PII is stored in the application database
- Names, phone numbers, and UPI IDs extracted from documents are sanitized before persistence (`ai-engine/sanitization/sanitizer.py`)
- No user data is used to train any model

---

## Model Limitations Acknowledged

- OCR accuracy depends on image quality; low-resolution or blurry documents may produce incomplete extractions
- The consistency score is a heuristic based on transaction patterns — it is not a financial risk model
- WhatsApp-derived text is treated as unverified by design
