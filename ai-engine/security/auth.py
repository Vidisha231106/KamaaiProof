from fastapi import HTTPException, Request

import storage.supabase_client as supabase_client


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def get_user_id_from_request(request: Request) -> str:
    token = _extract_bearer_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Missing Authorization bearer token.")

    client = supabase_client.get_client()
    if client is None:
        raise HTTPException(status_code=500, detail="Supabase is not configured.")

    try:
        response = client.auth.get_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

    user = getattr(response, "user", None) or (response.get("user") if isinstance(response, dict) else None)
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

    return user_id
