# Limitations

- **Not a hosting service.** You run this in your own agent runtime, with your own model, budget, and
  logged-in sessions. All costs are yours.
- **Requires a tool-capable runtime.** Shell/code execution + filesystem + network are mandatory.
  A pure no-tool LLM chat is **unsupported** — Agent-Reach (CLI), web fetch, and the ledger all need
  a shell. If a required tool is missing, the affected channel degrades to a clearly-labeled fallback,
  never to fabrication.
- **Simulation is never the worker's fallback.** If the discovery tools (Agent-Reach / Exa / web
  fetch) are unavailable or unwired in an otherwise tool-capable host, the worker reports the affected
  channel as **`discovery-failed`** and guides you to install/authenticate it — it **never fabricates
  or simulates leads** to fill the gap. Simulation is only ever an **explicit test/demo mode you
  request**, labeled as such in the output — never the worker's own degrade path.
- **Judgment quality depends on the host model.** Role classification, identity resolution, and fit
  scoring are the host model's reasoning. A weaker model yields weaker evidence and more
  misclassification.
- **No spreadsheet library → CSV fallback.** The leads list ships as a real Excel `.xlsx` **outreach
  working sheet** (frozen panes, autofilter, color coding, hyperlinks, an appended "Outreach
  Tracking" block — `outreach_status` / `channel_used` / `contacted_on` / `next_follow_up` / `owner`
  / `notes` with status-driven row colors — and a Summary sheet with an Outreach Funnel) when
  `openpyxl` or `pandas` is importable; without either, the worker emits **CSV with the identical
  16-column schema**. This is a graceful downgrade, not a failure — the same data, a plainer format
  (no Outreach Tracking layer or Summary sheet).

## Per-channel ban-risk grade & realistic throughput

Discovery is **slow and read-only** on purpose (a ban = permanent loss of a channel). The numbers
below are **conservative defaults** — start lower, watch for ban signals, and stop on the first one.
They are guidance, not guarantees; each platform changes its limits without notice.

| Channel | Ban-risk grade | Conservative pacing (default) | Realistic throughput |
| --- | --- | --- | --- |
| Web (Exa/Jina) | Low | 1 req / 2-5s; respect robots.txt | Tens of pages/hour after gate |
| X | Medium | 1 action / 5-10s; ~a few hundred reads/day | Dozens of qualified/hour |
| Reddit | Low-Medium | 1 req / 2-4s; obey API limits | Dozens/hour |
| LinkedIn | **High** | Very slow; small daily cap; sub-account only | Single digits-low dozens/hour |
| Instagram | **High** | Very slow; sub-account; avoid bursts | Low dozens/hour |
| Xiaohongshu (小红书) | **High** | Very slow; sub-account; region-sensitive | Low dozens/hour |
| Threads / TikTok | Medium-High (fallback) | Best-effort via insane-search | Variable, often partial |

On any ban signal (challenge, 429/403, empty-feed, `authentication required`): **stop that channel,
notify, report `partial`.** Never retry aggressively.

## "0 results" vs "discovery-failed" (mandatory distinction)

These are **not** the same and must never be conflated in the report:

- **0 results** — the channel ran successfully and genuinely found no matching leads. A real finding.
- **discovery-failed** — a tool/fetch error, a missing tool, or a blocked channel prevented discovery.
  **Not** evidence of "no leads," just that we couldn't look.
- **unauthenticated** — the channel was skipped because it wasn't logged in.
- **partial** — the channel ran but was interrupted (e.g. auth dropped mid-run).

The insight report labels every channel with one of these. Treating a failure as "0 results" would
falsely tell the user the well is dry.

## Scope limits

- **No sending / no campaigns / no outreach copy** — handed off (growth-marketer, web-copy-analyzer).
- **No private, gated, or leaked data.** Public business/creator contacts only.
- **No CRM entry, deliverability/warm-up, or paid-list purchase.**
- **Best-effort coverage.** Channels change constantly; some (Threads/TikTok) are fallback-only in
  v1. Frontier exhaustion is surfaced, not hidden — the worker proposes expanding the definition
  rather than padding the list.
- **Quality-first ceiling.** The requested count is a ceiling; a short, qualified list is the intended
  outcome when the frontier is thin, not a bug.

## Responsibility

Final decisions on who to contact and how — and the legality of any outreach — are the user's
(see `docs/security-notes.md`).
