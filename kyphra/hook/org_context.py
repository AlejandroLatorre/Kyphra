"""Organization and user policy context for classification.

Merged from environment variables and optional stdin JSON (`kyphra_org`).
When absent, the classifier applies only the data-leakage taxonomy.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OrgContext:
    """Sector, role, allowed scope, and user id for policy-aware classification."""

    sector: str
    role: str
    allowed_scope: str
    user_id: str

    @property
    def is_active(self) -> bool:
        """True when enough context is present to evaluate off-scope use."""
        return bool(self.sector.strip() or self.allowed_scope.strip())

    def to_payload(self) -> dict[str, str]:
        return {
            "sector": self.sector.strip(),
            "role": self.role.strip(),
            "allowed_scope": self.allowed_scope.strip(),
            "user_id": self.user_id.strip(),
        }


def _strip(v: Any) -> str:
    if isinstance(v, str):
        return v.strip()
    return ""


def merge_org_from_env_and_stdin(stdin_data: dict[str, Any]) -> OrgContext | None:
    """Build OrgContext from KYPHRA_ORG_* env vars, overridden by stdin `kyphra_org`."""
    sector = os.environ.get("KYPHRA_ORG_SECTOR", "").strip()
    role = os.environ.get("KYPHRA_ORG_ROLE", "").strip()
    allowed_scope = os.environ.get("KYPHRA_ORG_SCOPE", "").strip()
    user_id = os.environ.get("KYPHRA_ORG_USER_ID", "").strip()

    raw = stdin_data.get("kyphra_org")
    if isinstance(raw, dict):
        if raw.get("sector") is not None:
            sector = _strip(raw.get("sector"))
        if raw.get("role") is not None:
            role = _strip(raw.get("role"))
        if raw.get("allowed_scope") is not None:
            allowed_scope = _strip(raw.get("allowed_scope"))
        if raw.get("user_id") is not None:
            user_id = _strip(raw.get("user_id"))

    ctx = OrgContext(sector=sector, role=role, allowed_scope=allowed_scope, user_id=user_id)
    if not ctx.is_active:
        return None
    return ctx
