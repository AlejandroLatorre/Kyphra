"""Mapping from classifier score to response level (ALLOW / AVISO / ALERTA)."""
from __future__ import annotations

from typing import Final

from kyphra.taxonomy.categories import Category, Level

_LEVEL_ORDER: Final[tuple[Level, ...]] = (Level.ALLOW, Level.AVISO, Level.ALERTA)


def score_to_level(score: float) -> Level:
    if score < 0.5:
        return Level.ALLOW
    if score < 0.75:
        return Level.AVISO
    return Level.ALERTA


def effective_level(score: float, category: Category) -> Level:
    """Strictest of score-derived level and the category's default floor."""
    s = score_to_level(score)
    c = category.default_level
    return max((s, c), key=lambda x: _LEVEL_ORDER.index(x))
