"""Tests for kyphra.hook.notifier."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from kyphra.hook.logger import LogEvent
from kyphra.hook.notifier import notify
from kyphra.taxonomy.categories import Category, Level


def _event(level: Level) -> LogEvent:
    return LogEvent(
        hook_event_name="UserPromptSubmit",
        session_id="s1",
        cwd="/tmp",
        transcript_path=None,
        level=level,
        max_category=Category.BENIGN,
        max_score=0.1,
        redacted_prompt="redacted",
        classifier_outcome="OK",
        secret_short_circuit=False,
    )


def test_notify_skips_allow(monkeypatch: pytest.MonkeyPatch) -> None:
    called: list[object] = []

    def boom(*_a: object, **_k: object) -> None:
        called.append(True)

    monkeypatch.setenv("KYPHRA_NOTIFY_WEBHOOK", "https://example.com/hook")
    monkeypatch.setattr("kyphra.hook.notifier.urllib.request.urlopen", boom)
    notify(_event(Level.ALLOW))
    assert called == []


def test_notify_posts_json_for_aviso(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[bytes] = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            captured.append(self.rfile.read(length))
            self.send_response(204)
            self.end_headers()

        def log_message(self, *_args: object) -> None:
            return

    server = HTTPServer(("127.0.0.1", 0), H)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        monkeypatch.setenv("KYPHRA_NOTIFY_WEBHOOK", f"http://127.0.0.1:{port}/n")
        ev = LogEvent(
            hook_event_name="UserPromptSubmit",
            session_id="s1",
            cwd="/w",
            transcript_path=None,
            level=Level.AVISO,
            max_category=Category.PII_PERSONAL,
            max_score=0.55,
            redacted_prompt="x",
            classifier_outcome="OK",
            secret_short_circuit=False,
            org_sector="banking",
            org_role=None,
            org_user_id="u1",
            org_allowed_scope=None,
        )
        notify(ev)
        assert len(captured) == 1
        body = json.loads(captured[0].decode("utf-8"))
        assert body["level"] == "AVISO"
        assert body["max_category"] == "PII_PERSONAL"
        assert body["org_sector"] == "banking"
        assert "redacted_prompt" not in body
    finally:
        server.shutdown()
