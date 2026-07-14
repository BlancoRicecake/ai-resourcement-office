---
id: fit-scoring-rubric
title: Six-axis fit scoring rubric
tags:
  - scoring
  - transparency
  - qualification
source: seed
confidence: medium
created: 2026-07-15
---
Fit is scored on **six transparent axes** and the total is their (weighted) sum — **never a
black-box number**. **[H8]** This is success criterion **S7**.

The six axes:

1. **Identity match** — fit to the identity axis (right kind of producer/maker). [[two-axis-icp]]
2. **Intent strength** — the graded, recency-decayed demand signal. [[intent-signal-strength]]
3. **Real-person trust** — personhood + reachability; solo brand = plus, bot/mass/reseller/MLM/spam =
   penalty. [[human-vs-solo-brand-vs-bot]]
4. **Contactability** — trust of the extracted contact (own-domain email > bio > form > handle).
   [[contact-channel-trust]]
5. **Recency** — freshness of the demand signal / activity.
6. **Filter conformance** — match to language / region / scale / recency filters (soft — language
   `unknown` is not a fail). [[language-detection-confidence]]

Record each component in the CSV `fit_breakdown` column, e.g. `id:4 intent:5 human:4 contact:3
recency:4 filter:5`. **Scale: each of the six axes is scored 1-5, so the composed `fit_total` ranges
6-30 (max 30)** — the sample breakdown above is the shape (`id:4 intent:5 …`). Put the composed total
in `fit_total`. Default weights are
equal; a target may re-weight in `icp.yaml` (e.g. weight contactability higher for an email
campaign). Always show the components so the user can see *why* a lead scored as it did and re-rank if
they weight differently.

**Quality-first ceiling:** the requested count is a **ceiling, not a floor**. If too few leads clear
the threshold, hand over the qualified few and ask the user to **(A) relax the threshold** or
**(B) expand the search** — never pad with low-fit leads. Also carry an explicit producer-vs-consumer
role judgment ([[demand-false-positive]]) and an identity `resolution` ([[identity-resolution]]) with
each scored lead.

`confidence: medium` — the six-axis rubric is a bundle-authored synthesis over practitioner
intent-tiering (BANT, see RESEARCH.md), a transparent scoring convention rather than a measured law;
the axes, the 1-5 scale, and the weights are defaults to adapt, not calibrated constants.
