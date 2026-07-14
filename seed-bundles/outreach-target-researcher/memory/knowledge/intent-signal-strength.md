---
id: intent-signal-strength
title: Intent-signal strength & recency decay
tags:
  - intent
  - grading
  - demand
source: seed
confidence: medium
created: 2026-07-15
---
The demand-intent axis is **graded, not binary**, and decays with age. **[H2]**

Grade each demand signal:

- **Strong** — active, explicit demand tied to our offer. "I need a better stencil for filing nail
  tips — the ones I have keep slipping." A direct tool search, an explicit complaint about the exact
  problem we solve, a "does anyone make X?" post.
- **Medium** — latent or adjacent demand. Posts about the workflow/pain around our category without
  explicitly asking for our solution. Regular producing activity that implies the need.
- **Weak** — surface interest only. A like, a follow, a one-word mention, or generic category
  presence without a pain/desire signal.

**Recency decay:** a strong signal from two years ago is weaker today than a medium signal from last
week. Weight by the post/refresh date ([[contact-channel-trust]] records freshness). Decay does not
zero a signal, it discounts it — a still-relevant evergreen pain can hold value.

Guard against **false positives**: a keyword can look like demand while the role is wrong (a consumer
shopping, not a producer sourcing). Always cross-check role with [[demand-false-positive]]. The grade
here becomes the "intent" component in [[fit-scoring-rubric]], and it feeds the derived
[[approach-angle-derivation]] — the angle is built *from the quoted signal*, so a stronger, fresher,
more specific signal yields a sharper angle.

`confidence: medium` — the strong/medium/weak tiering is practitioner canon (see RESEARCH.md), useful
but not a measured law; hedge when a signal is ambiguous rather than over-claiming intent.
