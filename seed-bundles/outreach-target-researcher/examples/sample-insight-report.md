# Work Report — handmade-nailtip-makers (run 1)

_This sample is written in English for illustration. At runtime the deliverable language follows the
user's language — a Korean user gets a Korean report, and so on. Only the section headings and the
CSV column keys stay in stable English._

_Target: handmade nail-tip makers for a nail-art design/stencil tool. Illustrative example that pairs
with `sample-icp.yaml` and `sample-leads.csv`._

## 1. Executive Summary

- **Objective:** find solo / small-studio handmade nail-tip **makers** (producers, not wearers) who
  show active demand for a shape-consistency / stencil tool.
- **Result:** **3 qualified leads** shipped, from **web (Exa/Jina), Instagram, and Xiaohongshu**.
- **Headline insight:** the sharpest demand is a *shape-reproducibility* pain — makers can't reliably
  redo the same set — voiced across all three languages.
- **Recommendation:** approach the 3 now on the reproduce-the-exact-shape angle; then decide whether
  to **(A) relax the threshold** or **(B) expand the search** to grow the list past 3.

## 2. Objective & Scope

- **Target definition (identity axis):** solo / small-studio makers who *produce* handmade nail tips
  (穿戴甲 / 수제 네일팁), excluding wearers, resellers, and mass-brands.
- **Target definition (demand axis):** an evidenced signal of pain/desire around making tips —
  shape consistency, speed, hand-fatigue, design replication.
- **Channels searched:** web (Exa/Jina), Instagram, Xiaohongshu; X and Reddit attempted (see §4).
- **Filters:** language = ko / en / zh (soft; `unknown` bucketed, not excluded); region = none hard;
  recency window = 12 months.
- **Target count (ceiling):** 25. This is a **ceiling, not a floor** — a short qualified list is the
  intended outcome when the frontier is thin, not a shortfall to pad.
- **Run:** date 2026-07-15 · run-id `handmade-nailtip-makers/run-1`.

## 3. Method

- **Tools / channels:** web semantic search (Exa) + site entry (Jina); social discovery via
  Agent-Reach (Instagram, Xiaohongshu, X); Reddit via the user's session.
- **Dedup (net-new vs ledger):** every candidate's normalized key was checked against
  `ledger-keys.txt` and `do-not-contact.txt` **before** any extraction — the model never loaded the
  ledger body. 12 candidates were dropped as already-in-ledger; 0 hit the suppression list; the two
  seed accounts were excluded and their keys added.
- **Scoring rubric:** six transparent axes — identity match, intent strength, real-person trust,
  contactability, recency, filter conformance — **each scored 1-5, so `fit_total` ranges 6-30**. No
  black-box totals; the per-axis breakdown ships in the CSV `fit_breakdown` column.
- **Exclusions:** DNC / erasure list honored; private personal accounts excluded; non-producers
  (consumers buying press-ons, resellers/dropshippers) filtered by role.

## 4. Results at a Glance

**Candidates seen -> passed gate -> qualified:** 41 seen -> 29 passed dedup/suppression -> **3
qualified and shipped.** Most of the 29 that passed the gate were consumers or resellers, removed by
role — the list was **not** padded to hit the ceiling of 25.

**Fit-score distribution (of the 3 qualified, max 30):**

| Band | Count |
| --- | --- |
| 25-30 (strong) | 1 |
| 20-24 (solid) | 2 |
| < 20 | 0 |

**Per-channel status:**

| Channel | Status | Count | Detail |
| --- | --- | --- | --- |
| Web (Exa/Jina) | **success** | 1 | Domain-first gate skipped 6 known/marketplace domains before fetch. |
| Instagram | **success** | 1 | Hashtag + bio discovery. |
| Xiaohongshu | **partial** | 1 | Session dropped to `authentication required` mid-run; 1 gathered before stop; re-login branch offered. |
| Reddit | **unauthenticated** | 0 | Not logged in; user chose to exclude (**not** "0 results"). |
| X | **discovery-failed** | 0 | Agent-Reach fetch error — a tool failure, **not** evidence of "no leads." Retry next run. |

`discovery-failed` and `unauthenticated` are **not** "0 results" — the distinction is mandatory.

**Language distribution:**

