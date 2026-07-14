---
id: channel-tactics
title: Per-channel discovery tactics
tags:
  - channels
  - tactics
  - discovery
source: seed
confidence: high
created: 2026-07-15
---
Each channel needs a different tactic; one query shape does not fit all. **[H9]**

- **Web (Exa + Jina)** — semantic search with Exa to find candidate pages by meaning, then Jina to
  enter a page and extract contact/about content. Uses the **two-stage dedup gate**: domain key
  *before* site entry, email key *after* extraction ([[dedup-key-normalization]]).
- **X / Reddit / LinkedIn (Agent-Reach)** — text + bio search. Query the demand-signal phrasing, then
  read bios for role + contact. Handle key checked immediately.
- **Instagram / Xiaohongshu (小红书) (Agent-Reach)** — hashtag + handle discovery; visual-first
  platforms where the demand signal is often in captions and tags.
- **Threads / TikTok** — fallback tactics via **insane-search** when Agent-Reach has no first-class
  path; treat coverage as best-effort and label channel status accordingly.

Cross-cutting rules:

- **Slow and read-only** on every channel — conservative request intervals, no writes, dedicated
  sub-account for login walls ([[slow-readonly-default]]). A ban is the permanent loss of a channel.
- **Frontier-first** — pre-exclude already-seen space (`-site:`, `-from:`) using the cursor
  ([[cursor-frontier-search]]) so each run explores new ground.
- **Honest channel status** — report success / partial / failed(`discovery-failed`) /
  unauthenticated per channel, and never report a tool failure as `0 results` (docs/limitations.md).
- **Respect robots.txt / ToS** — a source that forbids access is skipped, not forced (RESEARCH.md,
  RFC 9309).

Tooling proper names (Exa, Jina, Agent-Reach, insane-search) are kept as-is; details and links are in
`memory/RESEARCH.md`.
