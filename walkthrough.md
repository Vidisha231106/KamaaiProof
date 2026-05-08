# KamaaiProof — End-to-End Run Guide

> **Goal:** Start both servers, upload a bill, see real parsed results, and download the PDF.

---

## Prerequisites (one-time)

| Tool | Check | Install if missing |
|---|---|---|
| Python ≥ 3.11 | `python --version` | https://python.org |
| Node.js ≥ 18 | `node --version` | https://nodejs.org |
| pip packages for ai-engine | See Step 1 | — |
| npm packages for frontend | See Step 2 | — |

---

## Step 1 — Install Backend Dependencies

Open a terminal in the **project root** (`KamaaiProof/`):

```powershell
pip install -r ai-engine/requirements.txt
pip install python-dotenv groq
```

> **Note:** `groq` is optional. Without it the backend still works — it falls back to regex extraction. You only need it for LLM-powered image reading.

---

## Step 2 — Install Frontend Dependencies (if not already done)

```powershell
cd frontend
npm install
```

---

## Step 3 — Start the Backend (AI Engine)

Open **Terminal 1**. Navigate to the ai-engine folder:

```powershell
cd ai-engine
python -m uvicorn main:app --port 8000 --reload
```

**What you should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

> The Swagger UI (interactive API docs) is available at: **http://localhost:8000/docs**
> Health check: **http://localhost:8000/health**

---

## Step 4 — Start the Frontend

Open **Terminal 2**. Navigate to the frontend folder:

```powershell
cd frontend
npm run dev
```

**What you should see:**
```
VITE v5.x.x  ready in ~2000ms
➜  Local:   http://localhost:5173/
```

Open **http://localhost:5173** in your browser.

---

## Step 5 — Prepare Your Bill Document

