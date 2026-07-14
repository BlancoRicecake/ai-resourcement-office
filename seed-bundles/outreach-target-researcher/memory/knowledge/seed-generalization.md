---
id: seed-generalization
title: Seed generalization
tags:
  - seed
  - attributes
  - generalization
source: seed
confidence: high
created: 2026-07-15
---
A seed account/page is a **template to generalize from**, not a lead to output. **[H12]**

The user gives one or more "perfect example" targets (seeds). The tactic:

1. **Extract attributes** — what makes this seed a match? (role = solo nail-tip maker; posts
   work-in-progress; own domain shop; uses hashtags `#수제네일팁` / `#handmadenailtips`; laments a
   specific filing pain; small/individual scale.)
2. **Generalize** — turn those attributes into search dimensions: the hashtags to search, the
   demand-signal phrasings to look for, the identity role to require, the scale filter.
3. **Search for the attributes**, not the seed. Find *other* people who share the generalized profile.
4. **Exclude the seed itself** from the output — the user already knows it. Add the seed's keys to the
   ledger so the dedup gate ([[dedup-key-normalization]]) won't re-surface it.

This links the ICP to concrete queries: the extracted attributes populate the identity axis of
[[two-axis-icp]] and the per-channel tactics of [[channel-tactics]]. Beware over-fitting to one seed —
if the user gives several seeds, generalize across their *common* attributes, and confirm the drafted
keywords with the user (icp-setup T5) before searching so the generalization matches intent.
