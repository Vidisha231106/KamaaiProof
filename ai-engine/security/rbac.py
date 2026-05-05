"""
security/rbac.py
================
Role-Based Access Control (RBAC) layer.

Roles:
  worker      — full access to their own data only
  mfi_officer — read-only access to summaries (no raw transactions)
  admin       — full access to all users (internal only)

Architecture note:
  In production, replace the `_USER_ROLES` dict with a token-validated
  JWT claim or database lookup. The `check_access()` interface stays the same.
"""

from typing import Literal
from pydantic import BaseModel


RoleType = Literal["worker", "mfi_officer", "admin"]


# ──────────────────────────────────────────────────────────────────────────────
# Mock user → role mapping
# Replace with DB lookup / JWT claim extraction in production
# ──────────────────────────────────────────────────────────────────────────────

_USER_ROLES: dict[str, RoleType] = {
    # Format: user_id → role
    "worker_001": "worker",
    "worker_002": "worker",
    "officer_001": "mfi_officer",
    "admin_001": "admin",
}


class AccessDecision(BaseModel):
    allowed: bool
    role: str
    visible_fields: list[str]  # which fields this role may see
    reason: str


_ROLE_PERMISSIONS: dict[str, dict] = {
    "worker": {
        "own_data": True,
        "others_data": False,
        "visible_fields": [
            "id", "source", "amount", "date", "transaction_type",
            "description", "confidence", "verified",
        ],
    },
    "mfi_officer": {
        "own_data": False,
        "others_data": True,
        "visible_fields": [
            # Officers see only summary-level fields, not raw transactions
            "summary", "consistency_score", "total_income", "months", "flags",
        ],
    },
    "admin": {
        "own_data": True,
        "others_data": True,
        "visible_fields": ["*"],  # full access
    },
}


def get_role(user_id: str) -> RoleType:
    """Return role for a user_id, defaulting to 'worker' if unknown."""
    return _USER_ROLES.get(user_id, "worker")


def check_access(
    requesting_user_id: str,
    target_user_id: str,
    action: Literal["read", "write"],
) -> AccessDecision:
    """
    Determine if requesting_user_id may perform action on target_user_id's data.

    Workers can only access their own data.
    MFI officers can read summaries of any user.
    Admins have full access.
    """
    role = get_role(requesting_user_id)
    perms = _ROLE_PERMISSIONS[role]

    # Workers: own data only
    if role == "worker":
        if requesting_user_id != target_user_id:
            return AccessDecision(
                allowed=False,
                role=role,
                visible_fields=[],
                reason="Workers can only access their own data.",
            )
        if action == "write":
            return AccessDecision(
                allowed=True,
                role=role,
                visible_fields=perms["visible_fields"],
                reason="Write access granted for own data.",
            )
        return AccessDecision(
            allowed=True,
            role=role,
            visible_fields=perms["visible_fields"],
            reason="Read access granted for own data.",
        )

    # MFI Officers: read-only, summary only
    if role == "mfi_officer":
        if action == "write":
            return AccessDecision(
                allowed=False,
                role=role,
                visible_fields=[],
                reason="MFI officers have read-only access.",
            )
        return AccessDecision(
            allowed=True,
            role=role,
            visible_fields=perms["visible_fields"],
            reason="Read access granted (summary-level only).",
        )

    # Admins: full access
    return AccessDecision(
        allowed=True,
        role=role,
        visible_fields=["*"],
        reason="Admin full access granted.",
    )


def filter_response_for_role(data: dict, role: str) -> dict:
    """
    Strip fields from a response dict that the role is not permitted to see.

    Returns a new dict with only permitted fields.
    """
    perms = _ROLE_PERMISSIONS.get(role, _ROLE_PERMISSIONS["worker"])
    visible = perms["visible_fields"]

    if "*" in visible:
        return data  # admin sees everything

    return {k: v for k, v in data.items() if k in visible}


# ──────────────────────────────────────────────────────────────────────────────
# Encryption stub
# Replace with AES-GCM or KMS-backed encryption in production
# ──────────────────────────────────────────────────────────────────────────────

def encrypt_field(value: str) -> str:
    """
    MOCK encryption placeholder.

    In production: use AES-256-GCM with a KMS-managed key.
    This stub exists to mark where encryption should be applied.
    """
    # TODO: Replace with: return aes_gcm_encrypt(value, key=KMS.get_key())
    return f"ENC({value})"


def decrypt_field(encrypted_value: str) -> str:
    """
    MOCK decryption placeholder.

    In production: use AES-256-GCM with a KMS-managed key.
    """
    # TODO: Replace with: return aes_gcm_decrypt(encrypted_value, key=KMS.get_key())
    if encrypted_value.startswith("ENC(") and encrypted_value.endswith(")"):
        return encrypted_value[4:-1]
    return encrypted_value
