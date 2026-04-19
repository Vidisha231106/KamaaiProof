# Person 2 — LangChain Chains + Document Parsing Developer Execution Guide

## Overview & Expected Output
**Goal:** Build the core AI Layer. Use LangChain and Anthropic (Claude Sonnet) to extract highly structured JSON data from random, messy user uploads (images, PDFs, text).
**Estimated Time:** 10–12 hours

---

## Step-by-Step Execution Guide

### Step 1: Backend Server Setup (Hours 1-2)
1. Navigate to the `backend/` directory. Initialize a Node.js project (`npm init -y`) or Python project (`poetry init` / `pip install fastapi uvicorn`).
2. **Install Dependencies:**
   - *Node:* `express`, `cors`, `dotenv`, `langchain`, `@langchain/anthropic`, `multer` (for file parsing).
   - *Python:* `fastapi`, `uvicorn`, `python-multipart`, `langchain`, `langchain-anthropic`, `pydantic`.
3. Create `src/server.js` (or `main.py`) with a simple GET `/health` endpoint to verify the server is running.
4. **Environment Variables:** Load `ANTHROPIC_API_KEY` from `.env`.

### Step 2: Configure LLM & Schemas (Hours 3-4)
1. Instantiate the LLM: Initialize Claude Sonnet using the LangChain wrapper. Set temperature to `0` for strict, deterministic extraction.
2. **Define Output Parsers (Zod/Pydantic):**
   - *UPI Schema:* `{ date: string, amount: number, senderName: string }`
   - *Utility Bill Schema:* `{ billingAddress: string, monthYear: string, consumerName: string, amountDue: number }`
   - *Receipt Schema:* `{ paymentDate: string, amount: number, employerName: string }`
   - *WhatsApp Schema:* `[{ date: string, amount: number, unverified: boolean }]` (Hardcode `unverified: true` for this schema).

### Step 3: Build Specific Chains (Hours 5-7)
1. Under `src/chains/`, create four separate chain files (or functions):
   - `upiChain`: Takes OCR/Image data -> Prompts Claude to extract UPI structure.
   - `billChain`: Takes OCR/Image data -> Prompts Claude to extract Bill structure.
   - `receiptChain`: Takes OCR/Image data -> Prompts Claude to extract Receipt structure.
   - `whatsappChain`: Takes raw text string -> Prompts Claude to extract payment mentions structure.
2. **Prompt Templates:** For each chain, build a `PromptTemplate`.
   - Include specific instructions: *You are a data extractor. Return EXACTLY the JSON schema provided, nothing else.*
   - Inject the format instructions from your structured output parser.

### Step 4: Parallel Chain Execution Logic (Hours 8-9)
1. Create a `orchestrator.js` (or `orchestrator.py`).
2. Create a function that accepts an array of documents (with their user-assigned tags).
3. Use `RunnableParallel` or `Promise.all()` / `asyncio.gather()` to route each document to its corresponding chain concurrently based on its tag.
4. Flatten the output. Convert the parallel results into a single list of `transactions` or `records`.

### Step 5: The API Endpoint (Hours 10-12)
1. Add a `POST /parse` route in your server.
2. **File Handling:** Use `multer` (Node) or `UploadFile` (FastAPI) to handle form-data containing the images/PDFs and the WhatsApp text.
3. **Preprocessing:** Since Claude needs text, decide on whether you are passing image base64 directly to Claude 3 (Vision), or if you are using an OCR utility first (e.g., Tesseract/pdf2image). Passing Base64 image payload to LangChain/Claude Vision is the easiest route.
4. Call your orchestration function with the incoming data.
5. Return the final structured JSON object to the client.
6. Verify against Postman/cURL before handing off to Person 3.
