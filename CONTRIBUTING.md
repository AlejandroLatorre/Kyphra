# Contributing

Single-developer project for now. This file is written for future-me and for any AI assistant operating in the repo.

## Dev environment

- Python 3.11+.
- `pip install -e ".[dev]"` from the repo root.
- `pre-commit install` once per clone.

## Branches

- `main` is protected. No direct pushes; always via PR.
- Feature branches: `feat/<short-slug>`.
- Bug fixes: `fix/<short-slug>`.
- Docs only: `docs/<short-slug>`.

## Commits

- English, imperative mood: `add classifier stub`, not `added classifier stub`.
- One logical change per commit. Split refactors from features.
- Never amend a pushed commit. Create a new commit instead.
- Never use `--no-verify`. If a hook fails, fix the underlying issue.

## Before opening a PR

Run locally:

```bash
ruff check .
ruff format --check .
mypy kyphra
pytest
```

All four must pass.

## Simplify pass before push

Before pushing, ask yourself:

1. Can I delete any file I just added without losing real value?
2. Is any abstraction justified today (as opposed to "we might need it")?
3. Is any comment redundant with well-named code?
4. Does any function do more than one thing?

If yes to any: simplify, re-stage, amend locally (not pushed commits), and push.

## Never push without explicit user approval

Even for trivial changes. The default is local-first.

## Code standards

- One module = one responsibility.
- Files over 200 lines are a smell; refactor them.
- Public functions must have type hints.
- `mypy --strict` must pass.
- No `Any` without a comment explaining why.
- No `print()` in productive code.
- No raw prompts to disk.
- No external calls without redaction.

## Tests

- `pytest` runs the full suite.
- `pytest --cov` for coverage report.
- Minimum 80% coverage in `kyphra/hook/classifier.py`, `kyphra/hook/secrets.py`, `kyphra/hook/redactor.py`.
- Invariant tests live in `tests/test_invariants.py` and enforce the security rules from `SECURITY.md`.

## Releases

No releases yet. When they start, tags follow `v0.X.Y` semver.
