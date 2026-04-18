"""Best-effort metadata for files referenced in the prompt (e.g. @data.csv).

Reads only a bounded prefix of each file (header + newline count). Never sends
file contents to the remote classifier — only structured hints (column names,
approximate row count, PII column name hits).
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Final

_ALLOWED_SUFFIX: Final[tuple[str, ...]] = (".csv", ".tsv", ".txt", ".md", ".json", ".xml")
_MAX_FILES: Final[int] = 5
_MAX_SNIFF_BYTES: Final[int] = 64 * 1024
_PII_HEADER_TOKENS: Final[tuple[str, ...]] = (
    "email",
    "mail",
    "telefono",
    "teléfono",
    "phone",
    "mobile",
    "dni",
    "nie",
    "nif",
    "iban",
    "ssn",
    "passport",
    "fecha_nacimiento",
    "date_of_birth",
    "dob",
    "credit_card",
    "card_number",
    "password",
    "nombre",
    "name",
    "address",
    "direccion",
    "customer_id",
)

_REF_PATTERN = re.compile(r"@([^\s\],;>]+)")


def _strip_trailing_junk(s: str) -> str:
    return s.rstrip(').,;"\'')


def _resolve_under_cwd(raw: str, cwd: Path) -> Path | None:
    raw = _strip_trailing_junk(raw.strip().strip("'\""))
    if not raw or raw.startswith("~"):
        return None
    if ".." in Path(raw).parts:
        return None
    try:
        candidate = Path(raw) if os.path.isabs(raw) else (cwd / raw)
        resolved = candidate.resolve()
        cwd_r = cwd.resolve()
        resolved.relative_to(cwd_r)
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def _suffix_ok(p: Path) -> bool:
    return p.suffix.lower() in _ALLOWED_SUFFIX


def _sniff_file(path: Path) -> dict[str, object] | None:
    try:
        file_size = path.stat().st_size
    except OSError:
        return None
    try:
        raw = path.read_bytes()[:_MAX_SNIFF_BYTES]
    except OSError:
        return None
    if b"\x00" in raw[:2048]:
        return None
    text = raw.decode("utf-8", errors="replace")
    lines = text.splitlines()
    header = lines[0][:500] if lines else ""
    lower_header = header.lower()
    hits = [t for t in _PII_HEADER_TOKENS if t in lower_header]
    newline_count = text.count("\n")
    approx_rows = max(0, newline_count) if lines else 0
    if lines and not lines[-1].strip():
        approx_rows = max(0, approx_rows - 1)
    if len(raw) >= _MAX_SNIFF_BYTES and file_size > len(raw):
        extrapolated_rows = int(max(1, newline_count) * (file_size / max(len(raw), 1)))
    else:
        extrapolated_rows = approx_rows
    col_guess = max(1, header.count(",") + 1) if "," in header else max(1, len(header.split()) if header else 1)
    density = min(
        1.0,
        (len(hits) / max(col_guess, 1))
        * (3.0 if extrapolated_rows > 10_000 else 1.5 if extrapolated_rows > 500 else 1.0),
    )
    return {
        "path": path.name,
        "header_sample": header[:240],
        "approx_row_count_in_sniff": approx_rows,
        "extrapolated_row_estimate": extrapolated_rows,
        "file_size_bytes": file_size,
        "pii_header_hits": hits[:20],
        "pii_column_density": round(min(1.0, density), 3),
    }


def collect_file_hints(prompt: str, cwd: str | None) -> list[dict[str, object]]:
    """Return 0..N serializable dicts for paths mentioned as @file under cwd."""
    if not cwd or not cwd.strip():
        return []
    try:
        base = Path(cwd).expanduser()
    except OSError:
        return []
    if not base.is_dir():
        return []

    seen: set[str] = set()
    out: list[dict[str, object]] = []
    for m in _REF_PATTERN.finditer(prompt):
        token = m.group(1)
        resolved = _resolve_under_cwd(token, base)
        if resolved is None or not _suffix_ok(resolved):
            continue
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        meta = _sniff_file(resolved)
        if meta is None:
            continue
        out.append(meta)
        if len(out) >= _MAX_FILES:
            break
    return out
