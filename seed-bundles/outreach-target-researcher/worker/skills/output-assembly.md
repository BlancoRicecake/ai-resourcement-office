---
name: output-assembly
description: Use to assemble the final deliverables. Defines the exact leads CSV schema and the insight report (language distribution, expressions, hashtags, channel status success/partial/failed/unauthenticated, approach angles).
---

# Output assembly

Two deliverables: the **leads CSV** (exact schema below) and the **insight report**. Run the
S1-S10 self-check first; if any criterion fails, return to the relevant workflow step before
assembling.

**Deliverable language.** These deliverables have no fixed language — write them in the **user's
language** (mirror the interaction language). Only the CSV **column keys** below stay as the
stable English schema keys; the **values** (report prose, angles, evidence framing) follow the
user's language. Discovered snippets are quoted in their original language. Do **not** hardcode
English for the output.

## Lead-list file format — XLSX primary (outreach worksheet), CSV fallback

The lead list is emitted as a real Excel `.xlsx` **when a spreadsheet library (openpyxl or pandas)
is importable**, and falls back to **CSV with the identical 16-column schema** otherwise. This
mirrors the SQLite tiering: the format is chosen **once at onboarding** (detection step parallel to
the storage-backend choice, see onboarding-setup.md) and re-checked at assembly if the library has
gone missing. The **16-column schema below is canonical for both formats** — column keys stay
English; cell values and report prose follow the user's language.

The `.xlsx` is not a data dump. The user runs **real marketing outreach off this file**, so the
workbook is built as a **ready-to-use working sheet** — prioritize visibility and usability.

### Sheet "Leads" — the outreach working sheet

The sheet is split into **two labeled column blocks**, separated by a visual divider / column-group
label so it reads as two zones at a glance:

- **"Lead Research"** — worker-generated: the 16 data columns below, in action-first order.
- **"Outreach Tracking"** — blank, user-filled: the outreach columns appended to the right.

- **Action-first display order.** The underlying data set is still the 16 columns below; only the
  **display order** changes so the columns a person needs to act are on the left:

  ```
  name_or_handle | source | detected_language | contact_type | contact_value |
  intent_strength | fit_total | approach_angle
  ```

  then, to the right: `identity_evidence` · `demand_evidence` · `posted_or_updated` ·
  `provenance_captured_at` · `resolution` · `identity_cluster_id` · `fit_breakdown`.

- **Freeze & filter.** **Freeze the header row AND the `name_or_handle` column** (freeze panes at
  B2) so the name and headers stay visible while scrolling. Put an **autofilter** on the header row.
  **Default-sort rows by `fit_total` descending, then `intent_strength`** (strong > medium > weak).

- **Color coding for scanability.**
  - `fit_total` — a **color scale or data bars** across the column (higher = stronger fill).
  - `intent_strength` — **strong = green, medium = amber, weak = grey**.
  - `resolution` — distinct fills for `confirmed` / `probable` / `single`.
  - `contact_type` — distinct fills for `email` / `handle` / `form` / `linktree`.

- **Hyperlinks.** Make `profile_or_site_url`, the links inside `identity_evidence` /
  `demand_evidence`, and any linktree in `contact_value` **clickable hyperlinks**.

- **Readability.** **Wrap** the long fields (`identity_evidence`, `demand_evidence`,
  `approach_angle`) with a **capped row height**; **band the rows** (alternating shading); tune
  column widths per field; make the header **bold with a fill color**.

- **★ Outreach Tracking layer (xlsx only).** Append **after** the 16 data columns, as the labeled
  **"Outreach Tracking"** block, six **blank** columns for the user to fill while working the list:
  - `outreach_status` — a **data-validation dropdown** for the pipeline: `new` / `contacted` /
    `follow-up` / `replied` / `meeting` / `won` / `lost` / `skip`. Every row starts at `new`.
  - `channel_used` — a **data-validation dropdown**: `email` / `DM` / `form` / `other`.
  - `contacted_on` — a **date** cell.
  - `next_follow_up` — a **date** cell.
  - `owner` — free text (who is handling the lead).
  - `notes` — free text (outcome / details).

  These exist **only in the `.xlsx`**. The **CSV stays 16 columns** — parity of the data schema is
  preserved.

