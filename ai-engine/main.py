"""
main.py
=======
KamaaiProof AI Engine — FastAPI application entry point.

Run with:
  uvicorn main:app --reload --port 8000

This server runs on port 8000 to match the frontend's VITE_BACKEND_API_URL default.
"""

import os

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
# Reads ALLOWED_ORIGINS from the environment (comma-separated), falling back
# to sensible local-dev defaults + the production Vercel URL.
_env_origins = [
    o.strip().rstrip("/")
    for o in os.getenv("ALLOWED_ORIGINS", "").split(",")
    if o.strip()
]
_default_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:5175",
    "http://localhost:3000",
    "http://localhost:4173",
    "https://kamaai-proof.vercel.app",   # production Vercel frontend
]
# Merge, deduplicate, keep order
_seen: set[str] = set()
_allowed_origins: list[str] = []
for _o in _default_origins + _env_origins:
    if _o not in _seen:
        _seen.add(_o)
        _allowed_origins.append(_o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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
