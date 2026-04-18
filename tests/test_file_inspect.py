"""Tests for kyphra.hook.file_inspect."""

from __future__ import annotations

from pathlib import Path

from kyphra.hook.file_inspect import collect_file_hints


def test_collect_file_hints_csv(tmp_path: Path) -> None:
    p = tmp_path / "sample.csv"
    p.write_text(
        "nombre,email,telefono,dni,plan\n" + ("x,y@z.com,1,12345678A,p\n" * 120),
        encoding="utf-8",
    )
    prompt = f"segment clients using @{p.name}"
    hints = collect_file_hints(prompt, str(tmp_path))
    assert len(hints) == 1
    h = hints[0]
    assert h["path"] == "sample.csv"
    assert "email" in h["pii_header_hits"]
    assert h["extrapolated_row_estimate"] >= 100


def test_collect_skips_parent_traversal(tmp_path: Path) -> None:
    p = tmp_path / "a.csv"
    p.write_text("a,b\n1,2\n", encoding="utf-8")
    assert collect_file_hints("@../outside.csv", str(tmp_path)) == []


def test_collect_empty_without_cwd() -> None:
    assert collect_file_hints("@foo.csv", None) == []
