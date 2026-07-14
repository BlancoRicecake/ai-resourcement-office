---
id: dedup-key-normalization
title: Dedup key normalization & set-compare
tags:
  - dedup
  - keys
  - gate
source: seed
confidence: high
created: 2026-07-15
---
Deduplication compares **normalized keys as sets**, not free text — and the model **never loads the
ledger body**, it only passes a candidate key to the host tool and reads back a boolean. **[H6]**

## Normalization

- **Email** — lowercase; apply provider folding where known (Gmail: strip dots and `+tag` in the
  local part). Key = `email:<normalized>`. **Generic local parts** (`info@`, `hello@`, `contact@`,
  `sales@`, `admin@`) are **demoted to weak keys**: they identify a business inbox, not a person, so
  they must not merge two identities ([[identity-resolution]]).
- **Domain** — reduce to the **registrable domain** (Public Suffix List), lowercase, strip `www.`.
  Key = `domain:<domain>`.
- **Handle** — platform-qualify, lowercase, strip `@`. Key = `<platform>:<handle>` (e.g.
  `x:janenails`, `instagram:jane.nails`).

## Set comparison (portable fallback tiers)

The gate ([[cursor-frontier-search]] provides the frontier; the dedup-gate skill provides the timing)
runs at the lightest tier the host supports:

1. **Shell `comm`/`grep`** — `grep -Fxqf ledger-keys.txt <candidate>`; also grep the suppression list.
2. **Python `set()`** — membership test when many keys are checked at once.
3. **SQLite (optional, large scale)** — `SELECT 1 FROM keys WHERE key = ?`, same-shell single file.

In every tier only the **candidate key** crosses into the tool; the ledger body never enters model
context (an absolute rule). This keeps context small and the ledger scalable.

## Why keys, not text

Two records for `Jane's Nails` written differently (`@janenails` vs `Jane Nails ☆`) are the same
person; comparing raw text would miss it or double-count. Normalized keys make the dedup + suppression
gate reliable, which is what proves success criterion **S3** (zero duplicates, gate before extraction).
