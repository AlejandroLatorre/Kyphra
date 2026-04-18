"""Integration tests for kyphra.hook.main."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


def _run_hook(stdin_obj: dict[str, object], monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> subprocess.CompletedProcess[str]:
    monkeypatch.setenv("KYPHRA_HOME", str(tmp_path))
    monkeypatch.setenv("KYPHRA_STUB", "1")
    monkeypatch.setenv("KYPHRA_PBKDF2_ITERATIONS", "1000")
    return subprocess.run(
        [sys.executable, "-m", "kyphra.hook.main"],
        input=json.dumps(stdin_obj),
        text=True,
        capture_output=True,
        check=False,
    )


def test_hook_always_exit_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    proc = _run_hook({"prompt": "hello world"}, monkeypatch, tmp_path)
    assert proc.returncode == 0


def test_log_never_contains_raw_secret(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    secret = "sk-ant-api03-" + "x" * 24
    proc = _run_hook({"prompt": f"use {secret} here"}, monkeypatch, tmp_path)
    assert proc.returncode == 0
    logf = tmp_path / "logs" / "events.jsonl"
    text = logf.read_text(encoding="utf-8")
    assert secret not in text
    assert "<SECRET_" in text


def test_hook_off_scope_banking_stub_alerta(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KYPHRA_HOME", str(tmp_path))
    monkeypatch.setenv("KYPHRA_STUB", "1")
    monkeypatch.setenv("KYPHRA_ORG_SECTOR", "retail_banking")
    monkeypatch.setenv("KYPHRA_ORG_ROLE", "payments_api_engineer")
    monkeypatch.setenv("KYPHRA_ORG_USER_ID", "jdoe")
    monkeypatch.setenv("KYPHRA_PBKDF2_ITERATIONS", "1000")
    proc = subprocess.run(
        [sys.executable, "-m", "kyphra.hook.main"],
        input=json.dumps(
            {
                "prompt": "instala un entorno python para trayectorias de drones motorizados",
            },
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "ALERTA" in proc.stderr
    assert "OFF_SCOPE" in proc.stderr
    logf = tmp_path / "logs" / "events.jsonl"
    text = logf.read_text(encoding="utf-8")
    assert "OFF_SCOPE" in text
    assert "retail_banking" in text
    assert "jdoe" in text


def test_hook_invalid_json_exit_zero(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KYPHRA_HOME", str(tmp_path))
    proc = subprocess.run(
        [sys.executable, "-m", "kyphra.hook.main"],
        input="not-json{",
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0
