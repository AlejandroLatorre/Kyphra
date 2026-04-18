"""PII redaction applied BEFORE any external call.

Replaces identifiable data (emails, DNI, NIE, IBANs) with structural tokens
and known secret shapes with SECRET tokens. The redactor is the only
sanctioned path from raw prompt to classifier client.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from kyphra.hook.secrets import SecretMatch, find_secrets

_EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"[a-zA-Z0-9._%+-]{1,64}@[a-zA-Z0-9.-]{1,253}\.[a-zA-Z]{2,63}"
    r"(?![A-Za-z0-9._%+-])",
)
_DNI_RE = re.compile(r"\b[0-9]{8}[A-Za-z]\b")
_NIE_RE = re.compile(r"\b[XYZxyz][0-9]{7}[A-Za-z]\b")
_IBAN_ES_RE = re.compile(r"\bES[0-9]{22}\b")
_IBAN_INTL_RE = re.compile(r"\b[A-Z]{2}[0-9]{2}[A-Z0-9]{13,28}\b")


@dataclass(frozen=True, slots=True)
class RedactedPrompt:
    text: str


def _secret_placeholder(match: SecretMatch, body: str) -> str:
    raw = body[match.start : match.end]
    preview = raw[:10]
    return f"<SECRET_{match.kind.value}_{preview}***>"


def _apply_secret_redactions(body: str, matches: list[SecretMatch]) -> str:
    out = body
    for m in sorted(matches, key=lambda x: x.start, reverse=True):
        token = _secret_placeholder(m, body)
        out = out[: m.start] + token + out[m.end :]
    return out


def _apply_pii_redactions(body: str) -> str:
    body = _EMAIL_RE.sub("<PII_email>", body)
    body = _DNI_RE.sub("<PII_dni>", body)
    body = _NIE_RE.sub("<PII_nie>", body)
    body = _IBAN_ES_RE.sub("<PII_iban>", body)
    return _IBAN_INTL_RE.sub("<PII_iban>", body)


def redact(text: str) -> RedactedPrompt:
    secret_matches = find_secrets(text)
    with_secrets = _apply_secret_redactions(text, secret_matches)
    final = _apply_pii_redactions(with_secrets)
    return RedactedPrompt(text=final)
