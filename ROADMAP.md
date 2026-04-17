# Roadmap

Eight-week plan to first paying design partner and a repeatable sales motion. Dates assume a start on **2026-04-17**.

## Week 1–2 — CLI audit standalone (entry wedge)

**Goal:** ship `kyphra scan <log-dir>` that reads historical Claude Code / Cursor logs and produces a PDF report with prompts classified retroactively. No backend, no auth, no dashboard.

- Implement `kyphra.cli.audit` with Typer.
- Implement `kyphra.taxonomy.categories` and `kyphra.taxonomy.system_prompt`.
- Implement `kyphra.hook.classifier` with stub + Haiku path.
- Implement `kyphra.hook.secrets` and `kyphra.hook.redactor` — the CLI reuses them.
- Golden set v1 (30 labeled prompts) for validating classifier accuracy.
- PDF template with Kyphra branding, executive summary, category breakdown, top 10 riskiest prompts.
- Record a 2-minute Loom demo walking through a scan on our own logs.

**Exit criteria:** `kyphra scan` runs end-to-end on my own `~/.claude/logs`, produces a valid PDF, Loom uploaded.

## Week 2–3 — Outreach

**Goal:** 5–10 conversations with PYMEs / small startups (10–30 developers) from the personal circle.

- Draft outreach email in English + Spanish.
- Build a shortlist of 15 candidates (LinkedIn, WhatsApp entrepreneur groups, direct network).
- Offer: free 1-day retroactive audit + PDF report. No commitment required.
- Track replies and meetings in a simple spreadsheet.

**Exit criteria:** 3 audits delivered, at least 1 verbal commitment to a 60-day pilot.

## Week 3–4 — Hook + endpoint + minimal dashboard

**Goal:** the continuous product (Option 3) works end to end in shadow mode.

- `kyphra.hook.main` as a Claude Code `UserPromptSubmit` hook.
- Cloudflare Worker endpoint, EU region, with Anthropic API key in Workers secrets and prompt caching enabled.
- Supabase project in EU region with RLS and minimal schema: `events`, `developers`, `organizations`.
- Angular 18+ dashboard with a single page: events table, filters (level, category, date), event detail modal.
- Supabase Auth for admins with MFA.

**Exit criteria:** install Kyphra from scratch on a fresh machine in under 5 minutes, run Claude Code, see events in the dashboard within seconds.

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
