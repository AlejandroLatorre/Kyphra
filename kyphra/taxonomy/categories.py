"""Canonical list of risk categories as an Enum plus metadata.

Kept in one place so classifier, logger, and UI all agree on ids, labels
and severity bands. Any change here must be reflected in TAXONOMY.md.

Default levels follow typical score floors in TAXONOMY.md (what band the
category usually opens in when present without a numeric score). The hook
uses `effective_level` so the final level is the stricter of score bands and
this default.
"""
from __future__ import annotations

from enum import StrEnum


class Level(StrEnum):
    ALLOW = "ALLOW"
    AVISO = "AVISO"
    ALERTA = "ALERTA"


class Category(StrEnum):
    PII_PERSONAL = "PII_PERSONAL"
    PII_SENSITIVE = "PII_SENSITIVE"
    SECRETS = "SECRETS"
    PROPRIETARY_CODE = "PROPRIETARY_CODE"
    CUSTOMER_DATA = "CUSTOMER_DATA"
    FINANCIAL_DATA = "FINANCIAL_DATA"
    STRATEGIC = "STRATEGIC"
    PROMPT_INJECTION = "PROMPT_INJECTION"
    OFF_SCOPE = "OFF_SCOPE"
    BENIGN = "BENIGN"

    @property
    def default_level(self) -> Level:
        match self:
            case Category.BENIGN:
                return Level.ALLOW
            case Category.PII_PERSONAL:
                return Level.AVISO
            case Category.PII_SENSITIVE:
                return Level.ALERTA
            case Category.SECRETS:
                return Level.ALERTA
            case Category.PROPRIETARY_CODE:
                return Level.AVISO
            case Category.CUSTOMER_DATA:
                return Level.AVISO
            case Category.FINANCIAL_DATA:
                return Level.AVISO
            case Category.STRATEGIC:
                return Level.AVISO
            case Category.PROMPT_INJECTION:
                return Level.ALERTA
            case Category.OFF_SCOPE:
                return Level.ALERTA
