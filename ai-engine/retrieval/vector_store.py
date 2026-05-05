"""
retrieval/vector_store.py
=========================
Mock vector store + similarity retrieval.

Purpose:
  - Store sanitized document summaries as "embeddings" (mock numeric vectors).
  - Enable similarity search for MFI officers reviewing worker profiles.

Architecture note:
  Replace `_mock_embed()` with a real embedding model call (e.g., sentence-
  transformers, OpenClaw embeddings) and `_cosine_similarity()` stays as-is.
  The `retrieve_similar()` interface does not change.
"""

import math
import hashlib
from typing import Any


# ──────────────────────────────────────────────────────────────────────────────
# In-memory vector store
# Each entry: { "user_id", "summary_text", "vector", "metadata" }
# ──────────────────────────────────────────────────────────────────────────────

_vector_store: list[dict] = []
_VECTOR_DIM = 64  # mock embedding dimension


def _mock_embed(text: str) -> list[float]:
    """
    Deterministic mock embedding.

    Converts text to a 64-dim float vector using character frequency
    bucketing. Not semantically meaningful, but reproducible and testable.

    REPLACE THIS with a real embedding call when integrating OpenClaw.
    """
    vector = [0.0] * _VECTOR_DIM
    for i, char in enumerate(text):
        bucket = ord(char) % _VECTOR_DIM
        vector[bucket] += 1.0

    # L2 normalize
    magnitude = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / magnitude for v in vector]


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Cosine similarity between two equal-length vectors."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    mag_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return dot / (mag_a * mag_b)


def index_summary(user_id: str, summary_text: str, metadata: dict = None) -> None:
    """
    Embed and store a sanitized summary for a user.

    Only call with PII-free text — summaries are what gets indexed.
    """
    vector = _mock_embed(summary_text)
    _vector_store.append({
        "user_id": user_id,
        "summary_text": summary_text,
        "vector": vector,
        "metadata": metadata or {},
    })


def retrieve_similar(query_text: str, top_k: int = 3) -> list[dict]:
    """
    Find the top_k most similar summaries to query_text.

    Returns list of { user_id, summary_text, score, metadata }.
    """
    if not _vector_store:
        return []

    query_vec = _mock_embed(query_text)
    scored = []
    for entry in _vector_store:
        score = _cosine_similarity(query_vec, entry["vector"])
        scored.append({
            "user_id": entry["user_id"],
            "summary_text": entry["summary_text"],
            "score": round(score, 4),
            "metadata": entry["metadata"],
        })

    # Sort descending by similarity score
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def store_size() -> int:
    """Number of indexed entries (for diagnostics)."""
    return len(_vector_store)
