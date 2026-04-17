"""Entry point for the Claude Code / Cursor UserPromptSubmit hook.

Pipeline:
    stdin (JSON) -> parse -> secrets short-circuit -> redact
                 -> (optional) file inspection -> classify -> level
                 -> log -> notify -> exit 0

Invariant: this function MUST return exit code 0 in every path, including errors.
"""
