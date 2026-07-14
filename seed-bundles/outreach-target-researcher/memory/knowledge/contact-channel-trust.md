---
id: contact-channel-trust
title: Contact-channel trust hierarchy
tags:
  - contact
  - trust
  - extraction
source: seed
confidence: high
created: 2026-07-15
---
Not all contact points are equal. Prefer the one that best signals a real, business-owned, reachable
channel. **[H4]**

Trust hierarchy (strongest first):

1. **Own-domain email** (`jane@janenails.com`) — a business identity; the person controls the domain.
2. **Bio link** (an own site or linktree in a profile bio) — self-published, intentional.
3. **Contact form** — reachable, but higher friction and no direct address.
4. **DM handle** — the platform handle itself, used only when nothing else is public.

Always record the contact **type** explicitly (`email` / `handle` / `form` / `linktree`) — success
criterion **S4** requires 100% type coverage.

**Personal free-mail flag:** a Gmail / Naver / QQ / Outlook personal address is captured but flagged
as a **personal channel** — weaker for business outreach and a privacy caution. It does not merge two
identities the way an own-domain address does (see [[dedup-key-normalization]] on generic vs strong
keys).

**Provenance is mandatory** on every contact: the **source URL + capture timestamp**. And record
**freshness** (the post/refresh date), which feeds recency decay in [[intent-signal-strength]] and the
recency axis of [[fit-scoring-rubric]]. Extraction is public-only: never pull a contact from a private
account, a gated page, or a source whose robots.txt / ToS forbids it ([[slow-readonly-default]]).
Outreach legality by channel (e.g. Korea Network Act §50 on advertising transmission) is summarized in
docs/security-notes.md and is the user's responsibility.
