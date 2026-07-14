---
id: slow-readonly-default
title: Slow, read-only default
tags:
  - safety
  - ban-risk
  - read-only
source: seed
confidence: high
created: 2026-07-15
---
Discovery is **slow and read-only by default**. A ban means the **permanent loss of a channel** — you
never trade that for speed. **[H14]**

- **Read-only** — discover and read; never post, follow, like, or DM as part of discovery. Writes
  raise ban risk and cross into outreach, which is out of scope (the worker never sends).
- **Slow** — keep conservative request intervals, per-session and per-day caps per channel (see
  docs/limitations.md for the conservative default numbers). Do not parallel-blast a channel.
- **Dedicated sub-account** for login-wall channels, never the user's main — so a rate limit or ban
  doesn't damage their primary presence ([[channel-tactics]]).
- **Stop + notify on ban signals** — a challenge, a 429/403 wall, a sudden feed of empty results, or
  `authentication required` means **stop that channel immediately** and tell the user; do not retry
  aggressively (repeated failed requests look like an attack). Record how far the run got so the
  channel status is reported as `partial`.
- **Respect robots.txt / ToS** — a source that disallows access is skipped. Public data scraping sits
  in a contested legal area (hiQ v. LinkedIn, RESEARCH.md); staying read-only, public-only, and
  ToS-respecting is the conservative posture. This is **not legal advice** and the legality of any
  outreach the user later sends is the user's responsibility (docs/security-notes.md).

This underlies success criterion **S10** (read-only, no auto-contact, no stored passwords, and an
actual branch presented on auth failure). Scale comes from **cursor-based frontier coverage over time**
([[cursor-frontier-search]]), not from hammering a channel faster.
