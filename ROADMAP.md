# Roadmap

Eight-week plan to first paying design partner and a repeatable sales motion. Dates assume a start on **2026-04-17**.

## Week 1–2 — Hook + classifier core (the MVP)

**Goal:** the continuous product (Option 3) works end to end on my own machine. This is the MVP — the CLI audit is a later wedge, not the product.

- Implement `kyphra.taxonomy.categories` and `kyphra.taxonomy.system_prompt`.
- Implement `kyphra.hook.secrets` and `kyphra.hook.redactor`.
- Implement `kyphra.hook.classifier` with stub + Haiku path, 2-second hard timeout, `UNKNOWN_TIMEOUT` outcome on failure.
- Implement `kyphra.hook.main` as a Claude Code `UserPromptSubmit` hook. Always exits 0.
- Local append-only JSONL logger with AES-GCM archive for ALERTA events.
- Golden set v1 (30 labeled prompts) for validating classifier accuracy.
- Invariant tests: no raw prompt to disk, no raw prompt to external API, hook always exits 0.

**Exit criteria:** hook installed on my own machine, classifies prompts live with Haiku, ALERTA events encrypted locally, invariant tests green.

## Week 3–4 — Endpoint + dashboard + first install

**Goal:** move the classifier off the developer machine, stand up the admin surface, make install painless.

- Cloudflare Worker endpoint, EU region, Anthropic key in Workers secrets, prompt caching enabled.
- Supabase project in EU region with RLS and minimal schema: `events`, `developers`, `organizations`.
- Angular 18+ dashboard: events table, filters (level, category, date), event detail modal.
- Supabase Auth for admins with MFA.
- Install script: one command to drop the hook into `~/.claude/settings.json` and register the machine.

**Exit criteria:** install Kyphra on a fresh machine in under 5 minutes, run Claude Code, see events appear in the dashboard within seconds.

## Week 4–5 — Outreach + CLI audit as entry wedge

**Goal:** 5–10 conversations with PYMEs / small startups (10–30 developers). The `kyphra scan` CLI exists only as a retroactive-audit opener — it is not the product.

- Draft outreach email in English + Spanish.
- Build a shortlist of 15 candidates (LinkedIn, WhatsApp entrepreneur groups, direct network).
- Implement `kyphra.cli.audit` reusing the classifier, secrets, and redactor from the hook.
- PDF report template: executive summary, category breakdown, top 10 riskiest prompts.
- Offer: free 1-day retroactive audit + PDF report, no commitment, as the entry to a pilot conversation about the continuous product.
- Record a 2-minute Loom demo of a scan on my own logs.

**Exit criteria:** 3 audits delivered, at least 1 verbal commitment to a 60-day pilot of the continuous hook.

## Week 5–6 — First design partners in shadow mode

**Goal:** 2–3 design partners running Kyphra in production, in shadow mode (no admin dashboard for them yet — just the pilot agreement and weekly reports from us).

- Onboarding playbook: install checklist, legitimate interest notice template, kickoff call agenda.
- Weekly report template: event counts by level and category, top 5 riskiest events (redacted), time to alert.
- Collect feedback on: false positive rate, signal/noise balance, which categories matter to them.
- File Inspection Module v1 (the commercial differentiator vs Harmonic / Prompt Security / Lasso).

**Exit criteria:** at least 1 design partner with real events flagged, written feedback collected.

## Week 7–8 — Testimonials and Laberit entry

**Goal:** case study + signed testimonials + first conversation with Laberit.

- Write case study: design partner challenge, Kyphra deployment, outcomes (events found, time saved, risks mitigated).
- Get at least 1 signed testimonial quote usable publicly.
- Prepare Laberit deck: problem, product, why now, case study, pricing, assessment offer.
- Schedule Laberit meeting using internal contact.

**Exit criteria:** signed testimonial in hand, Laberit meeting scheduled.

## Beyond week 8

- Decide on phase 2: self-hosted Gemma 4 on Hetzner GPU, triggered only by a concrete CISO objection or a client that refuses Anthropic for non-negotiable reasons.
- Decide on phase 3: browser extension and/or network proxy.
- Revisit pricing based on design partner feedback.
- Consider hiring: earliest hire is a go-to-market partner, not an engineer.

## Out of scope until further notice

- Multi-tenant SaaS.
- Billing integration.
- Open-source release.
- Integrations with SIEM / SOAR (will arrive with the first enterprise client, not before).
- Non-EU hosting.
