---
name: dedup-gate
description: Use during discovery to deduplicate and suppress candidates BEFORE expensive extraction. Covers per-channel gate timing (web two-stage domain-then-email, social handle-immediate), key normalization, suppression-list check, and the portable fallback tiers.
---

# Inline dedup & suppression gate

The gate exists to **discard duplicates and suppressed contacts before any expensive step** (site
entry, extraction, scoring). It runs **inline**, and the model **never loads the ledger body** — it
compares only normalized keys through the host tool. This is what proves **S3 (zero duplicates,
gate before contact extraction)**.

## Gate timing per channel

- **Web — two-stage gate:**
  1. **Domain key first**, *before entering the site*. Normalize the domain (strip `www.`,
     lowercase, registrable domain). If the domain key is already in `ledger-keys.txt` or the
     suppression list, **skip the site entirely** — no fetch, no cost.
  2. **Email key second**, *after extraction*. Once a contact email is extracted, normalize it and
     check again before the lead is written.
- **Social — handle immediate:** normalize the handle (lowercase, strip `@`, platform-qualified,
  e.g. `x:janedoe`) and check the moment a candidate is seen, before opening the profile / bio.

## Key normalization ([[dedup-key-normalization]])

- **Email:** lowercase; for known providers apply provider rules (e.g. Gmail dot/`+tag` folding);
  key = `email:<normalized>`. Generic local parts (`info@`, `hello@`, `contact@`, `sales@`) are
  **demoted to weak keys** — they identify a business inbox, not a person, so they don't merge two
  people.
- **Domain:** registrable domain, lowercased, `www.` stripped; key = `domain:<domain>`.
- **Handle:** platform-qualified, lowercased, `@` stripped; key = `<platform>:<handle>`.

## Suppression (DNC / erasure) — checked inline

The gate checks **both** `ledger-keys.txt` (already-seen) **and** `do-not-contact.txt` (the DNC /
erasure suppression list) on every candidate. A suppressed key is **permanently blocked from
re-collection** — this is how an erasure request stays honored across runs (see
`worker/skills/erasure-handling.md`).

## Portable fallback tiers (the model never loads the ledger body)

Pick the lightest tier the host supports:

1. **Shell `comm` / `grep`** — `grep -Fxqf ledger-keys.txt` (and the suppression file) against the
   candidate key. Simplest; good for small/medium ledgers.
2. **Python set** — load the key files into a `set()` and test membership. Good when many keys are
   checked in one run.
3. **SQLite (optional, large scale)** — `SELECT 1 FROM keys WHERE key = ?`. Only when the ledger is
   large enough that plain-text set-comparison is slow. This is the same-shell single-file backend
   from onboarding, not a separate server.

In every tier the model passes only the **candidate key** and reads back a boolean — the ledger body
never enters context.

## After the gate

- Passing keys proceed to contact extraction; failing keys are dropped with a reason
  (`duplicate` / `suppressed`) logged for the S3 proof.
- Newly written leads append their normalized keys to `ledger-keys.txt` (proposed as a memory update
  candidate, not auto-committed).

## If the discovery tools are missing — never simulate

The gate assumes real candidates arrived from a real discovery tool. If the discovery tools
(Agent-Reach / Exa / web fetch) are **unavailable or unwired** in an otherwise tool-capable host,
report the affected channel as **`discovery-failed`** and guide the user to install/authenticate it —
**never fabricate or simulate candidates** to feed the gate. A missing tool means "we couldn't look,"
not "nothing there" (see `docs/limitations.md`). Simulation is only ever an **explicit test/demo mode
the user requested**, labeled as such — never the worker's own degrade path.
