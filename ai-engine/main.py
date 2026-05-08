"""
main.py
=======
KamaaiProof AI Engine — FastAPI application entry point.

Run with:
  uvicorn main:app --reload --port 8000

This server runs on port 8000 to match the frontend's VITE_BACKEND_API_URL default.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="KamaaiProof AI Engine",
    description=(
        "Modular AI backend for processing informal worker financial documents. "
        "Converts raw/noisy OCR text into structured JSON with validation, "
        "privacy sanitization, and scoring."
    ),
    version="1.0.0",
    docs_url="/docs",       # Swagger UI at /docs
    redoc_url="/redoc",     # ReDoc at /redoc
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the frontend (Vite dev server on port 5173) to call this API.
# Tighten origins in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:4173",
    "https://kamaai-proof.vercel.app/",   # ← replace with real Vercel URL
],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────────────────
app.include_router(router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "service": "KamaaiProof AI Engine",
        "version": "1.0.0",
        "endpoints": {
            "process_document": "POST /process-document",
            "parse_frontend": "POST /parse",
            "get_results": "GET /results/{user_id}",
            "retrieve_similar": "POST /retrieve",
            "health": "GET /health",
            "docs": "GET /docs",
        },
    }
