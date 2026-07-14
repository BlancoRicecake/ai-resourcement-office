---
name: contact-extraction
description: Use after the dedup gate to extract a public contact point for a passing lead. Covers the contact-channel trust hierarchy, per-channel extraction (web site-entry, social bio link), provenance capture, freshness, and the public-only rule.
---

# Contact extraction

Only leads that **passed the dedup gate** reach this step. The job is to extract **one public
contact point** and record its **type, value, provenance, and freshness**. No contact, no complete
lead — leave the value blank with a reason rather than inventing one.

## Trust hierarchy ([[contact-channel-trust]])

Prefer, in order:

1. **Own-domain email** (`jane@janenails.com`) — strongest; a business identity.
2. **Bio link** (linktree / personal site in a profile bio).
3. **Contact form** (a form URL when no email is exposed).
4. **DM handle** (the platform handle itself, when nothing else is public).

Record the **type explicitly** (`email` / `handle` / `form` / `linktree`) — this is **S4 (contact
type 100%)**. A personal free-mail address (Gmail/Naver/QQ) is captured but **flagged as a personal
channel** (weaker for business outreach, and a privacy caution).

## Per-channel extraction

- **Web:** on the two-stage gate's pass, enter the site (Jina) and read the contact / about / footer
  for an own-domain email or form. Capture the exact page URL as provenance.
- **Social:** read the profile bio for a link (own domain > linktree) or, failing that, record the
  handle as the contact. Capture the profile URL as provenance.

## Provenance & freshness (required)

For every contact record:

- **Provenance** = the **source URL + capture timestamp** (ISO 8601). This is mandatory for every
  lead — it lets the user verify and lets outreach legality be reasoned about.
- **Freshness** = the **post / page refresh date** of the demand signal or profile. Stale signals
  decay the intent grade ([[intent-signal-strength]]).

## Public-only rule (hard)

- Extract **public business / creator contacts only.** Do **not** extract from private accounts,
  gated pages, leaked dumps, or sources whose robots.txt / ToS forbid it.
- **Exclude private personal accounts** — a personal, non-commercial individual is out of scope
  even if reachable. (A **solo/individual-run brand or creator** page *is* in scope — that is a
  reachable business person, a plus, not a private individual. See [[human-vs-solo-brand-vs-bot]].)
- Never store passwords; never bypass a login wall to reach a contact.
