"""
storage/supabase_client.py
==========================
Shared Supabase client singleton.

If SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not set,
get_client() returns None and the store falls back to in-memory mode.
This lets the backend run locally without Supabase configured.
"""

import os
from dotenv import load_dotenv

load_dotenv()

_client = None
_initialized = False


def get_client():
    """
    Return the initialised Supabase client, or None if not configured.
    Safe to call repeatedly — initialisation happens at most once.
    """
    global _client, _initialized
    if _initialized:
        return _client

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()

    if not url or not key:
        print("[Supabase] SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set — using in-memory fallback.")
        _initialized = True
        return None

    try:
        from supabase import create_client  # lazy import — optional dependency
        _client = create_client(url, key)
        print("[Supabase] Client initialised successfully.")
    except Exception as exc:
        print(f"[Supabase] Failed to initialise client: {exc}")
        _client = None

    _initialized = True
    return _client


def is_configured() -> bool:
    """True if both required env vars are present."""
    return bool(
        os.getenv("SUPABASE_URL", "").strip()
        and os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
