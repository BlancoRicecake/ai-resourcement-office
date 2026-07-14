---
name: erasure-handling
description: Use when someone asks not to be contacted or to be erased, or when a lead must be suppressed. Covers adding keys to the do-not-contact suppression list, purging the ledger, and how the inline dedup gate enforces permanent suppression.
---

# Erasure & do-not-contact handling

People can ask not to be contacted or to be removed. Honor it **permanently and across runs**. The
mechanism is the suppression list plus the inline dedup gate.

## The suppression list

`memory/targets/<slug>/do-not-contact.txt` holds **normalized keys** (same normalization as the
dedup gate — `email:`, `domain:`, `<platform>:handle`), one per line, with a short reason/date
comment. It is the **standard ledger file** for suppression.

## When a suppression / erasure request arrives

1. **Normalize** the contact(s) to keys ([[dedup-key-normalization]]).
2. **Add** the keys to `do-not-contact.txt` (proposed as a memory update candidate — but treat
   erasure as high priority and surface it prominently for approval).
3. **Purge** any existing matching rows from `leads-ledger.jsonl` and any pending output CSV, and
   drop the keys from active results. Keep the suppression key itself (that is what enforces future
   blocking) — do not keep the person's data, only the minimal key needed to *not* re-collect them.
4. **Confirm** to the user what was suppressed and purged.

## How enforcement works

The inline dedup gate checks `do-not-contact.txt` on **every** candidate, on every future run
(`worker/skills/dedup-gate.md`). A suppressed key can therefore **never be re-collected**, even if
the same person resurfaces under the same handle/domain/email in a later discovery pass. This is the
permanent, cross-run guarantee.

## Data-minimization note

The suppression list is a privacy-protective record: it stores only the **normalized key** needed to
avoid re-contacting someone, not their profile or personal data. This aligns with the erasure intent
(GDPR Art. 17 / PIPA) rather than working against it — see `docs/security-notes.md`. Do not persist
other personal PII into memory as part of handling an erasure request.
