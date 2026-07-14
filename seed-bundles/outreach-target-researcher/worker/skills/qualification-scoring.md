---
name: qualification-scoring
description: Use to qualify and score a lead after contact extraction. Covers the six-axis fit breakdown, the role-confidence component, identity resolution, language honesty, and the quality-first ceiling rule (hand over qualified few + ask relax/expand).
---

# Qualification & scoring

Turn a passing, contacted candidate into a scored lead. Every score is **decomposed into six
transparent axes** — no black-box totals. This is **S7 (fit is decomposable)**.

## Six-axis fit breakdown ([[fit-scoring-rubric]])

Score each axis, then compose the total (weights configurable in `icp.yaml`, default equal):

1. **Identity match** — how well the person fits the identity axis (producer/maker of the right
   kind). [[two-axis-icp]]
2. **Intent strength** — the graded, recency-decayed demand signal (strong/medium/weak).
   [[intent-signal-strength]]
3. **Real-person trust** — personhood + direct reachability. Solo/individual brand = plus; bot /
   mass-brand / reseller / MLM / spam = heavy penalty. [[human-vs-solo-brand-vs-bot]]
4. **Contactability** — trust level of the extracted contact (own-domain email > bio > form >
   handle). [[contact-channel-trust]]
5. **Recency** — freshness of the demand signal / profile activity.
6. **Filter conformance** — match to the language/region/scale/recency filters (soft — see below).

Expose the component scores in the CSV `fit_breakdown` column (e.g. `id:4 intent:5 human:4 contact:3
recency:4 filter:5`). **Scale: each of the six axes is scored 1-5, so `fit_total` ranges 6-30
(max 30)** — matching the sample breakdown shape above. The total is their (weighted) sum.

## Role confidence ([[demand-false-positive]])

Include an explicit **producer-vs-consumer** judgment. Our target is the **producer**. A surface
keyword match that is actually a consumer is a false positive — record the role and the signal that
decided it. This drives **S5 (role accuracy)**.

## Identity resolution ([[identity-resolution]])

- Assign an `identity_cluster_id` grouping accounts that are the same person.
- `resolution` = `confirmed` only with a **strong anchor** (matching handle + domain + name);
  `probable` for circumstantial links; `single` when there is just one account. This is **S9 (safe
  merge)** — never merge on weak evidence.

## Language honesty ([[language-detection-confidence]])

- Detect the lead's language across fields + script hints; report a **confidence**.
- Short or code-mixed text -> `unknown` with confidence, **never a forced guess**. `unknown` goes to
  a separate bucket and is **never auto-excluded** (language is a soft filter). This is **S8**.

## Quality-first ceiling rule

The target count is a **ceiling, not a floor**. If fewer leads clear the threshold than requested:

- **Do not pad** with low-fit or unevidenced leads.
- Hand over the qualified few, then ask the user: **(A) relax the fit threshold** or **(B) expand the
  search** (more channels, broader keywords, wider recency). Let the user decide.

## Approach angle ([[approach-angle-derivation]])

For each qualified lead, derive a **recommended approach angle from their own quoted demand signal**
(e.g. "she posted about hand-cramping when filing tips -> lead with the ergonomic-stencil benefit").
Surface the angle only — **do not write the outreach message.**
