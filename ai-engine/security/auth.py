from fastapi import Request

import storage.supabase_client as supabase_client

_ANONYMOUS_USER_ID = "anonymous"


def _extract_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization") or request.headers.get("Authorization")
    if not auth_header:
        return None
    if not auth_header.lower().startswith("bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def get_user_id_from_request(request: Request) -> str:
    """
    Extract and verify the Supabase JWT bearer token from the request.

    Graceful degradation:
    - If Supabase is not configured, return anonymous user ID so the app
      works locally without credentials.
    - If a token is present but Supabase IS configured, validate it fully.
    - If no token is present and Supabase is not configured, use anonymous.
    """
    token = _extract_bearer_token(request)
    client = supabase_client.get_client()

    # No Supabase configured — allow anonymous access for local dev
    if client is None:
        if token:
            print("[Auth] Supabase not configured, ignoring bearer token — using anonymous user.")
        return _ANONYMOUS_USER_ID

    # Supabase IS configured but no token provided
    if not token:
        print("[Auth] Missing Authorization bearer token — using anonymous user.")
        return _ANONYMOUS_USER_ID

    # Validate the token against Supabase
    try:
        response = client.auth.get_user(token)
    except Exception as exc:
        print(f"[Auth] Token validation failed: {exc} — using anonymous user.")
        return _ANONYMOUS_USER_ID

    user = getattr(response, "user", None) or (response.get("user") if isinstance(response, dict) else None)
    user_id = getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)
    if not user_id:
        print("[Auth] Token validated but no user ID found — using anonymous user.")
        return _ANONYMOUS_USER_ID

    return user_id
