"""Tests for kyphra.taxonomy.categories enums and default levels."""

from __future__ import annotations

import pytest

from kyphra.taxonomy.categories import Category, Level


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        (Category.BENIGN, Level.ALLOW),
        (Category.PII_PERSONAL, Level.AVISO),
        (Category.PII_SENSITIVE, Level.ALERTA),
        (Category.SECRETS, Level.ALERTA),
        (Category.PROPRIETARY_CODE, Level.AVISO),
        (Category.CUSTOMER_DATA, Level.AVISO),
        (Category.FINANCIAL_DATA, Level.AVISO),
        (Category.STRATEGIC, Level.AVISO),
        (Category.PROMPT_INJECTION, Level.ALERTA),
        (Category.OFF_SCOPE, Level.ALERTA),
    ],
)
def test_default_level_per_category(category: Category, expected: Level) -> None:
    assert category.default_level is expected


def test_ten_categories() -> None:
    assert len(Category) == 10


def test_three_levels() -> None:
    assert len(Level) == 3
