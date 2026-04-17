# Kyphra

Privacy and confidentiality classifier for developer prompts sent to AI coding assistants.

Kyphra observes the prompts developers send to tools like Claude Code, Cursor, GitHub Copilot and ChatGPT, classifies them by privacy and confidentiality risk, and alerts the security team when it detects leakage of sensitive data. **Kyphra never blocks, rewrites or modifies prompts.** It only observes, classifies and alerts.

## Why

Developers paste sensitive data into AI assistants every day: customer records, API keys, internal algorithms, non-public financial figures. Existing DLP tools are blind to this channel because the interaction happens inside the developer's terminal or IDE, not on the network or in a browser tab.

Kyphra sits on the developer's machine, classifies prompts locally or via a privacy-hardened API, and gives the security team structured visibility without interrupting the developer's flow.

## Positioning

- **CLI-first**, not browser-first. Covers Claude Code, Cursor, local CLIs — not just web chat.
- **File-aware**: inspects references to files in the prompt (`@path/to/file`, `Read()` tools) and classifies based on metadata, not file contents.
- **Non-blocking by design**: keeps the human decision with the security team and stays out of the EU AI Act "high risk" category.
- **Privacy by construction**: PII redaction before any external API call, encrypted local logs for high-severity events, EU data residency.

## Response model — three levels, never block

| Score | Level | Developer experience | Security team | Retention |
|-------|-------|----------------------|---------------|-----------|
| < 0.50 | `ALLOW` | silent | daily aggregate only | 30 days |
| 0.50–0.74 | `AVISO` | subtle stderr message | daily digest | 60 days |
| ≥ 0.75 | `ALERTA` | clear stderr warning | immediate email/Slack | 365 days, encrypted |

## Quickstart (coming soon)

```bash
pip install kyphra          # or pipx for global install
kyphra init                 # sets up local config and hook
kyphra scan ~/.claude/logs  # retroactive audit of prior prompts → PDF report
```

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — system design, data flow, trust zones.
- [`SECURITY.md`](SECURITY.md) — threat model, controls, disclosure policy.
- [`PRIVACY.md`](PRIVACY.md) — GDPR commitments, retention, data processors.
- [`TAXONOMY.md`](TAXONOMY.md) — the nine risk categories.
- [`ROADMAP.md`](ROADMAP.md) — eight-week MVP plan.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — development workflow.

## Status

**Phase**: pre-design-partner MVP. Not production ready. Not open source.

## License

Proprietary. All rights reserved. See [`LICENSE`](LICENSE).
