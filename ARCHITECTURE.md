# Architecture

## Goals

1. Observe prompts sent by developers to AI assistants with minimal latency (< 150 ms p95).
2. Classify each prompt by privacy/confidentiality risk without exposing its contents to parties that do not need them.
3. Give the security team structured, queryable visibility without interrupting the developer.
4. Stay out of the EU AI Act "high risk" category by never automating a blocking decision on a human.

## Non-goals (current MVP phase)

- Blocking, rewriting or modifying prompts.
- Multi-tenant SaaS.
- Browser extension.
- Network-level proxy.
- Self-hosted inference (phase 2).

## Components

```
                   Developer machine
 ┌──────────────────────────────────────────────────────────┐
 │                                                          │
 │  Claude Code / Cursor / CLI                              │
 │        │                                                 │
 │        │  UserPromptSubmit hook                          │
 │        ▼                                                 │
 │  ┌─────────────────┐                                     │
 │  │  kyphra.hook    │                                     │
 │  │    main.py      │                                     │
 │  └────────┬────────┘                                     │
 │           │                                              │
 │           ▼                                              │
 │  ┌─────────────────┐    ┌──────────────────┐             │
 │  │  secrets.py     │───▶│  short-circuit   │             │
 │  │  (regex local)  │    │  → ALERTA        │             │
 │  └────────┬────────┘    └──────────────────┘             │
 │           │ no match                                     │
 │           ▼                                              │
 │  ┌─────────────────┐                                     │
 │  │  redactor.py    │   removes PII before external call  │
 │  └────────┬────────┘                                     │
 │           │                                              │
 │           ▼                                              │
 │  ┌─────────────────┐                                     │
 │  │  file_inspect   │   metadata only, never contents     │
 │  │  (optional)     │                                     │
 │  └────────┬────────┘                                     │
 │           │                                              │
 │           ▼                                              │
 │  ┌─────────────────┐         HTTPS/EU          ┌──────────────────┐
 │  │  classifier.py  │ ────────────────────────▶ │  edge endpoint   │
 │  │  (client)       │                            │  (Cloudflare     │
 │  └────────┬────────┘                            │   Workers, EU)   │
 │           │                                     └────────┬─────────┘
 │           │                                              │
 │           │                                              ▼
 │           │                                   ┌──────────────────┐
 │           │                                   │  Anthropic API   │
 │           │                                   │  Haiku 4.5 (EU)  │
 │           │                                   └──────────────────┘
 │           ▼
 │  ┌─────────────────┐
 │  │  levels.py      │   score → ALLOW / AVISO / ALERTA
 │  └────────┬────────┘
 │           │
 │           ▼
 │  ┌─────────────────┐   ┌──────────────────┐
 │  │  logger.py      │──▶│  local JSONL +   │
 │  │                 │   │  encrypted       │
 │  │                 │   │  ALERTA archive  │
 │  └────────┬────────┘   └──────────────────┘
 │           │
 │           ▼
 │  ┌─────────────────┐      HTTPS/EU        ┌──────────────────┐
 │  │  notifier.py    │ ───────────────────▶ │  Supabase        │
 │  │                 │                       │  (EU, Postgres)  │
 │  └─────────────────┘                       └────────┬─────────┘
 │                                                     │
 └──────────────────────────────────────────────────────┼──────────
                                                       ▼
                                              ┌──────────────────┐
                                              │  Angular admin   │
                                              │  dashboard       │
                                              └──────────────────┘
```

## Trust zones

| Zone | Who controls it | What lives there | Threats |
|------|-----------------|------------------|---------|
| Dev process | developer | raw prompt | developer mistakes, malware on machine |
| Local Kyphra process | dev + Kyphra code | redacted prompt, classification, logs | unauthorized local reads, log exfiltration |
| Edge endpoint (CF) | Kyphra ops | redacted prompt in transit | TLS misconfig, Worker secret leak |
| Anthropic API | Anthropic (EU) | redacted prompt during inference | Anthropic-side incident, DPA breach |
| Supabase | Supabase (EU) | aggregated events, no raw prompts | credential leak, RLS misconfig |
| Admin browser | security admin | aggregated events, dashboards | session hijack, XSS |

## Data flow, in words

1. Developer submits a prompt through Claude Code (or compatible tool). The `UserPromptSubmit` hook fires.
2. `main.py` receives the prompt from stdin and runs `secrets.scan_secrets()` first. If it finds a known secret pattern, Kyphra short-circuits: the classification is `SECRETS` with score 0.99, the Haiku call is skipped, and the event is routed to `ALERTA`.
3. Otherwise, `redactor.redact()` replaces PII (emails, DNIs, NIEs, phones, IBANs, card numbers) with tokens like `<EMAIL>`, `<DNI>`.
4. If the prompt contains file references, the optional file inspection module computes metadata (header, line count, PII density) and attaches it to the request. File contents are never sent.
5. `classifier.classify()` sends the redacted prompt to a Cloudflare Worker in the EU region. The Worker forwards the call to the Anthropic API with the cached system prompt.
6. The response is a JSON with categories, scores, and reasons. `levels.score_to_level()` maps `max_score` to `ALLOW` / `AVISO` / `ALERTA`.
7. `logger.log_event()` writes a structured event locally. `AVISO` goes to a plain JSONL with 60-day retention. `ALERTA` goes to an AES-GCM encrypted archive with 365-day retention.
8. `notifier.notify()` pushes a summary of `AVISO` and `ALERTA` events to Supabase for the admin dashboard. No raw or redacted prompts are pushed — only aggregated metadata.
9. The hook returns exit code 0. The developer's flow is never interrupted.

## Why these choices

| Choice | Why |
|--------|-----|
| Python for the hook | Ubiquitous on developer machines, fast enough, same language as classifier logic. |
| Cloudflare Workers, EU region | Low latency to Anthropic EU endpoints, cheap, scales to zero, KV for secrets. |
| Anthropic Haiku 4.5 | Best accuracy/cost ratio for the classification task; DPA available with EU residency; prompt caching cuts cost 10x on the static system prompt. |
| Supabase free EU | Postgres + auth + RLS in EU region at zero cost for the MVP; migration path to self-hosted Postgres later. |
| Angular 18+ | Alejandro's primary frontend stack; signals keep the dashboard simple. |
| AES-GCM + PBKDF2 for ALERTA | Symmetric encryption at rest is sufficient; admin password derives the key. |
| No network proxy, no browser extension | Kept out of phase 1 to preserve focus and minimize install friction for design partners. |

## Migration path

- **Phase 1 (current):** external API (Haiku) with hardened redaction and DPA.
- **Phase 2:** optional self-hosted Gemma 4 on Hetzner GPU for clients that refuse external LLM calls. Same interface on the classifier side.
- **Phase 3:** browser extension and network proxy as complementary collection surfaces.
