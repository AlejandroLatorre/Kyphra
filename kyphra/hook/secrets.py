"""Local regex short-circuit for known secret patterns.

Runs BEFORE any external call. Matches here skip the Haiku round-trip
and go straight to ALERTA. Patterns are inspired by TruffleHog / Gitleaks.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum


class SecretKind(StrEnum):
    ANTHROPIC_API_KEY = "anthropic_api_key"
    OPENAI_PROJECT_KEY = "openai_project_key"
    AWS_ACCESS_KEY_ID = "aws_access_key_id"
    GITHUB_CLASSIC_TOKEN = "github_classic_token"
    GITHUB_FINE_GRAINED_TOKEN = "github_fine_grained_token"
    SLACK_TOKEN = "slack_token"
    JWT = "jwt"
    PRIVATE_KEY_PEM = "private_key_pem"
    POSTGRES_URL = "postgres_url"
    MYSQL_URL = "mysql_url"
    MONGODB_URL = "mongodb_url"


@dataclass(frozen=True, slots=True)
class SecretMatch:
    start: int
    end: int
    kind: SecretKind


_RULES: list[tuple[SecretKind, re.Pattern[str]]] = [
    (
        SecretKind.ANTHROPIC_API_KEY,
        re.compile(r"sk-ant-api\d{2}-[A-Za-z0-9_-]{20,}"),
    ),
    (
        SecretKind.OPENAI_PROJECT_KEY,
        re.compile(r"sk-proj-[A-Za-z0-9_-]{40,}"),
    ),
    (
        SecretKind.AWS_ACCESS_KEY_ID,
        re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])"),
    ),
    (
        SecretKind.GITHUB_CLASSIC_TOKEN,
        re.compile(r"ghp_[0-9a-zA-Z]{36,}"),
    ),
    (
        SecretKind.GITHUB_FINE_GRAINED_TOKEN,
        re.compile(r"github_pat_[0-9a-zA-Z_]{80,}"),
    ),
    (
        SecretKind.SLACK_TOKEN,
        re.compile(r"xox[baprs]-[0-9a-zA-Z-]{16,}"),
    ),
    (
        SecretKind.JWT,
        re.compile(
            r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}",
        ),
    ),
    (
        SecretKind.PRIVATE_KEY_PEM,
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----[\s\S]{0,100000}?"
            r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.MULTILINE,
        ),
    ),
    (
        SecretKind.POSTGRES_URL,
        re.compile(
            r"(?i)\bpostgres(?:ql)?://[^\s:@]+:[^\s@/]+@[^\s]+",
        ),
    ),
    (
        SecretKind.MYSQL_URL,
        re.compile(
            r"(?i)\bmysql://[^\s:@]+:[^\s@/]+@[^\s]+",
        ),
    ),
    (
        SecretKind.MONGODB_URL,
        re.compile(
            r"(?i)\bmongodb(?:\+srv)?://[^\s:@]+:[^\s@/]+@[^\s]+",
        ),
    ),
]


def _merge_non_overlapping(matches: list[SecretMatch]) -> list[SecretMatch]:
    if not matches:
        return []
    by_length_then_start = sorted(
        matches,
        key=lambda m: (-(m.end - m.start), m.start),
    )
    chosen: list[SecretMatch] = []
    for m in by_length_then_start:
        if any(not (o.end <= m.start or o.start >= m.end) for o in chosen):
            continue
        chosen.append(m)
    return sorted(chosen, key=lambda m: m.start)


def find_secrets(text: str) -> list[SecretMatch]:
    raw: list[SecretMatch] = []
    for kind, pattern in _RULES:
        for m in pattern.finditer(text):
            raw.append(SecretMatch(start=m.start(), end=m.end(), kind=kind))
    return _merge_non_overlapping(raw)
