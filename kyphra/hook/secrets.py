"""Local regex short-circuit for known secret patterns.

Runs BEFORE any external call. Matches here skip the Haiku round-trip
and go straight to ALERTA. Patterns are inspired by TruffleHog / Gitleaks.
"""