- **Status-driven conditional formatting.** Color the row (or the `outreach_status` cell) by
  `outreach_status` so the pipeline is visible at a glance: **won = green, replied = teal,
  meeting = blue, contacted = light-blue, follow-up = amber, lost / skip = grey + strikethrough,
  new = default (no fill).**

### Sheet "Summary" — dashboard

A one-glance dashboard that ties to the work report **§4 Results at a Glance**: per-channel status
(success / partial / failed / unauthenticated) with counts, language distribution (incl. the
`unknown` bucket), intent-strength distribution, and fit-band counts.

- **★ Outreach Funnel.** Add a funnel block: **counts by `outreach_status`** (`new` / `contacted` /
  `follow-up` / `replied` / `meeting` / `won` / `lost` / `skip`) — all rows are `new` at generation
  and the counts fill in as the user works the list. Include a small **legend** explaining the
  status pipeline and the row colors (won = green, replied = teal, meeting = blue,
  contacted = light-blue, follow-up = amber, lost / skip = grey + strikethrough, new = default) so a
  marketer can pick the sheet up immediately. Keep the existing research dashboard (per-channel
  status, language, intent, fit bands) alongside it.

### CSV fallback

If no spreadsheet library is importable, emit **CSV** with the same 16 columns in the same order (no
Outreach Tracking columns, no Summary sheet / Outreach Funnel) — a graceful downgrade, not a failure (see
docs/limitations.md). In both formats the **column keys stay English**; **values and report prose
follow the user's language.**

## Leads CSV — required columns (exact)

One row per lead, in this column order:

1. `name_or_handle` — display name and/or handle.
2. `source` — the discovery channel: `web` / `x` / `instagram` / `reddit` / `linkedin` /
   `xiaohongshu` / `threads` / `tiktok` / …
3. `profile_or_site_url` — the profile or site URL.
4. `contact_type` — `email` / `handle` / `form` / `linktree` (never blank — **S4**).
5. `contact_value` — the contact itself (mark personal free-mail as a personal channel).
6. `identity_evidence` — identity-axis proof: **link + quoted snippet**.
7. `demand_evidence` — demand-intent-axis proof: **link + quoted snippet**.
8. `intent_strength` — `strong` / `medium` / `weak`.
9. `posted_or_updated` — post/refresh date (freshness).
10. `detected_language` — language + confidence, or `unknown` (+confidence).
11. `fit_total` — the composed total score.
12. `fit_breakdown` — the six axes, e.g. `id:4 intent:5 human:4 contact:3 recency:4 filter:5`.
13. `identity_cluster_id` — the resolution cluster id.
14. `resolution` — `confirmed` / `probable` / `single`.
15. `provenance_captured_at` — source URL + capture timestamp (ISO 8601) — **required on every row**.
16. `approach_angle` — the derived angle (not outreach copy).

Both `identity_evidence` and `demand_evidence` must be present and non-hallucinated (**S1, S2**). A
lead missing either axis is not shipped.

## Insight report — a formal WORK REPORT

