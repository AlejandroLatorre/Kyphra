"""Tests for kyphra.hook.redactor.

Cover: each PII type produces the expected token, no bleed-through of raw values,
idempotency (redacting twice is a no-op).
"""
