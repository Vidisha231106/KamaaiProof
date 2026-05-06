# KamaaiProof

## Overview
This skill enables an AI agent to process messy, informal financial documents (UPI screenshots, utility bills, rent receipts) and extract structured JSON data with high precision. It transitions from legacy OCR-based retrieval to a **Vision-First OpenClaw pipeline** optimized for the Indian informal economy.

## Capabilities
- **Document Classification**: Native multi-modal identification of document types (GPay, PhonePe, BHIM, Electricity, Water, Rent).
- **Vision-First Extraction**: Uses **Llama 4 Scout (17B Multimodal)** to "see" and interpret visual data, handwritten text, and currency symbols (₹) directly from images.
- **Privacy-First Sanitization**: Automatic masking of PII (Names, Phone Numbers, UPI IDs, Bank Accounts) at the ingestion layer using OpenClaw-ready filters.
- **Business Rule Validation**: Enforces strict validation on transaction amounts, ISO 8601 dates, and transaction directions (Credit/Debit).
- **Confidence Scoring**: Dynamic scoring based on field completeness and LLM self-assessment.

## Pipeline Architecture (OpenClaw Simulation)
1. **Perception**: Image is ingested and processed by the Vision LLM (`meta-llama/llama-4-scout-17b-16e-instruct`).
2. **Extraction**: Structured JSON is generated, with resilient logic to handle nested "fields" or "data" blocks.
3. **Sanitization**: Textual descriptions are scrubbed of PII before reaching the storage layer.
4. **Validation**: Business rules verify the integrity of the extraction (e.g., rejecting future-dated bills).
5. **Storage & Indexing**: PII-free records are stored and indexed for similarity search via a vector store.

## Input Specification
- `image_path`: String path to the document image (JPG, PNG).

## Output Specification (Work Passport Payload)
```json
{
  "status": "PROCESSED",
  "extracted_data": {
    "amount": 0.0,
    "date": "YYYY-MM-DD",
    "transaction_type": "credit|debit",
    "description": "Sanitized transaction context",
    "confidence": 0.0-1.0
  },
  "validation": {
    "is_valid": true,
    "issues": []
  }
}
```

## Setup & Dependencies
- **LLM**: Groq API with `meta-llama/llama-4-scout-17b-16e-instruct`.
- **Logic**: Python 3.12+ with `pydantic`, `opencv-python-headless`, and `python-dotenv`.
- **Legacy OCR**: `pytesseract` (retained for anchor-based fallback).
- **Schemas**: Located in `backend/src/Python_engine/Schemas/`.
