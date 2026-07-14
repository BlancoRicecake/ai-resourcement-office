---
id: language-detection-confidence
title: Language-detection confidence
tags:
  - language
  - honesty
  - soft-filter
source: seed
confidence: medium
created: 2026-07-15
---
Report the lead's language **with a confidence**, and treat language as a **soft signal**. **[H7]**

- Detect across **multiple fields** (bio + posts + captions) and use **script hints** (Hangul,
  Hanzi/Kanji, Latin, Cyrillic) as corroboration. More text = higher confidence.
- **Short or code-mixed text -> `unknown`** with a stated confidence, never a forced guess. A
  two-word bio or an emoji-heavy caption does not license a confident language label; language ID is
  known to degrade on short strings (RESEARCH.md).
- **Soft filter:** language **never auto-excludes** a lead. `unknown` goes to a **separate bucket** in
  the insight report, surfaced for the user to decide, not silently dropped. A great-fit maker whose
  language is unclear is still a lead.

This is success criterion **S8** (language honesty). The label feeds the "filter conformance" axis of
[[fit-scoring-rubric]] as a soft input, and the language distribution (including the `unknown` bucket)
is a required section of the insight report ([[approach-angle-derivation]] may note that an approach
angle should be written in the lead's language later — by the user, not this worker).

`confidence: medium` — detection quality depends on text length and the host model; hedge on short
input rather than over-claiming. Multilingual targets keep each language's keywords in their own
script (e.g. ko / en / zh) during discovery.
