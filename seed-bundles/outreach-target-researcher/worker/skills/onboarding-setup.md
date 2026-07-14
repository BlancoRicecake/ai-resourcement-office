---
name: onboarding-setup
description: Use on the first run for a new environment. An environment-readiness gate before any ICP Setup or discovery — verifies Agent-Reach (with install guidance), insane-search fallback, web (Exa/Jina), storage deps (sqlite/python), and the Excel-generation env (openpyxl/pandas), reports a ✓/✗ readiness summary, then covers login-wall channel guidance (dedicated sub-account), the storage-backend choice (plain-text default vs optional SQLite + migration), and the xlsx/CSV output choice.
---

# Onboarding & setup

Run this once when a user first uses the bundle in an environment. It sets up tooling, channel
access, and the storage backend. **Speak the user's language.**

## 1. Environment readiness check (a gate — do this before any ICP Setup or discovery)

Confirm the environment can actually run the job before starting. This is a **gate**: probe each
dependency, guide installation of anything missing, report a readiness summary, and only proceed
once the essentials are in place (or the user accepts a degraded mode). **Never fabricate** to
cover a missing tool.

**0. Runtime.** Confirm shell/code execution + filesystem + network are available. If this is a
no-tool chat, stop — this worker is unsupported here (see `AGENTS.md`); nothing below can run.

**Agent-Reach (primary discovery — social + web).** Check it is installed (`agent-reach version`,
then `agent-reach doctor`). If missing, guide installation **before** proceeding — e.g.
`pipx install https://github.com/Panniantong/agent-reach/archive/main.zip` then
`agent-reach install --env=auto`, or hand the agent the install doc at
`https://raw.githubusercontent.com/Panniantong/agent-reach/main/docs/install.md`. Without it,
social channels are `discovery-failed` (not `0 results`); keyless web (Exa/Jina) may still work.
`agent-reach doctor` also reports which social channels are authenticated (X, Reddit, LinkedIn,
Instagram, Xiaohongshu, Threads, TikTok) and whether Exa / Jina web fetch works (keyless tier is
fine; a key would raise limits).

**insane-search (fallback reader).** Check whether it is available (Threads public, TikTok
best-effort, otherwise-blocked public pages). It is a **Claude Code plugin**; if missing and the
host is Claude Code, add it: `/plugin marketplace add https://github.com/fivetaku/gptaku_plugins.git`
-> `/plugin install insane-search@gptaku-plugins` -> `/reload-plugins`. It is **optional** — the
worker runs without it, with reduced fallback coverage.

**Storage deps.** Confirm a shell + `sqlite3` (or Python's built-in `sqlite3`) — decides §3.

**Excel-generation env.** Probe whether `openpyxl` or `pandas` is importable — decides §4. If absent
and the user wants the `.xlsx` outreach worksheet, offer `pip install openpyxl`; otherwise CSV is
the automatic fallback (same 16-column schema).

**Readiness summary — report to the user before proceeding.** Present a ✓/✗ checklist with the fix
for each ✗, then confirm how to proceed:

| Item | State | If missing |
| --- | --- | --- |
| Runtime (shell/net) | ✓/✗ | unsupported → stop |
| Agent-Reach (installed / channels authed) | ✓/✗ | install (above) / log in per §2 |
| insane-search (fallback) | ✓/✗ | optional plugin install (above) |
| Web (Exa / Jina) | ✓/✗ | keyless usually works |
| Storage (sqlite / python) | ✓/✗ | plain-text default still works |
| Excel lib (openpyxl / pandas) | ✓/✗ | `pip install openpyxl`, else CSV |

Then ask: **proceed now**, **install a missing piece first**, or **run in a degraded mode**
(e.g. web-only discovery, or CSV instead of `.xlsx`). Do not start ICP Setup until this is
acknowledged.

## 2. Login-wall channels

Several channels (LinkedIn, Instagram, Xiaohongshu, etc.) are behind a login. Agent-Reach uses the
user's **own interactive browser session** — this bundle **never stores passwords**.

- Advise using a **dedicated discovery sub-account**, not the user's main account, so that any rate
  limit or ban does not affect their primary presence.
- Keep discovery **slow and read-only** ([[slow-readonly-default]]). A ban means the permanent loss
  of that channel.

## 3. Storage backend (plain-text default vs SQLite)

The per-target ledger is **plain-text by default** (`leads-ledger.jsonl` + `ledger-keys.txt` +
`state.yaml`). The reason plain-text is the default is **not** "chat can't run SQLite" — this
runtime always has a shell. It is because plain-text is **human-readable, needs no DB
initialization, and is simple**.

**SQLite is an optional performance backend inside the same shell** — not a separate server, just a
single file via the `sqlite3` binary or Python's built-in `sqlite3` (free, serverless). It helps
when a ledger grows large (tens of thousands of keys) and set-comparison in plain text gets slow.

Ask the user to choose:

- **(A) Set up SQLite now** — create `ledger.db` with a `leads` table and a `keys` table
  (`key TEXT UNIQUE`). The dedup gate becomes `SELECT 1 FROM keys WHERE key = ?`.
- **(B) Start plain-text, migrate later** — begin with the jsonl/txt files; migrate when volume
  warrants.

### Migration procedure (plain-text -> SQLite, later)

1. `CREATE TABLE keys(key TEXT PRIMARY KEY);` and `CREATE TABLE leads(...);` mirroring the jsonl
   fields.
2. Import: stream `ledger-keys.txt` into `keys` (dedup on insert), and `leads-ledger.jsonl` into
   `leads`.
3. Point the dedup gate at the `keys` table. Keep the plain-text files as a human-readable mirror;
   they remain the source of truth unless the user decides otherwise.

Regardless of backend, the model **never loads the ledger body** — it only compares normalized keys
through the host tool ([[dedup-key-normalization]]).

## 4. Lead-list output format (XLSX outreach worksheet vs CSV fallback)

The lead list ships as a real Excel `.xlsx` **outreach working sheet** when a spreadsheet library is
available, else as CSV with the identical 16-column schema. This detection is a **step parallel to
the storage-backend choice above**: probe whether `openpyxl` or `pandas` is importable, then branch:

- **(A) Emit `.xlsx`** — a spreadsheet library is present; write the leads workbook as an
  **outreach-ready working sheet**: action-first column order, frozen header + name column,
  autofilter, default sort by `fit_total`, color coding, hyperlinks, banded rows, plus the appended
  **"Outreach Tracking" columns** (`outreach_status` dropdown / `channel_used` dropdown /
  `contacted_on` / `next_follow_up` / `owner` / `notes`, with status-driven row colors) and a
  **"Summary" dashboard sheet** (research dashboard + **Outreach Funnel**). See output-assembly.md
  for the full layout.
- **(B) Emit CSV** — no library available; write the same 16 columns as CSV (no Outreach Tracking
  columns, no Summary sheet). This is a graceful downgrade, not a failure.

If no library is importable, CSV is chosen automatically. Like the storage choice, this is decided
once here and re-checked at assembly if the library has gone missing.

## 5. Record the choices

Propose the tooling status, storage choice, and lead-list output format as `memory/USER.md` and
`memory/PROJECT.md` update candidates (no auto-commit).
