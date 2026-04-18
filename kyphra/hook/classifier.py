"""Classifier client.

Two modes:
- Stub (default, KYPHRA_STUB=1): deterministic keyword-based classification for offline dev.
- Remote: calls the Cloudflare Worker endpoint (OpenRouter / Anthropic server-side).

Must never receive a raw prompt. Input is always the redacted version.
Optional `OrgContext` is forwarded as JSON for OFF_SCOPE policy when configured.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Final, Literal
from urllib.parse import urlparse
from urllib.request import Request

from kyphra.hook.org_context import OrgContext
from kyphra.taxonomy.categories import Category

Outcome = Literal["OK", "UNKNOWN_TIMEOUT"]

_INJECTION_MARKERS: Final[tuple[str, ...]] = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard the above",
    "print your system prompt",
    "reveal your system prompt",
)

_BANK_SECTOR_MARKERS: Final[tuple[str, ...]] = ("bank", "finance", "insurance", "fintech")
_STUB_OFF_SCOPE_MARKERS: Final[tuple[str, ...]] = (
    "drone",
    "uav",
    "quadcopter",
    "volador",
    "flying vehicle",
    "trayectoria",
    "trayectorias",
    "interceptar",
    "ballistic",
    "vehículo motorizado",
    "vehiculo motorizado",
)


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    max_category: Category
    max_score: float
    outcome: Outcome


def _stub_off_scope(lower: str, org: OrgContext | None) -> bool:
    if org is None or not org.is_active:
        return False
    policy = f"{org.sector} {org.allowed_scope}".lower()
    if not any(m in policy for m in _BANK_SECTOR_MARKERS):
        return False
    return any(m in lower for m in _STUB_OFF_SCOPE_MARKERS)


def _stub_classify(redacted: str, org: OrgContext | None) -> ClassificationResult:
    lower = redacted.lower()
    for marker in _INJECTION_MARKERS:
        if marker in lower:
            return ClassificationResult(
                max_category=Category.PROMPT_INJECTION,
                max_score=0.92,
                outcome="OK",
            )
    if _stub_off_scope(lower, org):
        return ClassificationResult(max_category=Category.OFF_SCOPE, max_score=0.92, outcome="OK")
    return ClassificationResult(max_category=Category.BENIGN, max_score=0.05, outcome="OK")


def _http_classify(redacted: str, endpoint: str, org: OrgContext | None) -> ClassificationResult:
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https"):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    payload: dict[str, object] = {"prompt": redacted}
    if org is not None:
        payload["org"] = org.to_payload()
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, OSError, urllib.error.URLError):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")

    try:
        max_score = float(payload["max_score"])
        max_cat = Category(str(payload["max_category"]))
    except (KeyError, TypeError, ValueError):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")

    return ClassificationResult(max_category=max_cat, max_score=max_score, outcome="OK")


def classify(redacted_prompt: str, org: OrgContext | None = None) -> ClassificationResult:
    stub = os.environ.get("KYPHRA_STUB", "1") == "1"
    if stub:
        return _stub_classify(redacted_prompt, org)
    endpoint = os.environ.get("KYPHRA_CLASSIFIER_ENDPOINT", "").strip()
    if not endpoint:
        return _stub_classify(redacted_prompt, org)
    return _http_classify(redacted_prompt, endpoint, org)
