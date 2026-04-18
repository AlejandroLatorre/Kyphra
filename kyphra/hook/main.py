"""Entry point for the Claude Code / Cursor UserPromptSubmit hook.

Pipeline:
    stdin (JSON) -> parse -> secrets short-circuit -> redact
                 -> (optional) file inspection -> classify -> level
                 -> log -> notify -> exit 0

Invariant: this function MUST return exit code 0 in every path, including errors.
"""
from __future__ import annotations

import json
import sys
import traceback

from kyphra.hook.classifier import ClassificationResult, classify
from kyphra.hook.levels import score_to_level
from kyphra.hook.logger import LogEvent, log_event
from kyphra.hook.redactor import redact
from kyphra.hook.secrets import find_secrets
from kyphra.taxonomy.categories import Category, Level


def _stderr(level: Level, msg: str) -> None:
    if level == Level.AVISO:
        sys.stderr.write(f"kyphra [AVISO]: {msg}\n")
    elif level == Level.ALERTA:
        sys.stderr.write(f"kyphra [ALERTA]: {msg}\n")


def run() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        sys.stderr.write(f"kyphra: invalid json on stdin: {e}\n")
        return
    except OSError as e:
        sys.stderr.write(f"kyphra: read error: {e}\n")
        return

    prompt = data.get("prompt")
    if not isinstance(prompt, str):
        sys.stderr.write("kyphra: missing or invalid 'prompt' field\n")
        return

    hook_event = data.get("hook_event_name")
    hook_event_name = hook_event if isinstance(hook_event, str) else "UserPromptSubmit"
    session_id = data.get("session_id") if isinstance(data.get("session_id"), str) else None
    cwd = data.get("cwd") if isinstance(data.get("cwd"), str) else None
    transcript_path = data.get("transcript_path") if isinstance(data.get("transcript_path"), str) else None

    secret_sc = bool(find_secrets(prompt))
    if secret_sc:
        redacted = redact(prompt).text
        result = ClassificationResult(max_category=Category.SECRETS, max_score=0.99, outcome="OK")
    else:
        redacted = redact(prompt).text
        result = classify(redacted)

    if result.outcome == "UNKNOWN_TIMEOUT":
        level = Level.ALLOW
        max_score = 0.0
        max_category = Category.BENIGN
        outcome = "UNKNOWN_TIMEOUT"
    else:
        max_score = result.max_score
        max_category = result.max_category
        outcome = result.outcome
        level = score_to_level(max_score)

    summary = f"{max_category.value} score={max_score:.2f}"
    if level in (Level.AVISO, Level.ALERTA):
        _stderr(level, summary)

    log_event(
        LogEvent(
            hook_event_name=hook_event_name,
            session_id=session_id,
            cwd=cwd,
            transcript_path=transcript_path,
            level=level,
            max_category=max_category,
            max_score=max_score,
            redacted_prompt=redacted,
            classifier_outcome=outcome,
            secret_short_circuit=secret_sc,
        )
    )


def main() -> None:
    try:
        run()
    except Exception:
        sys.stderr.write("kyphra: unexpected error\n")
        traceback.print_exc(file=sys.stderr)
    sys.exit(0)


if __name__ == "__main__":
    main()
