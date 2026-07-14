# Cost Guide

This bundle has **no required API keys**, but "no key" is not "no cost." Two cost sources: **host
model tokens** (all judgment) and **network time** (slow, read-only discovery). Plan around both.

## Where cost comes from

- **Host model tokens** — every judgment (role classification, identity resolution, fit scoring,
  approach angle, report writing) is host-model reasoning. Cost scales with the number of candidates
  examined, channels, and report length. The knowledge graph is read INDEX-first (open only relevant
  nodes), which keeps context small; the ledger body is **never** loaded (keys only).
- **Network / time** — discovery is deliberately slow ([[slow-readonly-default]]). Throughput is
  capped by conservative pacing, not by money, so a run's real "cost" is often **wall-clock time**.

## Exa / Jina usage

- **Exa** (semantic web search) and **Jina Reader** (URL-to-text extraction) offer **keyless tiers**
  that work for modest volumes. Optional keys raise rate limits / quality (see `.env.example`).
- Cost/limits scale with **pages fetched**. The **two-stage web gate** saves the most money here: the
  **domain key is checked before site entry**, so known/suppressed domains are skipped with **zero
  fetch**. Only novel domains are entered and extracted.
- Long pages cost more to read; Jina returns cleaned text, and you can cap how much is pulled into
  context.

## Agent-Reach usage

- Runs against **your own logged-in sessions** — no per-call API fee, but strict **rate/ban limits**.
  The binding constraint is pacing, not price. Budget **time**, use a dedicated sub-account, and stop
  on ban signals.

## Per-channel hourly throughput (rough, conservative)

| Channel | Qualified leads / hour (rough) | Dominant cost |
| --- | --- | --- |
| Web (Exa/Jina) | Tens (after gate) | Fetch volume + tokens |
| X / Reddit | Dozens | Pacing + tokens |
| LinkedIn / Instagram / Xiaohongshu | Single digits-low dozens | **Pacing (ban risk)** |
| Threads / TikTok (fallback) | Variable / partial | Tool availability |

Numbers assume the conservative pacing in `docs/limitations.md`. Faster is not better here — it is a
ban.

## Expected time for a typical run

A focused run (one target, 2-3 channels, a few dozen qualified leads) is usually a **matter of hours**
of slow discovery, plus token cost proportional to candidates and report length — not minutes, by
design. The frontier cursor ([[cursor-frontier-search]]) lets you resume across sessions instead of
front-loading one long, risky burst.

## How to spend less

1. **Narrow the target** (tighter identity + role + keywords) so fewer junk candidates are examined.
2. **Lean on the domain-first web gate** — it skips known domains before any fetch.
3. **Fewer channels, deeper** — pick the 1-2 channels where the target actually lives
   ([[channel-tactics]]).
4. **Open only relevant knowledge nodes** (INDEX-first), and let the ledger stay on disk (keys only).
5. **Resume with the cursor** across sessions instead of one long run.
