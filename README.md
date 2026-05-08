# KamaaiProof
### Work Passport for India's Invisible Workforce

> **Live Demo:** [https://kamaai-proof.vercel.app](https://kamaai-proof.vercel.app)

---

## Problem

India's informal workforce — domestic workers, auto drivers, street vendors, and daily wage laborers — earns consistently but lacks formal proof of income. Salary slips, employer letters, and credit histories simply don't exist for this segment.

Income evidence is scattered across:
- UPI screenshots
- Utility bills
- Rent receipts
- Employer WhatsApp messages

The gap is not income creation — it's **evidence assembly and presentation quality**. Lenders and MFIs cannot process what they cannot read.

---

## Solution

KamaaiProof collects user-submitted records, parses them with AI, applies consistency checks, and returns a **Work Passport** — a lender-readable proof packet that turns informal documents into structured financial evidence.

**Primary outputs:**
- Estimated monthly income
- Consistency score (out of 100)
- Parsed document list with dates, amounts, and verification status
- Plain-language warnings and fraud flags
- Downloadable Work Passport PDF (generated client-side)

---

## Architecture

```
User (Google OAuth)
        ↓
  React Frontend (Vercel)
        ↓  multipart/form-data + Bearer token
  FastAPI AI Engine (Render)
        ↓
  Groq Vision (OCR + extraction)
        ↓
  Supabase (auth + persistence)
        ↓
  Frontend renders score, transactions, warnings
        ↓
  @react-pdf/renderer → Work Passport PDF
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI + Uvicorn (Python) |
| AI / OCR | Groq Vision (llama-4 vision) |
| Auth | Supabase (Google OAuth) |
| Database | Supabase (Postgres + RLS) |
| PDF | @react-pdf/renderer (client-side) |
| Frontend Deploy | Vercel |
| Backend Deploy | Render |

---

## Repository Structure

```
KamaaiProof/
├── ai-engine/          # FastAPI backend
│   ├── extraction/     # Groq vision extraction + OpenClaw gateway
│   ├── pipeline/       # Orchestration + 6-month scoring
│   ├── validation/     # Field validation
│   ├── sanitization/   # PII scrubbing
│   ├── storage/        # Supabase client
│   ├── security/       # Auth + RBAC
│   └── api/            # Route definitions
├── frontend/           # React + Vite app
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
└── docs/               # Spec documents
```

---

## Local Setup

### Prerequisites
- Node.js 18+
- Python 3.11+
- A Supabase project
- A Groq API key

---

### 1. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env`:
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_BACKEND_API_URL=http://localhost:8000
```

```bash
npm run dev
```

---

### 2. AI Engine (Backend)

```bash
cd ai-engine
pip install -r requirements.txt
```

Create `ai-engine/.env`:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-key
```

```bash
uvicorn main:app --port 8000 --reload
```

---

### 3. Supabase Schema

Run once in Supabase SQL Editor:

```sql
alter table sessions add column if not exists user_id uuid references auth.users(id);
alter table transactions add column if not exists user_id uuid references auth.users(id);

alter table sessions enable row level security;
alter table transactions enable row level security;

create policy "sessions_select_own" on sessions for select using (auth.uid() = user_id);
create policy "sessions_insert_own" on sessions for insert with check (auth.uid() = user_id);
create policy "transactions_select_own" on transactions for select using (auth.uid() = user_id);
create policy "transactions_insert_own" on transactions for insert with check (auth.uid() = user_id);
```

---

### 4. Google OAuth

1. In Google Cloud Console, add redirect URI:
   `https://YOUR_PROJECT.supabase.co/auth/v1/callback`
2. In Supabase → Authentication → URL Configuration:
   - Site URL: `http://localhost:5173`
   - Redirect URLs: `http://localhost:5173`, `http://localhost:5173/upload`
3. In Supabase → Providers → Google: paste Client ID + Secret

---

## Usage

1. Sign in with Google
2. Upload informal income documents (UPI screenshots, receipts, utility bills)
3. Wait for AI extraction and scoring
4. View your Work Passport — income summary, consistency score, parsed transactions
5. Download the PDF to share with lenders or MFI field officers

---

## API Contract

**Endpoint:** `POST /parse`  
**Auth:** `Bearer <supabase_access_token>`  
**Content-Type:** `multipart/form-data`

| Field | Type | Description |
|---|---|---|
| `files` | File[] | Document files |
| `metadata` | JSON string | Per-file tags and metadata |
| `whatsappText` | string (optional) | Plain text from WhatsApp |
| `sessionId` | UUID (optional) | Client-generated for retry safety |

**Response:**
```json
{
  "session_id": "uuid",
  "consistencyScore": 78,
  "totalIncome": 12000,
  "months": ["2025-10", "2025-11", "2025-12"],
  "transactions": [
    {
      "id": "tx-1",
      "source": "gpay_screenshot.jpg",
      "category": "UPI Screenshot",
      "date": "2026-02-06",
      "amount": 2500,
      "verified": true
    }
  ],
  "flags": ["Address mismatch detected across utility bills"]
}
```

---

## Target Personas

1. **Informal worker** — primary beneficiary, submits documents to build their Work Passport
2. **SHG leader** — assists with document collection and onboarding
3. **MFI field officer** — uses the summary to reduce manual verification time

---

## Known Limitations

- Vision/OCR quality depends on Groq configuration; plain text files are most reliable
- Large document batches may hit Groq rate limits; retry if needed
- Work Passport is supporting evidence only — not a loan approval decision

---

## Privacy

- Raw PII (names, phone numbers, UPI IDs) is not persisted in scored records
- WhatsApp-derived records are explicitly labeled unverified
- Users control their own data flow; output is evidence, not a credit score

---

## Documentation

## 🎥 Demo Video

👉 [Watch the full walkthrough here](https://drive.google.com/file/d/15u-VTZ2A4oxDs_xcZyafK1uI7GySnwwg/view?usp=sharing)

> See KamaaiProof in action — document upload, AI extraction, scoring, and Work Passport PDF generation.

