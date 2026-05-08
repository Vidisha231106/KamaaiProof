"""
api/routes.py
=============
FastAPI route definitions for KamaaiProof AI Engine.

Endpoints:
  POST /process-document   — full AI pipeline for a single document
  POST /parse              — alias matching the existing frontend contract
  GET  /results/{user_id} — retrieve stored results for a user
  GET  /retrieve           — similarity search across stored summaries
  GET  /health             — liveness probe

Design principle:
  Routes are thin. All business logic lives in pipeline/orchestrator.py.
  This makes it trivial to swap the HTTP framework (e.g., move to gRPC).
"""

import json
import os
import tempfile
from uuid import uuid4, UUID
from fastapi import APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import Optional, List, Dict, Any

from pipeline.orchestrator import run_pipeline, run_pipeline_batch
import storage.store as store
import storage.supabase_client as supabase_client
import retrieval.vector_store as vector_store
from security.rbac import check_access, get_role, filter_response_for_role
from security.auth import get_user_id_from_request
from extraction.openclaw_gateway import OpenClawGateway


router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Request / response schemas
# ──────────────────────────────────────────────────────────────────────────────

class ProcessDocumentRequest(BaseModel):
    user_id: str
    document_type: str   # "upi" | "rent" | "bill"
    content: str         # raw text (simulated OCR output)

    @field_validator("document_type")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        allowed = {"upi", "rent", "bill"}
        if v not in allowed:
            raise ValueError(f"document_type must be one of {allowed}")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be empty")
        return v


class RetrieveRequest(BaseModel):
    query: str
    top_k: int = 3


class SkillInvokeRequest(BaseModel):
    """Request to invoke an OpenClaw skill."""
    skill: str
    input: Dict[str, Any] = {}


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health_check():
    """Liveness probe — returns OK if the server is running."""
    return {"status": "ok", "engine": "KamaaiProof AI Engine v1.0"}


@router.post("/process-document")
async def process_document(body: ProcessDocumentRequest):
    """
    Main AI pipeline endpoint.

    Accepts raw text (simulated OCR), runs the full pipeline:
      Sanitize → Extract → Validate → Store → Index

    Returns structured transaction data and summary.
    """
    try:
        result = run_pipeline(
            user_id=body.user_id,
            document_type=body.document_type,
            raw_content=body.content,
        )
        return JSONResponse(content=result, status_code=200)
    except Exception as exc:
        # Never expose internal errors to client — log and return safe message
        raise HTTPException(
            status_code=500,
            detail=f"Pipeline processing failed: {str(exc)}",
        )


@router.post("/parse")
async def parse_multipart(
    request: Request,
    files: List[UploadFile] = File(default=[]),
    metadata: str = Form(default="[]"),
    whatsappText: str = Form(default=""),
    sessionId: str = Form(default=""),
):
    """
    Frontend-compatible parse endpoint.

    Accepts multipart/form-data with files[], metadata (JSON string), whatsappText.
    Uploads raw files to Supabase Storage (when configured), runs the AI pipeline,
    persists results to Supabase Postgres, and returns the scoring summary +
    a session_id the frontend can use to re-fetch results later.
    """
    def _is_valid_uuid(value: str) -> bool:
        try:
            UUID(value)
            return True
        except Exception:
            return False

    session_id = sessionId if sessionId and _is_valid_uuid(sessionId) else str(uuid4())
    user_id = get_user_id_from_request(request)
    documents = []
    skipped_files: list[str] = []
    temp_paths: list[str] = []

    # Parse metadata JSON
    try:
        meta_list = json.loads(metadata) if metadata else []
    except json.JSONDecodeError:
        meta_list = []

    # Supabase Storage client (None if not configured)
    sb = supabase_client.get_client()
    supabase_url = os.getenv("SUPABASE_URL", "").strip()

    # Handle uploaded files
    for i, upload in enumerate(files):
        raw_bytes = await upload.read()
        filename = upload.filename or f"file_{i}"
        ext = os.path.splitext(filename)[1].lower()
        content_type = (upload.content_type or "").lower()

        # ── Upload to Supabase Storage ────────────────────────────────────────
        document_url: str | None = None
        if sb and raw_bytes:
            storage_path = f"{session_id}/{filename}"
            try:
                sb.storage.from_("document-uploads").upload(
                    storage_path,
                    raw_bytes,
                    {"content-type": upload.content_type or "application/octet-stream"},
                )
                document_url = storage_path  # store path; generate signed URL on demand
            except Exception as exc:
                print(f"[Storage] Upload failed for {upload.filename}: {exc}")

        # ── Decode text content ───────────────────────────────────────────────
        is_text = content_type.startswith("text/") or ext in {".txt", ".csv", ".md", ".log", ".json"}
        text_content = ""
        is_binary = False

        if is_text:
            try:
                text_content = raw_bytes.decode("utf-8")
            except Exception:
                try:
                    text_content = raw_bytes.decode("latin-1")
                except Exception:
                    text_content = ""
        else:
            if raw_bytes:
                is_binary = True
                suffix = ext if ext else ".bin"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(raw_bytes)
                    temp_paths.append(tmp.name)
                    text_content = tmp.name

        # Map frontend tag label → internal document_type
        doc_type = "bill"  # default
        if i < len(meta_list) and isinstance(meta_list[i], dict):
            tag = meta_list[i].get("tag", "").lower()
            if any(k in tag for k in ("upi", "gpay", "phonepe", "bhim", "paytm")):
                doc_type = "upi"
            elif "rent" in tag:
                doc_type = "rent"
            elif any(k in tag for k in ("utility", "bill", "electricity", "water", "gas")):
                doc_type = "bill"
            elif any(k in tag for k in ("receipt", "invoice", "payment")):
                doc_type = "bill"

        if text_content.strip():
            documents.append({
                "document_type": doc_type,
                "content": text_content,
                "document_url": document_url,
                "is_binary": is_binary,
                "filename": filename,
                "mime_type": content_type,
            })
        else:
            skipped_files.append(filename)

    # Handle WhatsApp text (treat as UPI by default, no file upload)
    if whatsappText and whatsappText.strip():
        documents.append({"document_type": "upi", "content": whatsappText, "document_url": None})

    if not documents:
        flags = ["No processable content found in submission."]
        if skipped_files:
            flags.append(f"Skipped empty/unsupported files: {', '.join(skipped_files)}")
        return JSONResponse(content={
            "session_id": session_id,
            "consistencyScore": 0,
            "totalIncome": 0,
            "months": [],
            "transactions": [],
            "flags": flags,
        }, status_code=200)

    try:
        result = run_pipeline_batch(user_id=user_id, documents=documents, session_id=session_id)
    finally:
        for path in temp_paths:
            try:
                os.remove(path)
            except OSError:
                pass

    summary = result.get("summary", {})
    flags = list(summary.get("flags", []))
    if skipped_files:
        flags.append(f"Skipped empty/unsupported files: {', '.join(skipped_files)}")

    return JSONResponse(content={
        "session_id":          result.get("session_id", session_id),
        "consistencyScore":    summary.get("consistency_score", 0),
        "totalIncome":         summary.get("total_income", 0),
        "averageMonthlyIncome": summary.get("average_monthly_income", 0),
        "months":              summary.get("months", []),
        "transactions":        result.get("transactions", []),
        "flags":               flags,
    }, status_code=200)


