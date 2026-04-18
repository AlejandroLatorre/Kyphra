"""Tests for kyphra.hook.levels."""

from __future__ import annotations

from kyphra.hook.levels import score_to_level
from kyphra.taxonomy.categories import Level


def test_score_to_level_allow() -> None:
    assert score_to_level(0.0) is Level.ALLOW
    assert score_to_level(0.49) is Level.ALLOW


def test_score_to_level_aviso() -> None:
    assert score_to_level(0.5) is Level.AVISO
    assert score_to_level(0.74) is Level.AVISO


def test_score_to_level_alerta() -> None:
    assert score_to_level(0.75) is Level.ALERTA
    assert score_to_level(1.0) is Level.ALERTA
