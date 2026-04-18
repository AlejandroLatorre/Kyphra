"""Mapping from classifier score to response level (ALLOW / AVISO / ALERTA)."""
from __future__ import annotations

from kyphra.taxonomy.categories import Level


def score_to_level(score: float) -> Level:
    if score < 0.5:
        return Level.ALLOW
    if score < 0.75:
        return Level.AVISO
    return Level.ALERTA
