"""Source of truth for the classifier system prompt.

This module holds the canonical system prompt text. It is version-controlled
here for review, diffing, and evaluation against the golden set.

At deploy time the string is pushed into the Cloudflare Worker as a secret.
**The Python client never reads or ships this prompt to runtime**; only the
Worker calls Anthropic with it. See SECURITY.md T5.
"""
