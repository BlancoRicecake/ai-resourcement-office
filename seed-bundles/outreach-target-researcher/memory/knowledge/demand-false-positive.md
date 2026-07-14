---
id: demand-false-positive
title: Demand false-positive & role confusion
tags:
  - role
  - producer
  - consumer
source: seed
confidence: medium
created: 2026-07-15
---
The most common discovery failure is pulling **consumers when the target is producers** (or vice
versa). A surface keyword match is not a role match. **[H11]**

Our target (for the worked scenario) is the **producer** — the person who *makes* nail tips — not the
**consumer** who *buys* press-ons. Both use the words "nail tips," so a naive keyword search mixes
them.

Role signals (illustrative):

- **Producer / maker (target):** "where do you buy **blank** tips **wholesale**?", posts of
  work-in-progress, sells finished sets, talks about tools/supplies/process, has a shop.
- **Consumer (not target):** "where can I **buy** cute press-ons?", asks for recommendations to wear,
  reviews products they purchased, no production activity.
- **Reseller / dropshipper (excluded):** lists many SKUs with no making, generic catalog, no craft —
  penalized like a mass-brand ([[human-vs-solo-brand-vs-bot]]).

Discipline:

- Make the **producer-vs-consumer signal a required part of ICP Setup** (T2) and record an
  explicit **role judgment** per lead, with the signal that decided it — this drives success criterion
  **S5** (role accuracy below the misclassification threshold).
- Treat a keyword-only match as a *candidate*, not a lead, until the role is verified.
- Wrong role = false positive = discard, even if the fit "looks" high on other axes; the identity
  axis of [[two-axis-icp]] is not satisfied by a mismatched role.

When the role is genuinely ambiguous, mark it and lower the identity-match score rather than assuming
the favorable role.

`confidence: medium` — the producer-vs-consumer role split is practitioner canon (see RESEARCH.md), a
reliable heuristic rather than a measured law; when the role signal is thin, mark it ambiguous rather
than forcing a class.