@router.get("/session/{session_id}")
async def get_session(session_id: str, request: Request):
    """
    Re-fetch a previously processed session by its UUID.

    The frontend stores session_id in localStorage after a successful /parse
    call and uses this endpoint to restore the result page on revisit.
    """
    user_id = get_user_id_from_request(request)
    session = store.get_session(session_id, user_id=user_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Session '{session_id}' not found.",
        )
    return JSONResponse(content=session)


@router.get("/results/{user_id}")
async def get_results(user_id: str, request: Request):
    """
    Retrieve stored results for a user.

    Applies RBAC: workers see full transactions, officers see summaries only.

    Query params:
      requesting_user — the user making the request (for RBAC check).
                        In production this comes from the JWT token.
    """
    # RBAC check
    requesting_user = get_user_id_from_request(request)
    if requesting_user != user_id:
        raise HTTPException(status_code=403, detail="Access denied for this user.")

    access = check_access(
        requesting_user_id=requesting_user,
        target_user_id=user_id,
        action="read",
    )
    if not access.allowed:
        raise HTTPException(status_code=403, detail=access.reason)

    results = store.get_results(user_id)
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No results found for user '{user_id}'.",
        )

    role = get_role(requesting_user)

    # Filter each result based on role permissions
    filtered = []
    for record in results:
        if role == "mfi_officer":
            # Officers see only the summary
            filtered.append({
                "summary": record.get("summary", {}),
                "validation_errors": record.get("validation_errors", []),
            })
        else:
            filtered.append(record)

    return JSONResponse(content={"user_id": user_id, "results": filtered})


@router.post("/retrieve")
async def retrieve_similar(body: RetrieveRequest):
    """
    Similarity search across indexed document summaries.

    Useful for MFI officers to find similar income patterns.
    """
    results = vector_store.retrieve_similar(body.query, top_k=body.top_k)
    return JSONResponse(content={
        "query": body.query,
        "results": results,
        "indexed_count": vector_store.store_size(),
    })


# ──────────────────────────────────────────────────────────────────────────────
# OpenClaw Gateway Routes
# ──────────────────────────────────────────────────────────────────────────────

_gateway = OpenClawGateway()


@router.get("/openclaw/skills")
async def list_openclaw_skills():
    """
    List all available OpenClaw skills.

    Returns:
      { "skills": ["KamaaiProof", ...] }
    """
    try:
        skills = _gateway.list_skills()
        return JSONResponse(content={"skills": skills})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/openclaw/skills/{skill_name}")
async def get_skill_info(skill_name: str):
    """
    Get metadata for a specific OpenClaw skill.

    Returns skill manifest (name, version, description, capabilities, entry_point, etc.)
    """
    try:
        skill_info = _gateway.get_skill_info(skill_name)
        return JSONResponse(content={"skill": skill_name, "manifest": skill_info})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/openclaw/invoke")
async def invoke_openclaw_skill(body: SkillInvokeRequest):
    """
    Invoke an OpenClaw skill with input data.

    Body:
      {
        "skill": "KamaaiProof",
        "input": { "image_path": "..." } or other skill-specific input
      }

    Returns:
      {
        "status": "success" | "error",
        "skill": "KamaaiProof",
        "result": { ... },
        "error": "..." (if status == "error")
      }
    """
    try:
        result = _gateway.invoke_skill(body.skill, body.input)
        if result.get("status") == "error":
            raise HTTPException(status_code=400, detail=result.get("error"))
        return JSONResponse(content=result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
