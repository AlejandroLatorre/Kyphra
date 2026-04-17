# Privacy

Kyphra classifies prompts to *reduce* privacy exposure. It cannot do that credibly unless the tool itself is privacy-respecting by design. This document states the commitments and how they are implemented.

## Principles

1. **Minimize what leaves the machine.** The only data that crosses a trust boundary is a redacted prompt plus structured metadata. Never file contents, never raw secrets, never identifiers of natural persons.
2. **Minimize what is stored.** We persist redacted prompts locally with short retention. Remote persistence only covers aggregated counts and references to local records.
3. **Minimize who can see.** Role-based access, MFA for admins, RLS on Supabase, no engineer of Kyphra has access to client data in production.
4. **Make the local host the primary control point.** Encryption at rest for high-severity records, rotating keys under admin control, local key material never leaves the machine.

## GDPR posture

### Roles

- **Data controller**: the customer (the organization whose developers run Kyphra).
- **Data processor**: Alejandro Latorre, operating Kyphra.
- **Sub-processors**: Anthropic (inference), Cloudflare (edge), Supabase (storage). All with DPAs and EU regions.

### Lawful basis

- **Legitimate interest** of the controller to detect and prevent data leakage to AI assistants. Documented legitimate interest assessment required before onboarding.
- **Developers must be informed** before Kyphra is installed on their machines. A template notice is shipped in [`docs/notice_to_developers.md`](docs/notice_to_developers.md) (to be added).

### Data subject rights

Kyphra processes data about developers (prompt content they wrote, timestamps, machine id). For each GDPR right we implement:

| Right | How |
|-------|-----|
| Access (art. 15) | Admin can export all events tagged with a given developer id as a signed JSON bundle. |
| Rectification (art. 16) | Events are classifications, not assertions about the data subject. No rectification workflow required. |
| Erasure (art. 17) | Admin endpoint to delete all events for a developer id, both locally (signed command sent to the hook) and on Supabase. |
| Restriction (art. 18) | Admin can mark a developer id as "frozen": new events are accepted but flagged unavailable for dashboards until review. |
| Portability (art. 20) | Same bundle as art. 15, in JSON format. |
| Object (art. 21) | Uninstalling Kyphra is the primary mechanism. Developer-level opt-out documented for customers with works councils. |
| Not subject to automated decision (art. 22) | **Kyphra never makes a binding decision about a person.** This is why we do not block and why we stay out of "high risk" EU AI Act. |

### EU AI Act

Kyphra classifies prompts for risk. It does not evaluate people, make hiring or benefit decisions, or impose an automated consequence on a data subject. We believe Kyphra falls into **limited risk / general AI system** with transparency obligations only. The "never block" rule is a deliberate choice to stay in this band.

A formal EU AI Act conformity assessment will be commissioned before general availability.

## Data processors

| Processor | Purpose | Region | DPA | Data sent |
|-----------|---------|--------|-----|-----------|
| Anthropic | Haiku 4.5 inference | EU | DPA via Console | Redacted prompt, system prompt (cached) |
| Cloudflare | Workers edge endpoint | EU data centers only | Cloudflare standard DPA | Redacted prompt in transit, short-lived logs |
| Supabase | Postgres persistence | EU (`eu-central-1` or `eu-west-1`) | Supabase DPA | Aggregated event counts and metadata — no prompts |

## Retention

See [`SECURITY.md`](SECURITY.md) for exact windows. Summary:

- `ALLOW`: 30 days, counters only.
- `AVISO`: 60 days, redacted content.
- `ALERTA`: 365 days, encrypted.

All retention windows are enforced automatically; admin can shorten them further by configuration but not extend them beyond the documented maxima.

## What Kyphra never does

- Send file contents to any external service.
- Send raw secrets or credentials to any external service.
- Send unredacted PII to any external service.
- Send anything to a non-EU region by default. A customer explicitly choosing US hosting is a contractual opt-in, not a default.
- Make a binding automated decision about a developer.
- Train on customer prompts. No customer data is used to improve the classifier. Haiku is called with zero-retention parameters where available; system prompt improvements come from synthetic data and the curated golden set.
