"""Classifier client.

Two modes:
- Stub (default, KYPHRA_STUB=1): deterministic keyword-based classification for offline dev.
- Haiku: calls the Cloudflare Worker endpoint which fronts Anthropic Haiku 4.5.

Must never receive a raw prompt. Input is always the redacted version.
"""
