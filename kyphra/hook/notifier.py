"""Admin notifications for AVISO (daily digest) and ALERTA (immediate).

Transports: optional HTTP POST to KYPHRA_NOTIFY_WEBHOOK (Slack incoming webhook,
generic HTTPS endpoint). Never sends prompt text — only classification metadata.
Supabase realtime is planned for the dashboard phase.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from urllib.parse import urlparse
from urllib.request import Request

from kyphra.hook.logger import LogEvent
from kyphra.taxonomy.categories import Level


def notify(event: LogEvent) -> None:
    """Fire-and-forget webhook for AVISO/ALERTA. No-op if unset or ALLOW."""
    if event.level == Level.ALLOW:
        return
    url = os.environ.get("KYPHRA_NOTIFY_WEBHOOK", "").strip()
    if not url:
        return
    parts = urlparse(url)
    if parts.scheme not in ("http", "https"):
        return
    payload: dict[str, object | None] = {
        "level": event.level.value,
        "max_category": event.max_category.value,
        "max_score": event.max_score,
        "hook_event_name": event.hook_event_name,
        "session_id": event.session_id,
        "cwd": event.cwd,
        "transcript_path": event.transcript_path,
        "classifier_outcome": event.classifier_outcome,
        "secret_short_circuit": event.secret_short_circuit,
        "org_sector": event.org_sector,
        "org_role": event.org_role,
        "org_user_id": event.org_user_id,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, method="POST", headers={"Content-Type": "application/json"})  # noqa: S310
    try:
        urllib.request.urlopen(req, timeout=3)  # noqa: S310 — only http/https URLs accepted above
    except (TimeoutError, OSError, urllib.error.URLError):
        return
