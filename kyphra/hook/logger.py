"""Local structured logging of classification events.

- ALLOW: aggregated counters only, 30-day retention.
- AVISO: redacted content in JSONL, 60-day retention.
- ALERTA: redacted content in an AES-GCM encrypted archive, 365-day retention.

Raw prompts are NEVER written to disk.
"""
from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from kyphra.taxonomy.categories import Category, Level


def _pbkdf2_iterations() -> int:
    raw = os.environ.get("KYPHRA_PBKDF2_ITERATIONS", "").strip()
    if raw.isdigit():
        return max(1_000, int(raw))
    return 600_000


def _kyphra_home() -> Path:
    home = os.environ.get("KYPHRA_HOME", "").strip()
    if home:
        return Path(home).expanduser()
    return Path.home() / ".kyphra"


def _encrypt_alert_line(password: str, plaintext: bytes) -> str:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=_pbkdf2_iterations(),
    )
    key = kdf.derive(password.encode("utf-8"))
    nonce = os.urandom(12)
    aes = AESGCM(key)
    ciphertext = aes.encrypt(nonce, plaintext, None)
    blob = salt + nonce + ciphertext
    return base64.b64encode(blob).decode("ascii")


@dataclass(frozen=True, slots=True)
class LogEvent:
    hook_event_name: str
    session_id: str | None
    cwd: str | None
    transcript_path: str | None
    level: Level
    max_category: Category
    max_score: float
    redacted_prompt: str
    classifier_outcome: str
    secret_short_circuit: bool
    org_sector: str | None = None
    org_role: str | None = None
    org_user_id: str | None = None
    org_allowed_scope: str | None = None
    file_inspection_summary: str | None = None


def _record_dict(event: LogEvent) -> dict[str, Any]:
    scope = event.org_allowed_scope
    if isinstance(scope, str) and len(scope) > 400:
        scope = scope[:400] + "…"
    fsum = event.file_inspection_summary
    if isinstance(fsum, str) and len(fsum) > 500:
        fsum = fsum[:500] + "…"
    return {
        "ts": datetime.now(UTC).isoformat(),
        "hook_event_name": event.hook_event_name,
        "session_id": event.session_id,
        "cwd": event.cwd,
        "transcript_path": event.transcript_path,
        "level": event.level.value,
        "max_category": event.max_category.value,
        "max_score": event.max_score,
        "redacted_prompt": event.redacted_prompt,
        "classifier_outcome": event.classifier_outcome,
        "secret_short_circuit": event.secret_short_circuit,
        "org_sector": event.org_sector,
        "org_role": event.org_role,
        "org_user_id": event.org_user_id,
        "org_allowed_scope": scope,
        "file_inspection_summary": fsum,
    }


def log_event(event: LogEvent) -> None:
    base = _kyphra_home()
    logs = base / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    path = logs / "events.jsonl"
    line = json.dumps(_record_dict(event), ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)

    if event.level != Level.ALERTA:
        return

    password = os.environ.get("KYPHRA_ADMIN_PASSWORD", "").strip()
    if not password:
        return

    alert_path = logs / "alerta.enc.jsonl"
    inner = json.dumps(_record_dict(event), ensure_ascii=False).encode("utf-8")
    enc_line = _encrypt_alert_line(password, inner) + "\n"
    with alert_path.open("a", encoding="utf-8") as f:
        f.write(enc_line)
