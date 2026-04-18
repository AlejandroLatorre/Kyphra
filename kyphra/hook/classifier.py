"""Classifier client.

Two modes:
- Stub (default, KYPHRA_STUB=1): deterministic keyword-based classification for offline dev.
- Remote: calls the Cloudflare Worker endpoint (OpenRouter / Anthropic server-side).

Must never receive a raw prompt. Input is always the redacted version.
Optional `OrgContext` is forwarded as JSON for OFF_SCOPE policy when configured.
Optional `file_hints` lists metadata from `file_inspect.collect_file_hints` (no file body).
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


def _stub_file_drive(file_hints: list[dict[str, object]] | None) -> ClassificationResult | None:
    if not file_hints:
        return None
    for h in file_hints:
        hits = h.get("pii_header_hits")
        if not isinstance(hits, list):
            continue
        est_raw = h.get("extrapolated_row_estimate", 0)
        if isinstance(est_raw, bool):
            est = 0
        elif isinstance(est_raw, int):
            est = est_raw
        elif isinstance(est_raw, float):
            est = int(est_raw)
        elif isinstance(est_raw, str):
            try:
                est = int(est_raw)
            except ValueError:
                est = 0
        else:
            est = 0
        dens_raw = h.get("pii_column_density", 0.0)
        if isinstance(dens_raw, bool):
            density = 0.0
        elif isinstance(dens_raw, (int, float)):
            density = float(dens_raw)
        elif isinstance(dens_raw, str):
            try:
                density = float(dens_raw)
            except ValueError:
                density = 0.0
        else:
            density = 0.0
        if len(hits) >= 3 and est >= 8_000:
            return ClassificationResult(max_category=Category.CUSTOMER_DATA, max_score=0.9, outcome="OK")
        if len(hits) >= 2 and est >= 500 and density >= 0.35:
            return ClassificationResult(max_category=Category.CUSTOMER_DATA, max_score=0.72, outcome="OK")
    return None


def _stub_off_scope(lower: str, org: OrgContext | None) -> bool:
    if org is None or not org.is_active:
        return False
    policy = f"{org.sector} {org.allowed_scope}".lower()
    if not any(m in policy for m in _BANK_SECTOR_MARKERS):
        return False
    return any(m in lower for m in _STUB_OFF_SCOPE_MARKERS)


def _stub_classify(
    redacted: str,
    org: OrgContext | None,
    file_hints: list[dict[str, object]] | None,
) -> ClassificationResult:
    lower = redacted.lower()
    for marker in _INJECTION_MARKERS:
        if marker in lower:
            return ClassificationResult(
                max_category=Category.PROMPT_INJECTION,
                max_score=0.92,
                outcome="OK",
            )
    file_hit = _stub_file_drive(file_hints)
    if file_hit is not None:
        return file_hit
    if _stub_off_scope(lower, org):
        return ClassificationResult(max_category=Category.OFF_SCOPE, max_score=0.92, outcome="OK")
    return ClassificationResult(max_category=Category.BENIGN, max_score=0.05, outcome="OK")


def _http_classify(
    redacted: str,
    endpoint: str,
    org: OrgContext | None,
    file_hints: list[dict[str, object]] | None,
) -> ClassificationResult:
    endpoint_parts = urlparse(endpoint)
    if endpoint_parts.scheme not in ("http", "https"):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    payload: dict[str, object] = {"prompt": redacted}
    if org is not None:
        payload["org"] = org.to_payload()
    if file_hints:
        payload["file_hints"] = file_hints
    body = json.dumps(payload).encode("utf-8")
    req = Request(
        endpoint,
        data=body,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=2) as resp:
            parsed = json.loads(resp.read().decode("utf-8"))
    except (TimeoutError, OSError, urllib.error.URLError):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")

    if not isinstance(parsed, dict):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    data: dict[str, object] = parsed
    ms_raw = data.get("max_score")
    mc_raw = data.get("max_category")
    if isinstance(ms_raw, bool) or ms_raw is None:
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    if isinstance(ms_raw, (int, float)):
        max_score = float(ms_raw)
    elif isinstance(ms_raw, str):
        try:
            max_score = float(ms_raw)
        except ValueError:
            return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    else:
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    if not isinstance(mc_raw, str):
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")
    try:
        max_cat = Category(mc_raw)
    except ValueError:
        return ClassificationResult(max_category=Category.BENIGN, max_score=0.0, outcome="UNKNOWN_TIMEOUT")

    return ClassificationResult(max_category=max_cat, max_score=max_score, outcome="OK")


def classify(
    redacted_prompt: str,
    org: OrgContext | None = None,
    file_hints: list[dict[str, object]] | None = None,
) -> ClassificationResult:
    stub = os.environ.get("KYPHRA_STUB", "1") == "1"
    if stub:
        return _stub_classify(redacted_prompt, org, file_hints)
    endpoint = os.environ.get("KYPHRA_CLASSIFIER_ENDPOINT", "").strip()
    if not endpoint:
        return _stub_classify(redacted_prompt, org, file_hints)
    return _http_classify(redacted_prompt, endpoint, org, file_hints)
