"""Tests for kyphra.hook.levels."""

from __future__ import annotations

from kyphra.hook.levels import effective_level, score_to_level
from kyphra.taxonomy.categories import Category, Level


def test_score_to_level_allow() -> None:
    assert score_to_level(0.0) is Level.ALLOW
    assert score_to_level(0.49) is Level.ALLOW


def test_score_to_level_aviso() -> None:
    assert score_to_level(0.5) is Level.AVISO
    assert score_to_level(0.74) is Level.AVISO


def test_score_to_level_alerta() -> None:
    assert score_to_level(0.75) is Level.ALERTA
    assert score_to_level(1.0) is Level.ALERTA


def test_effective_level_uses_stricter_of_score_and_category() -> None:
    assert effective_level(0.3, Category.STRATEGIC) is Level.AVISO
    assert effective_level(0.3, Category.OFF_SCOPE) is Level.ALERTA
    assert effective_level(0.8, Category.BENIGN) is Level.ALERTA
    assert effective_level(0.1, Category.BENIGN) is Level.ALLOW
