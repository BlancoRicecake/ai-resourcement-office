---
id: cursor-frontier-search
title: Cursor-based frontier search
tags:
  - cursor
  - frontier
  - efficiency
source: seed
confidence: high
created: 2026-07-15
---
Each run should explore **new frontier**, not re-walk ground already covered. A cursor plus query
pre-exclusion makes that happen. **[H13]**

- **Cursor in `state.yaml`** — record where the last run stopped per channel/query (last page,
  last date window, last hashtag cursor, exhausted queries). The next run resumes from there.
- **Query pre-exclusion** — bake already-seen space into the query itself: `-site:` for domains
  already in the ledger, `-from:` for handles already collected, date windows past the last cursor.
  This avoids spending fetch budget on known results before the dedup gate even runs.
- **Ledger-aware** — the frontier respects `ledger-keys.txt` (already collected) and
  `do-not-contact.txt` (suppressed), so exploration never loops back onto them
  ([[dedup-key-normalization]]).

Why it matters: discovery is **slow and read-only** ([[slow-readonly-default]]) — budget is scarce, so
every fetch should target unexplored space. Re-walking old ground burns rate limit (raising ban risk)
for zero new leads.

**Frontier exhaustion** is a signal, not a failure: when the cursor shows a channel/query space is
used up and few new leads appear, surface it and propose **expanding the definition** (new keywords,
adjacent channels, wider recency/region) — a quality-first move, not padding
([[fit-scoring-rubric]]). Advance the cursor as a memory update candidate at the end of each run
(no auto-commit).
