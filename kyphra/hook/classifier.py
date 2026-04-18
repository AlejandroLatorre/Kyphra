"""Classifier client.

Two modes:
- Stub (default, KYPHRA_STUB=1): deterministic keyword-based classification for offline dev.
- Haiku: calls the Cloudflare Worker endpoint which fronts Anthropic Haiku 4.5.

Must never receive a raw prompt. Input is always the redacted version.
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

from kyphra.taxonomy.categories import Category

Outcome = Literal["OK", "UNKNOWN_TIMEOUT"]

_INJECTION_MARKERS: Final[tuple[str, ...]] = (
    "ignore previous instructions",
    "ignore all previous",
    "disregard the above",
    "print your system prompt",
    "reveal your system prompt",
)


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    max_category: Category
    max_score: float
    outcome: Outcome


def _stub_classify(redacted: str) -> ClassificationResult:
    lower = redacted.lower()
    for marker in _INJECTION_MARKERS:
        if marker in lower:
            return ClassificationResult(
                max_category=Category.PROMPT_INJECTION,
                max_score=0.92,
                outcome="OK",
            )
    return ClassificationResult(max_category=Category.BENIGN, max_score=0.05, outcome="OK")


def _http_classify(redacted: str, endpoint: str) -> ClassificationResult:
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https"):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    body = json.dumps({"prompt": redacted}).encode("utf-8")
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


def classify(redacted_prompt: str) -> ClassificationResult:
    stub = os.environ.get("KYPHRA_STUB", "1") == "1"
    if stub:
        return _stub_classify(redacted_prompt)
    endpoint = os.environ.get("KYPHRA_CLASSIFIER_ENDPOINT", "").strip()
    if not endpoint:
        return _stub_classify(redacted_prompt)
    return _http_classify(redacted_prompt, endpoint)
