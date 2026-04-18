"""Tests for kyphra.hook.secrets regex library.

Cover: known positive cases per pattern, false positive resistance on placeholders,
never logs the raw match — only the tokenized preview.
"""
from __future__ import annotations

from kyphra.hook.secrets import SecretKind, find_secrets


def _kinds(text: str) -> set[SecretKind]:
    return {m.kind for m in find_secrets(text)}


def test_anthropic_sk_ant_shape_synthetic() -> None:
    token = "sk-ant-api03-" + "a" * 24
    assert SecretKind.ANTHROPIC_API_KEY in _kinds(f"use key {token} here")


def test_openai_sk_proj_shape_synthetic() -> None:
    token = "sk-proj-" + "b" * 40
    assert SecretKind.OPENAI_PROJECT_KEY in _kinds(f"export KEY={token}")


def test_aws_access_key_id_synthetic() -> None:
    key = "AKIA" + "1" * 16
    assert SecretKind.AWS_ACCESS_KEY_ID in _kinds(f"aws_key={key}")


def test_github_classic_token_synthetic() -> None:
    tok = "ghp_" + "c" * 36
    assert SecretKind.GITHUB_CLASSIC_TOKEN in _kinds(tok)


def test_github_fine_grained_pat_synthetic() -> None:
    tok = "github_pat_" + "d" * 80
    assert SecretKind.GITHUB_FINE_GRAINED_TOKEN in _kinds(tok)


def test_slack_bot_token_synthetic() -> None:
    tok = "xoxb-" + "0" * 16
    assert SecretKind.SLACK_TOKEN in _kinds(tok)


def test_jwt_synthetic_three_segments() -> None:
    jwt = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ."
        "SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
    )
    assert SecretKind.JWT in _kinds(f"bearer {jwt}")


def test_private_key_pem_synthetic() -> None:
    pem = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC\n"
        "-----END PRIVATE KEY-----"
    )
    assert SecretKind.PRIVATE_KEY_PEM in _kinds(pem)


def test_postgres_url_with_password_synthetic() -> None:
    url = "postgres://svc_user:fakepass123@db.internal:5432/app"
    assert SecretKind.POSTGRES_URL in _kinds(url)


def test_mysql_url_with_password_synthetic() -> None:
    url = "mysql://root:fakepass123@127.0.0.1:3306/dev"
    assert SecretKind.MYSQL_URL in _kinds(url)


def test_mongodb_url_with_password_synthetic() -> None:
    url = "mongodb+srv://app:fakepass123@cluster0.example.mongodb.net/db"
    assert SecretKind.MONGODB_URL in _kinds(url)


def test_placeholder_not_matched_as_anthropic() -> None:
    assert find_secrets('api_key = "YOUR_KEY_HERE"') == []


def test_short_sk_proj_not_matched() -> None:
    assert find_secrets("sk-proj-short") == []


def test_find_secrets_returns_sorted_non_overlapping() -> None:
    text = "sk-ant-api03-" + "x" * 24 + " also " + "sk-proj-" + "y" * 40
    matches = find_secrets(text)
    assert matches == sorted(matches, key=lambda m: m.start)
    spans = [(m.start, m.end) for m in matches]
    for i in range(len(spans) - 1):
        assert spans[i][1] <= spans[i + 1][0]


def test_secret_match_positions() -> None:
    prefix = "start "
    token = "sk-ant-api03-" + "z" * 24
    suffix = " end"
    text = prefix + token + suffix
    m = find_secrets(text)
    assert len(m) == 1
    assert text[m[0].start : m[0].end] == token
