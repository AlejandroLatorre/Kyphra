"""Tests for kyphra.hook.redactor.

Cover: each PII type produces the expected token, no bleed-through of raw values,
idempotency (redacting twice is a no-op).
"""
from __future__ import annotations

from kyphra.hook.redactor import redact


def test_redact_email() -> None:
    r = redact("contact dev@example.com today")
    assert r.text == "contact <PII_email> today"
    assert "example.com" not in r.text


def test_redact_dni() -> None:
    r = redact("id 12345678Z for review")
    assert r.text == "id <PII_dni> for review"


def test_redact_nie() -> None:
    r = redact("nie Y2345678X")
    assert r.text == "nie <PII_nie>"


def test_redact_spanish_iban() -> None:
    r = redact("iban ES2100817360875920001234 ok")
    assert "21008173" not in r.text
    assert r.text == "iban <PII_iban> ok"


def test_redact_secret_anthropic_token() -> None:
    tok = "sk-ant-api03-" + "q" * 24
    r = redact(f"key={tok}")
    assert tok not in r.text
    assert r.text.startswith("key=<SECRET_anthropic_api_key_sk-ant-api")


def test_idempotency_double_redact() -> None:
    raw = (
        "mail a@b.co dni 87654321A secret sk-ant-api03-"
        + "r" * 24
        + " iban ES9121000418450200051332"
    )
    once = redact(raw)
    twice = redact(once.text)
    assert once.text == twice.text
