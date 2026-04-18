# Kyphra

**Product line:** privacy and confidentiality observability for developer prompts sent to AI coding assistants (Claude Code, Cursor, Copilot, ChatGPT, and similar). **Privacy-first**, EU AI Act–aligned positioning: Kyphra **observes, classifies, alerts, and logs**. It **never blocks, rewrites, or modifies** prompts or model calls — the hook **always exits 0**; security keeps the human decision.

Personal project (not NTT Data). Earlier working name: SentinelAI.

## Why

Developers paste sensitive data into AI assistants every day: customer records, API keys, internal algorithms, non-public financial figures. Classic DLP is blind to this channel because the interaction often happens in the **terminal or IDE**, not only in the browser or on a managed network path.

Kyphra sits **CLI-first** on the developer machine: **regex short-circuit for secrets**, **PII redaction** before any remote classifier call, then **HTTPS → Cloudflare Worker (EU) → small LLM** (today: OpenRouter + default `anthropic/claude-3.5-haiku`) to interpret **composition and intent**, not only keywords. Optional **organization context** (`KYPHRA_ORG_*` env + `kyphra_org` in hook JSON) enables **`OFF_SCOPE`** when work does not fit the stated sector/scope (e.g. banking vs drones). The final level is the stricter of **score bands** and **category default floor** (`effective_level`).

## What is implemented today vs planned

| Area | Status |
|------|--------|
| Hook pipeline (`kyphra.hook.main`) | **Yes** — stdin JSON, org merge, secrets scan, redact, classify (stub or Worker), levels, local JSONL + ALERTA encryption |
| Cloudflare Worker classifier | **Yes** — EU deploy path; OpenRouter; optional `org` in POST body |
| Stub classifier | **Yes** — offline dev; banking + drone-style **OFF_SCOPE** heuristics |
| **File-aware** `@file` inspection | **Yes (v1)** — `collect_file_hints` under `cwd`; CSV/JSON/txt/md/tsv/xml; header + row estimate + PII-like column hits → `file_hints` to Worker / stub; summary in logs |
| **Notifier** (`KYPHRA_NOTIFY_WEBHOOK`) | **Yes** — optional POST of **metadata only** (no prompt body) for AVISO/ALERTA |
| Supabase + Angular dashboard | **Planned** — see `ROADMAP.md` |

## Response model — three levels, never block

| Score | Level | Developer experience | Security team | Retention (target) |
|-------|-------|----------------------|----------------|-------------------|
| < 0.50 | `ALLOW` | silent | daily aggregate only | 30 days |
| 0.50–0.74 | `AVISO` | subtle stderr message | daily digest | 60 days |
| ≥ 0.75 | `ALERTA` | clear stderr warning | immediate email/Slack (when wired) | 365 days, encrypted |

Category floors (e.g. `OFF_SCOPE` → ALERTA by default) can raise the level above the score alone; see `kyphra.hook.levels.effective_level`.

## Quickstart (developer machine)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"   # if extras defined; else pip install -e .
export KYPHRA_STUB=1
export KYPHRA_HOME="${HOME}/.kyphra"
echo '{"prompt":"refactor this loop"}' | python -m kyphra.hook.main
```

For live classification, set `KYPHRA_STUB=0`, `KYPHRA_CLASSIFIER_ENDPOINT` to your Worker URL, and optional `KYPHRA_ORG_SECTOR` / `KYPHRA_NOTIFY_WEBHOOK`. See `.env.example`.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system design, data flow, trust zones.
- [`SECURITY.md`](SECURITY.md) — threat model, controls, disclosure policy.
- [`PRIVACY.md`](PRIVACY.md) — GDPR commitments, retention, data processors.
- [`TAXONOMY.md`](TAXONOMY.md) — **ten** risk categories (incl. `OFF_SCOPE`).
- [`ROADMAP.md`](ROADMAP.md) — eight-week MVP plan.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development workflow.

## Status

**Phase:** pre-design-partner MVP. Not production ready. Not open source.

## License

Proprietary. All rights reserved. See [`LICENSE`](LICENSE).