> [!IMPORTANT]
> **The current `/parse` backend reads uploaded files as plain text (UTF-8).** This means:
> - ✅ **Text files (`.txt`)** work perfectly — amount, date, and category are extracted via regex
> - ⚠️ **Images (`.jpg`, `.png`)** are read as raw bytes decoded as UTF-8, which returns garbage text. The regex extractor then falls back on the OpenClaw fallback and returns a default amount.
> - ✅ **If you have a GROQ_API_KEY** (free at https://console.groq.com/keys), add it to `ai-engine/.env` and the Groq Vision LLM path activates for images

### Option A: Upload a Text Bill (Works out of the box)

Create a `.txt` file with your bill's key details. Example — save as `electricity_bill.txt`:

```
BESCOM Electricity Bill
Consumer Number: 56789012
Billing Period: April 2026
Due Date: 15 Apr 2026
Amount Due: Rs. 2,450
Previous Reading: 3280 units
Current Reading: 3410 units
Address: 12 Brigade Road, Bangalore
```

The extractor will find `Rs. 2,450` → amount = 2450, `15 Apr 2026` → date, and classify it as a debit (bill).

### Option B: UPI Payment Screenshot (as text)

Save as `upi_payment.txt`:
```
Google Pay
Payment Successful
Amount: ₹3,500 received
From: Employer
Date: 20 Apr 2026
Reference: 123456789012
```

This will extract ₹3,500 as a credit transaction for April 2026.

### Option C: Rent Receipt (as text)

Save as `rent_receipt.txt`:
```
Rent Receipt
Received from tenant
Monthly Rent: Rs 8000
For the month of: March 2026
Payment Date: 01 Mar 2026
```

---

## Step 6 — Upload on the Frontend

1. Go to **http://localhost:5173**
2. Click **"Start Building Passport"**
3. On the Upload page:
   - **Drag and drop** your `.txt` file(s) into the upload box (or click to browse)
   - For each file, use the **dropdown** to select its type:
     - Electricity/water/gas text → **"Utility Bill"**
     - GPay/PhonePe/BHIM text → **"UPI Screenshot"**
     - Rent receipt text → **"Receipt"**
   - Add at least **3 tagged files** (the "Generate Passport" button stays disabled until then)
   - Optionally paste WhatsApp payment messages in the text area at the bottom
4. Click **"Generate Passport"**

---

## Step 7 — Watch the Backend Parse

In **Terminal 1** (uvicorn), you'll see live logs like:

```
INFO:     127.0.0.1:57432 - "POST /parse HTTP/1.1" 200 OK
INFO:OpenClawExtractor:[OpenClawExtractor] Using skill: KamaaiProof
INFO:OpenClawExtractor:[OpenClawExtractor] Raw Vision Data: ...
INFO:[FallbackExtractor] OpenClaw failed, falling back to MockExtractor.
```

The fallback to `MockExtractor` (regex) is **normal** without a Groq API key — you still get real extracted amounts and dates from your text.

---

## Step 8 — Read the Result Page

After ~2-5 seconds, you land on the Result page. You'll see:

| Field | What it means |
|---|---|
| **Estimated Monthly Income** | Sum of all credit transactions found across covered months |
| **Consistency Score** | 0–100. Based on: how many of the last 6 months have income records (70 pts) + how stable the income is month-to-month (30 pts) |
| **Months Covered** | How many distinct months in the last 6 months had at least one income record |
| **Parsed Documents table** | Every transaction extracted: source file, category, date, amount, Verified/UNVERIFIED status |
| **Manual Review Warnings** | Flags like "Income evidence missing in 5 months" or "Low confidence extraction" |
| **Loan Reality Check** | Moneylender vs MFI repayment comparison in ₹ |

---

## Step 9 — Download the Work Passport PDF

At the bottom of the Result page, you'll see 3 buttons in the action row:

1. **"Loading PDF…"** → briefly appears while `@react-pdf/renderer` initialises (1–2 seconds)
2. **"Download Work Passport"** ← click this once it appears (teal/green button)
3. A file named `KamaaiProof-WorkPassport-YYYY-MM-DD.pdf` downloads

**The PDF contains:**
- Dark header: KamaaiProof branding + generation date
- Summary cards: Income / Score (colour-coded) / Months covered
- Full transactions table with UNVERIFIED badges for WhatsApp rows
- Flags section (if any warnings)
- Disclaimer footer for MFI loan officers

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| "Generate Passport" button stays grey | Fewer than 3 files are tagged | Assign a type to each file from the dropdown |
| Backend returns `consistencyScore: 0` | No text with amounts/dates found | Use `.txt` format with `Rs.` or `₹` amounts and a date like `15 Apr 2026` |
| "PDF unavailable" button | `@react-pdf/renderer` failed to load | Hard-refresh the page (Ctrl+Shift+R) |
| Backend won't start: `ModuleNotFoundError` | Missing pip packages | Run `pip install -r ai-engine/requirements.txt && pip install python-dotenv` |
| CORS error in browser console | Backend not running | Check Terminal 1 — restart `uvicorn main:app --port 8000 --reload` |
| Images return 0 amounts | Binary image decoded as UTF-8 | Use `.txt` files, or add `GROQ_API_KEY` to `ai-engine/.env` for vision extraction |

---

## Quick Test Without Any Files

On the Upload page, click **"Open Demo Result"** — this skips the API entirely and loads pre-canned demo data directly in the browser. The PDF download works immediately from the demo result. Use this to verify the PDF generation works before worrying about real document parsing.

---

## Architecture Reminder

```
Your bill .txt ─→ Upload Page (React)
                     │  POST /parse  multipart/form-data
                     ▼
              AI Engine (FastAPI :8000)
                     │
                ┌────┴─────────────────────────┐
                │ 1. Sanitize PII              │
                │ 2. Extract (regex heuristics) │
                │    → amount, date, type       │
                │ 3. Validate                   │
                │ 4. Score (6-month window)     │
                │ 5. Return JSON                │
                └──────────────────────────────┘
                     │
              Result Page (React)
                     │  dynamic import
                     ▼
         @react-pdf/renderer → PDF blob → Download
```
