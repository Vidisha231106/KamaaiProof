# KamaaiProof — Migrate to Supabase (Storage + Database)

Replace the in-memory Python dict and browser `localStorage` with a real Supabase backend: file uploads go into **Storage buckets**, parsed results go into **Postgres tables**.

---

## What currently exists (no Supabase at all)

| Layer | Current state |
|---|---|
| Backend store | `storage/store.py` — plain Python `defaultdict` in RAM, wiped on restart |
| Frontend result cache | `localStorage` key `kamaaiproof-last-result` |
| File storage | Files are read in `routes.py`, decoded to text, then discarded — originals never persisted |
| Schema | None defined anywhere — only the `Transaction` Pydantic model and `_build_summary()` shape |
| Supabase | Zero references across the entire project |

---

## Proposed Architecture

```
User uploads files
       │
       ▼
FastAPI /parse endpoint
       ├─► Upload raw files → Supabase Storage bucket: document-uploads/{session_id}/filename
       ├─► Run AI pipeline (unchanged)
       └─► Write to Supabase Postgres:
               sessions      (one row per upload batch)
               transactions  (one row per parsed document)
       │
       ▼
Returns JSON → Frontend renders ResultPage
(result is no longer stored in localStorage — fetched by session_id from Supabase if needed)
```

---

## Database Schema (new — no pre-existing schema found)

### Table: `sessions`
Stores one row per user submission batch.

```sql
create table public.sessions (
  id            uuid primary key default gen_random_uuid(),
  created_at    timestamptz not null default now(),
  consistency_score   int not null default 0,
  total_income        numeric(12,2) not null default 0,
  avg_monthly_income  numeric(12,2) not null default 0,
  months_covered      text[] not null default '{}',
  window_months       text[] not null default '{}',
  monthly_income      jsonb not null default '{}',
  flags               text[] not null default '{}',
  avg_confidence      numeric(4,2) not null default 0,
  transaction_count   int not null default 0
);
```

### Table: `transactions`
One row per parsed document within a session.

```sql
create table public.transactions (
  id              uuid primary key default gen_random_uuid(),
  session_id      uuid not null references public.sessions(id) on delete cascade,
  created_at      timestamptz not null default now(),
  source          text not null,          -- "upi" | "rent" | "bill"
  amount          numeric(12,2),
  date            date,
  frequency       text,                   -- "monthly" | "one_time" | etc.
  transaction_type text,                  -- "credit" | "debit" | "unknown"
  description     text,
  confidence      numeric(4,2),
  verified        boolean not null default false,
  document_url    text                    -- Supabase Storage public URL
);
```

### Storage Bucket: `document-uploads`
- One folder per session: `document-uploads/{session_id}/{filename}`
- Bucket policy: **private** (only the backend service role can read/write)

---

## Files to Create / Modify

---

### Supabase Client (Python)

#### [NEW] `ai-engine/storage/supabase_client.py`
Initialises the `supabase-py` client from env vars. Shared singleton imported by `store.py` and `routes.py`.

---

### Storage Layer

#### [MODIFY] `ai-engine/storage/store.py`
Replace the in-memory `defaultdict` with Supabase Postgres calls.  
`save()` will insert into `sessions` + `transactions`.  
`get_results()` will query by `session_id`.

---

### API Routes

#### [MODIFY] `ai-engine/api/routes.py`
In `parse_multipart()`:
1. Generate a `session_id = uuid4()` at the top of the request.
2. **Before** running the pipeline: upload each raw file to `document-uploads/{session_id}/{filename}` and capture the storage URL.
3. Pass the `session_id` and `document_url` map into the pipeline/store so each transaction row gets its `document_url` populated.
4. Return `session_id` in the JSON response so the frontend can reference it.

---

### Environment Variables

#### [MODIFY] `ai-engine/.env`
Add:
```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

#### [NEW] `frontend/.env` (or `frontend/.env.local`)
```
VITE_BACKEND_API_URL=http://localhost:8000
```
(already works, no Supabase keys needed in frontend — all DB access goes through the FastAPI backend)

---

### Requirements

#### [MODIFY] `ai-engine/requirements.txt`
Add `supabase>=2.4.0`

---

### Frontend

#### [MODIFY] `frontend/src/pages/UploadPage.jsx`
- Remove `localStorage.setItem(...)` call (already in `goToResult` but result is now derived from the backend response which includes `session_id`).
- Pass `session_id` through router state alongside `result`.

#### [MODIFY] `frontend/src/pages/ResultPage.jsx`
- Remove `localStorage.getItem(...)` fallback.
- If `result` is absent from router state, show "session expired" rather than pulling stale data from localStorage.

---

## Supabase Cloud Setup — Step-by-Step Guide

This will be written into the final walkthrough after implementation.

> [!IMPORTANT]
> **One open question for you:** Do you want users to be able to re-fetch their old results by `session_id` (i.e., should the frontend hit a `GET /session/{id}` endpoint)? Or is one-shot (upload → result → done) enough for now? This determines whether I wire up the retrieval endpoint.

---

## Verification Plan

### Automated
- Upload `sample3.txt` via `/parse` → confirm `sessions` table has a new row in Supabase dashboard
- Confirm `transactions` table has the extracted row
- Confirm file appears in `document-uploads` bucket

### Manual
- Open Supabase Studio → Table Editor → verify data shape
- Check bucket → verify file uploaded
- Reload ResultPage → confirm result comes from router state (not localStorage)
