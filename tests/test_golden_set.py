"""Schema validation for tests/golden_set.jsonl (curated expected labels)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kyphra.taxonomy.categories import Category, Level

_GOLDEN_PATH = Path(__file__).resolve().parent / "golden_set.jsonl"


def _load_rows() -> list[dict[str, object]]:
    lines = _GOLDEN_PATH.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


_GOLDEN = _load_rows()


@pytest.mark.parametrize("row", _GOLDEN, ids=lambda r: str(r["id"]))
def test_golden_row_schema(row: dict[str, object]) -> None:
    assert isinstance(row.get("id"), str)
    assert isinstance(row.get("prompt"), str)
    assert row["prompt"].strip()
    Category(str(row["expected_category"]))
    Level(str(row["expected_level"]))
    org = row.get("kyphra_org")
    if org is not None:
        assert isinstance(org, dict)


def test_golden_set_minimum_size() -> None:
    assert len(_GOLDEN) >= 20
