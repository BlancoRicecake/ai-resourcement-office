# Outreach Target Researcher bundle

Give it an **outreach target** and it standardizes it into an **ICP**, then discovers real, directly-reachable people who match —
finding creators and small businesses who both **are who you want** (identity) and **show they want
what you offer** (demand-intent), with **link + quote evidence** on every lead. It is not a scraper
that grabs everything; it is a researcher that finds people who will actually reply. It **builds the
list and derives an approach angle — it never sends outreach.**

## Quick Start

1. Open this folder in a tool-capable agent runtime (Claude Code, Codex, etc.). A pure no-tool chat
   is unsupported — this worker needs shell + filesystem + network (see **Requirements** below).
2. Let the runtime follow `AGENTS.md`'s load order: `worker/agent.md` -> `memory/` ->
   `worker/skills/`. (If manual, paste `worker/agent.md` into the system instruction.)
3. **First run:** the worker onboards you — checks tooling (`agent-reach doctor`), explains the
   login-wall channels (use a dedicated sub-account, never your main), and asks you to pick a
   storage backend: **(A) set up SQLite now** or **(B) start plain-text and migrate later**.
4. It runs **ICP Setup** — interviewing you to define the ICP (product -> identity + **role** -> demand signals ->
   seeds -> per-channel keywords -> language/region/scale/recency/target count), then discovers,
   dedups, extracts contacts, scores fit, and hands you two deliverables: the **lead list** (an
   **outreach-ready Excel `.xlsx` working sheet** when a spreadsheet library — openpyxl/pandas — is
   available, else **CSV** with the identical 16-column schema) and the **work report**, delivered
   as both Markdown (`.md`) and a self-contained, offline **HTML** (`.html`) view.

No required API keys. Web discovery uses Exa/Jina keyless tiers; social discovery uses Agent-Reach
against your own logged-in sessions.

## AI Worker

`Outreach Target Researcher` operates as a senior lead-discovery researcher.

- **Identity** — finds reachable people, not volume. Won't start before the two-axis ICP is settled,
  discards any lead without evidence, and treats the target count as a **ceiling, not a floor**.
- **Knowledge** — two-axis ICP, intent-signal grading, human-vs-solo-brand-vs-bot judgment,
  contact-channel trust, identity resolution, dedup-key normalization, language-detection
  confidence, six-axis fit scoring, channel tactics, approach-angle derivation, demand
  false-positives, seed generalization, cursor-frontier search, and slow/read-only defaults — a
  **14-node knowledge graph**.
- **Output** — a lead list (an **outreach-ready `.xlsx` working sheet** when a spreadsheet library is
  available — action-first columns, frozen header + name column, autofilter, `fit_total`-sorted,
  color-coded, hyperlinked, with an appended "Outreach Tracking" block (`outreach_status` /
  `channel_used` / `contacted_on` / `next_follow_up` / `owner` / `notes`, status-driven row colors)
  and a Summary dashboard sheet with an Outreach Funnel — **else CSV with the same 16-column
  schema**: provenance URL + capture
  timestamp, contact-type, six-axis fit breakdown, detected language, identity-cluster-id,
  resolution) + a work report — delivered as both **Markdown (`.md`)** and a **self-contained,
  offline HTML (`.html`)** view (language distribution, expressions, hashtags, channel status,
  recommended approach angle per lead).

## Storage backend & migration

The per-target ledger is **plain-text by default** — human-readable, no DB to initialize, simple:

```
memory/targets/<slug>/
  icp.yaml         confirmed ICP
  leads-ledger.jsonl   append-only lead records (one JSON per line)
  ledger-keys.txt      normalized dedup keys (one per line)
  state.yaml           frontier cursor
  do-not-contact.txt   DNC / erasure suppression list
  learnings.md  runs/
```

**SQLite is an optional performance backend inside the same shell** — not a separate server, just a
single file via the `sqlite3` binary or Python's built-in `sqlite3` (free, serverless). Onboarding
asks whether to set it up now or start plain-text and migrate later. To migrate later:

1. Create the DB: a `leads` table (mirroring the jsonl fields) and a `keys` table (one row per
   normalized key, `UNIQUE`).
2. Import: stream `leads-ledger.jsonl` into `leads`, and `ledger-keys.txt` into `keys`.
3. Switch the dedup gate to `SELECT 1 FROM keys WHERE key = ?`; keep the jsonl as a human-readable
   mirror if you like. The plain-text files remain the source of truth unless you decide otherwise.

Either way the model never loads the ledger body — it compares normalized keys via the host tool.

## Requirements

A tool-capable agent runtime with **shell/code execution + filesystem + network** is required.
Agent-Reach (CLI), Exa/Jina web fetch, and the on-disk ledger all assume a shell. A pure no-tool
LLM chat is an **unsupported runtime**.

## Structure tree

```txt
outreach-target-researcher/
  AGENTS.md                 folder entry point (runtime requirement, load order, tool wiring, scope)
  README.md  bundle.json  .env.example  LICENSE
  worker/
    agent.md                identity + [H1-H14] + workflow + S1-S10 + absolute rules + learning loop
    agent.json              machine-readable meta
    skills/                 icp-setup, onboarding-setup, auth-preflight, dedup-gate,
                            contact-extraction, qualification-scoring, output-assembly,
                            erasure-handling
  memory/                   learning loop (reloaded next session)
    MEMORY.md USER.md PROJECT.md DECISIONS.md RUNS.md RESEARCH.md
    knowledge/              14 nodes + INDEX.md (engine-less graph)
  docs/                     security-notes · limitations · cost-guide
  examples/                 nail-art tool -> handmade nail-tip makers (profile, leads CSV, report .md + .html)
```

## Safety & limits

- Discovers **public business/creator contacts only**; excludes private personal accounts, leaked
  data, and robots.txt / ToS-forbidden sources.
- **Never sends outreach, never stores passwords, read-only and slow by default** (a ban means the
  permanent loss of a channel).
- Requires **provenance (source URL + capture timestamp)** on every lead and checks a **DNC /
  erasure suppression list**.
- The legality of any outreach **you** send is **your responsibility**; this is not legal advice.
  See `docs/security-notes.md` for GDPR / Korea PIPA / Network Act / CAN-SPAM / CASL summaries.
