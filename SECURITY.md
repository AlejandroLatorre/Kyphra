# Security

This document captures the threat model, trust boundaries, and concrete controls for Kyphra. It is a living document — every architectural change must review this file.

## Scope

Kyphra protects the privacy and confidentiality of developer prompts sent to AI coding assistants. The asset we are protecting is the content of those prompts and any derived metadata.

## Actors and trust levels

| Actor | Trust level | What they can do |
|-------|-------------|------------------|
| Developer | Semi-trusted | Submits prompts. May accidentally include sensitive data. |
| Security admin | Trusted | Configures Kyphra, reviews alerts, exports logs. |
| Anthropic (processor) | Contractually trusted | Processes redacted prompts under DPA, EU residency. |
| Supabase (processor) | Contractually trusted | Stores aggregated metadata under DPA, EU region. |
| External attacker | Untrusted | May try to exfiltrate prompts, tamper with logs, impersonate admin, inject malicious prompts. |
| Malware on developer machine | Untrusted | May try to read local logs, modify the hook, exfiltrate. |

## STRIDE threat model

> **Status legend.** Mitigations marked `[planned]` are the target design; they are **not yet implemented** in the current bootstrap. Items without a tag are inherent to the architecture (e.g. choice of provider with EU residency). A control is only considered in force when the corresponding module and test land — see [`ROADMAP.md`](ROADMAP.md).

### Spoofing

- **T1 — Fake admin login to dashboard.** `[planned]` Supabase Auth with MFA required for admin role.
- **T2 — Spoofed hook on developer machine** (malware replaces `kyphra.hook.main`). `[planned]` Code signing on release artifacts and integrity check on startup.

### Tampering

- **T3 — Modification of local logs to hide an incident.** `[planned]` Append-only JSONL + AES-GCM encrypted ALERTA archive (AES-GCM includes an authentication tag that detects tampering).
- **T4 — Modification of classification result in transit.** `[planned]` TLS 1.3 with strict certificate verification and HSTS for the Worker; TLS 1.3 with certificate pinning at the Worker layer for outbound calls to `api.anthropic.com`. Anthropic does not support customer-side mTLS; we rely on TLS + pinning, not mTLS, for the upstream leg.
- **T5 — Tampering with the system prompt to weaken the classifier.** `[planned]` The canonical system prompt lives in `kyphra/taxonomy/system_prompt.py` for version control and review, but is deployed as a Cloudflare Workers secret at release time. The classifier client on the developer machine never reads it and never ships it to runtime.

### Repudiation

- **T6 — Developer denies having sent a flagged prompt.** `[planned]` Redacted-prompt logs with timestamp, machine id, and a per-record HMAC chain on the ALERTA archive.

### Information disclosure

- **T7 — Raw prompts sent to Anthropic.** `[planned]` Mandatory `redactor.redact()` before any external call. Any code path that bypasses the redactor is a P0 bug. Enforced by an invariant test.
- **T8 — Raw prompts on disk.** `[planned]` Logs store only the redacted version. Enforced by an invariant test.
- **T9 — Secrets logged in plaintext.** `[planned]` Tokenized previews only (first 10 characters + `***`).
- **T10 — ALERTA logs read by unauthorized user on the dev machine.** `[planned]` AES-GCM encryption with key derived from admin password via PBKDF2-HMAC-SHA256 (≥ 600 000 iterations, 16-byte random salt per record). The derived key is held in memory only for the duration of a read/write and is never persisted.
- **T11 — Anthropic API key leaked.** `[planned]` The key is stored as a Cloudflare Workers secret, never in the developer client. The client calls the Worker, not Anthropic directly.
- **T12 — Supabase service role key leaked.** `[planned]` Clients use only the anon key with RLS enforcing row-level access. The service role key lives only on the Worker.

### Denial of service

- **T13 — Hook hangs and blocks the developer.** `[planned]` Hard 2-second timeout on any external call. On timeout the classifier returns a dedicated `UNKNOWN_TIMEOUT` outcome (not `BENIGN`, to avoid conflating "safe" with "unverified") that maps to `ALLOW` for the developer but is logged and counted separately for the admin digest. The hook always exits 0.
- **T14 — Rate limit exhaustion on Anthropic.** `[planned]` Cloudflare KV rate limiting per developer plus exponential backoff with jitter on the Worker.

### Elevation of privilege

- **T15 — Developer disables the hook.** Accepted risk. Kyphra is not an enforcement tool; it is a detection and alerting tool. `[planned]` Scope violations detected out-of-band by comparing expected vs observed event counts per developer in the admin dashboard.
- **T16 — Regular admin user escalates to super admin.** `[planned]` Supabase RLS policies and a separate `super_admin` role gate.

## Core security invariants

Enforce these in code and verify with tests:

1. No code path writes the raw prompt to disk.
2. No code path calls an external API with the raw prompt.
3. Secret values in prompts are never logged in plaintext.
4. The hook always exits 0.
5. ALERTA events are always encrypted at rest before fsync.
6. The Anthropic API key never appears in the client package or in logs.

## Cryptographic choices

- **Symmetric encryption**: AES-GCM with 256-bit key.
- **KDF**: PBKDF2-HMAC-SHA256 with ≥ 600 000 iterations and 16-byte random salt per record.
- **Transport**: TLS 1.3, HSTS, strict cert pinning for `api.anthropic.com` at the Worker layer.
- **Random**: `secrets.token_bytes()` only; never `random`.

## Retention

| Level | Retention | Storage | Encrypted at rest |
|-------|-----------|---------|-------------------|
| ALLOW | 30 days | local JSONL, counters only | No (counts, no content) |
| AVISO | 60 days | local JSONL + Supabase summary | No (redacted content only) |
| ALERTA | 365 days | local encrypted archive + Supabase summary | Yes |

Retention is enforced by a daily job on the developer machine and by a scheduled Supabase function.

## Disclosure and response

Until we have a dedicated channel, security issues should be reported to `latorreotero@gmail.com` with subject `[Kyphra Security]`. Acknowledgement within 48 hours. No public disclosure until fixed. A formal `SECURITY.md` disclosure policy and `security.txt` will land before design partner onboarding.

## Audit checklist (before each design partner onboarding)

- [ ] `mypy --strict` passes on `kyphra/` with zero errors.
- [ ] `ruff check --select S` (bandit rules) passes on `kyphra/`.
- [ ] All core invariants have a passing test.
- [ ] Secrets scanner: no live keys in the repo (`gitleaks detect`).
- [ ] DPA with Anthropic confirmed in current Console account.
- [ ] Supabase project is in EU region (not US).
- [ ] Cloudflare Worker is pinned to EU datacenters.
- [ ] A documented key rotation procedure exists for the admin password.
