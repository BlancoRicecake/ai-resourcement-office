---
name: icp-setup
description: Use at the start of a discovery job to define the ICP (ICP Setup). Covers the T1-T6 interview (product, identity + producer-vs-consumer role, demand signals, seeds, per-channel keywords, filters + target count) and the YAML output. Discovery must not start before this is settled.
---

# ICP Setup

Discovery starts from a **target**, not from a search box. Without the two-axis ICP (identity +
demand-intent) settled, any list is just noise. Do not start discovery before this profile is
confirmed. **Conduct the interview in the user's language** (mirror what they write), even though
this document is English.

## If an ICP already exists

If `memory/targets/<slug>/icp.yaml` exists, **render it back as Q&A** ("here is your current
target — product X, identity Y, role = producer, demand signals Z, filters…") and ask **"anything
to change?"** first. Never silently reuse a stale profile.

## T1-T6 interview

| Step | Question | Why it matters |
| --- | --- | --- |
| **T1 Product** | What do you offer, in one sentence? Who is it for? | Everything downstream ("does this lead need it?") is judged against this. |
| **T2 Identity + ROLE** | Who exactly is the target person? And crucially — are they the **producer/maker** or the **consumer**? What signal tells producer from consumer? | The single most common failure is pulling consumers. The role signal is **required**, not optional. See [[demand-false-positive]]. |
| **T3 Demand signals** | What would a real lead *say or do* that shows they want/need this? (complaints, wishes, tool searches, workflow posts) | These become the demand-intent axis and the intent-strength grade. See [[intent-signal-strength]]. |
| **T4 Seeds** | Any example accounts/pages that are perfect targets? | Seeds are for **attribute extraction**, then excluded from output. See [[seed-generalization]]. |
| **T5 Per-channel keywords** | For each channel, which keywords / hashtags / exclusion terms? (Draft, then confirm.) | Different channels need different query shapes. Draft them, read back, confirm. See [[channel-tactics]]. |
| **T6 Filters + count** | Language(s), region, scale (solo/small/large), recency window, and target count? | Filters are soft signals (language `unknown` is not excluded). **Target count is a ceiling, not a floor.** See [[language-detection-confidence]]. |

## Rules

- **T2 role signal is mandatory.** If the user cannot articulate producer-vs-consumer, keep probing
  with concrete examples ("a person posting *'where do you buy blank nail tips wholesale?'* is a
  producer sourcing supplies; a person posting *'where can I buy cute press-ons?'* is a consumer").
- **Both ICP axes must be defined** — identity *and* demand-intent. A one-axis target yields weak
  leads (see [[two-axis-icp]]).
- Draft T5 keywords per channel, read them back, and only proceed on confirmation. For multilingual
  targets, keep each language's terms in its own script (e.g. ko / en / zh).
- Restate the target count as a ceiling: "I'll aim for up to N qualified leads; if fewer qualify,
  I'll hand over the qualified ones and ask whether to relax the threshold or expand."
- Output an **ICP YAML** and propose it as the `icp.yaml` candidate for
  `memory/targets/<slug>/` (no auto-commit). See `examples/sample-icp.yaml` for the shape.