| Language | Qualified leads | Notes |
| --- | --- | --- |
| ko | 1 | high confidence (0.99) |
| en | 1 | high confidence (0.96) |
| zh | 1 | high confidence (0.98) |
| unknown | 0 | short/code-mixed bios were bucketed during triage; none reached qualified this run |

Language is a **soft filter** — `unknown` leads are bucketed for user review, never auto-excluded.

**Intent-strength distribution:**

| Intent | Qualified leads |
| --- | --- |
| strong | 2 |
| medium | 1 |
| weak | 0 |

## 5. Key Findings (Segment Insights)

**Common expressions & hashtags** (for the user's later messaging — not written by this worker):

- Recurring pain phrasings: "can't get the same shape twice", "한 세트 만드는 데 손목이 너무 아파요",
  "每次想复刻之前的款式都做不出一样的".
- Productive hashtags: `#수제네일팁`, `#handmadenailtips`, `手工美甲片`, `穿戴甲 制作`.
- Consumer-leaning tags to keep excluding: `#pressonhaul`, `#nailswap`.

**Where they cluster & notable patterns:** producers concentrate on Instagram (ko) and Xiaohongshu
(zh) with WIP/process posts; the web channel surfaces the ones with an own-domain shop. The
shape-reproducibility pain recurs across all three languages — a cross-market signal, not a local one.

**Top leads (why they scored highest):**

1. **Mina (Tips by Mina)** — web, own-domain email, `confirmed`. **Fit 27/30**
   (`id:5 intent:5 human:5 contact:5 recency:4 filter:3`). Highest because every axis is strong: a
   clear producer identity, an explicit consistency pain, an own-domain email (top contactability),
   and a solo one-person brand — **treated as a true positive, the top fit, not filtered as "a
   brand."** **Angle:** reproduce-the-exact-shape stencil (her stated "redoing a set 3x" pain).
2. **jiwoo.nailtip** — Instagram, linktree, `probable`. **Fit 24/30**
   (`id:5 intent:5 human:4 contact:3 recency:5 filter:2`). Solo Korean maker, fresh hand-fatigue
   post; `probable` because identity rests on bio + content with no strong cross-domain anchor.
   **Angle:** speed / hand-fatigue benefit — approach in Korean.
3. **美甲片小工坊** — Xiaohongshu, DM handle only, `single`. **Fit 20/30**
   (`id:4 intent:4 human:4 contact:2 recency:3 filter:3`). Producer with a design-replication wish;
   contactability low (handle only, no public email). **Angle:** design-replication template benefit.

All three are **producers** (role-checked), not consumers or resellers, and each carries evidence on
**both** ICP axes plus provenance (source URL + capture timestamp).

## 6. Recommendations & Next Steps

- **Approach angles per segment:** reproduce-the-exact-shape stencil (web / en shop owners);
  speed & hand-fatigue relief (Instagram / ko solo makers); design-replication templates
  (Xiaohongshu / zh studios).
- **3 qualified vs target 25** — the frontier is thin on producers. Decide:
  **(A) relax the threshold** (accept `medium`-intent producers) or **(B) expand the search** (retry
  X, log in to Reddit, add Threads/TikTok fallback, add adjacent hashtags `#customnails`,
  `ネイルチップ 作り方`).
- **Frontier-exhaustion note:** producers are sparse relative to consumers on these channels this
  run; a third option is to **(C) expand the definition** to include small studios (2-4 makers), not
  only solo. Advancing the cursor and appending the 3 leads + their keys are proposed as **memory
  update candidates** (no auto-commit).

## 7. Appendix

- **Coverage caveats:** Reddit is `unauthenticated` and X is `discovery-failed` this run — **neither
  is "0 results."** The producer frontier was only partially explored (Xiaohongshu stopped early on
  auth). Absence of leads on a failed/unauthenticated channel is not evidence of absence.
- **Provenance & freshness:** every shipped lead carries a source URL + capture timestamp (ISO 8601)
  and a post/refresh date; the demand signals here are within the 12-month recency window.
- **Compliance:** **public business/creator contacts only** — no private personal accounts, no leaked
  or gated data. The DNC / erasure suppression list was honored (0 hits this run). This worker builds
  the list and never sends outreach; **the legality of any outreach the user sends is the user's
  responsibility** (see `docs/security-notes.md`). This is not legal advice.
- **Data:** the full 3-lead dataset with all 16 columns is in `examples/sample-leads.csv`.