The insight report is a **formal business work report** alongside the CSV, not a loose note. It uses
the **seven sections below** (English section headings are stable anchors; the prose inside each
follows the user's language). Keep the runtime-language caveat at the very top of the report.

**The work report is emitted as BOTH formats, always both:** a portable **`.md`** (diffable, pastes
anywhere) **and** a self-contained **`.html`** (comfortable, visual viewing). There is no dependency
that gates this — the `.html` is a plain-text file the worker writes, so it is **always produced
alongside the `.md`**, never optional. Same seven sections, same numbers, two renderings.

1. **Executive Summary** — the objective in one line, **N qualified leads**, which channels produced
   them, the single headline insight, and a one-line recommendation.
2. **Objective & Scope** — the target definition (**identity + demand axes**), channels searched,
   filters applied (language / region / recency), the target count (a **ceiling**), and the run date /
   run-id.
3. **Method** — tools/channels used, dedup applied (net-new vs ledger), the **six-axis scoring
   rubric** ([[fit-scoring-rubric]], each axis 1-5, `fit_total` 6-30), and exclusions (DNC, private
   accounts, non-producers).
4. **Results at a Glance** — a table with: qualified count, fit-score distribution, **per-channel
   status** (success / partial / failed / unauthenticated) with counts, language distribution (incl.
   the `unknown` bucket, [[language-detection-confidence]]), and intent-strength distribution.
5. **Key Findings (Segment Insights)** — the segment's common expressions / hashtags, where they
   cluster, notable patterns, and the **top leads highlighted with why they scored highest** (keep
   the solo/individual-brand-as-top-fit case — a one-person brand is a true positive, not "a brand").
6. **Recommendations & Next Steps** — approach angles per segment; the **"N qualified vs target M ->
   (A) relax threshold (B) expand search"** decision; and a frontier-exhaustion note if any.
7. **Appendix** — coverage caveats (**0-results vs discovery-failed**, see docs/limitations.md),
   provenance & freshness note, compliance note (**public business contacts only; the legality of any
   outreach is the user's responsibility; DNC honored**), and a reference to the leads CSV.

**Channel status vocabulary** (used in section 4): **success** (ran, found leads), **partial** (ran,
interrupted — e.g. auth dropped mid-run), **failed** (`discovery-failed`: tool/fetch error or missing
tool, *not* "no matches"), **unauthenticated** (skipped, not logged in). Distinguishing `failed` from
`0 results` is mandatory (see docs/limitations.md).

### HTML report — layout & rules

The `.html` renders the **same seven sections** with visibility the Markdown can't carry (metric
tiles, colored badges, CSS bars, lead cards). Hard rules:

- **Single self-contained file.** All styling in one **inline `<style>`** block; **no external
  resources** — no CDN, no external stylesheet, no web fonts, no remote images, no server, **no JS**.
  It must open **offline** by double-clicking in any browser. Use the OS font stack
  (`system-ui, -apple-system, Segoe UI, Roboto, sans-serif`) and CSS-only visuals so nothing is
  fetched and nothing can break.
- **Runtime-language caveat at the top**, mirroring the `.md`: English is only the section headings /
  CSV keys; the content language follows the user.
- **Section mapping (visualized):**
  - **§1 Executive Summary → metric tiles.** A top row of tiles for the headline numbers: **N
    qualified**, channels that produced them, and the one-line headline insight.
  - **§4 Results at a Glance → color-coded status badges + tables.** Per-channel status as badges:
    **success = green, partial = amber, failed = red, unauthenticated = grey**. Keep the fit /
    language / intent tables.
  - **fit-score / language / intent distributions → CSS bar visualizations.** Pure-CSS horizontal
    bars (a filled `<div>` sized by percentage width) — **no JS, no chart library**.
  - **§5 top leads → cards.** One card per top lead: a **fit badge**, the **contact type**, the
    **approach angle**, and **clickable links** (profile/site, evidence) as real `<a href>`.
  - **§7 compliance / appendix → a muted footer.** De-emphasized (smaller, low-contrast) footer for
    provenance, freshness, and the compliance / DNC / "outreach legality is the user's
    responsibility" note.
- **Print-friendly, light theme by default;** an **optional `@media (prefers-color-scheme: dark)`**
  may add a dark variant. Colors must keep the badge semantics readable in both. Avoid fixed heights
  that clip on print; let content flow.

See `examples/sample-insight-report.html` for the worked, self-contained HTML rendering.

See `examples/sample-leads.csv` and `examples/sample-insight-report.md` for the worked shape.

## After assembly

Propose ledger append, cursor advance ([[cursor-frontier-search]]), and any generalizable learning
as **memory update candidates** — never auto-commit.
