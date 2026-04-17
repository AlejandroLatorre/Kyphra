"""Local structured logging of classification events.

- ALLOW: aggregated counters only, 30-day retention.
- AVISO: redacted content in JSONL, 60-day retention.
- ALERTA: redacted content in an AES-GCM encrypted archive, 365-day retention.

Raw prompts are NEVER written to disk.
"""
