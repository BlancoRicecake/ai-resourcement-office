---
id: identity-resolution
title: Identity resolution confidence
tags:
  - identity
  - resolution
  - merge
source: seed
confidence: high
created: 2026-07-15
---
When the same person appears across accounts, resolve them into one identity — **conservatively**.
A wrong merge fabricates a person who doesn't exist. **[H5]**

Assign an `identity_cluster_id` grouping accounts believed to be the same person, and grade the
`resolution`:

- **`confirmed`** — a **strong anchor** ties the accounts: matching handle *and* own domain *and*
  name, or an explicit cross-link (the X bio links the exact site whose contact page names the same
  person). High certainty.
- **`probable`** — only **circumstantial** evidence: same display name but different handle, similar
  content, same city. Recorded as probable, never promoted to confirmed without a strong anchor.
- **`single`** — just one account; no merge attempted.

The rule (success criterion **S9**): **only strong anchors produce `confirmed`.** Prefer leaving two
records separate over merging on weak evidence — a false merge corrupts the contact, the provenance,
and the count. Generic keys (`info@`, a shared agency domain) must **not** be used as merge anchors
(see [[dedup-key-normalization]]) — many people can sit behind one `info@`.

Resolution interacts with dedup: two accounts confirmed as one person should collapse to one lead,
and their keys both enter the ledger so neither is re-collected. This borrows from record-linkage
practice (Fellegi–Sunter, RESEARCH.md): a probabilistic match is stated with its confidence, not
asserted as fact. When uncertain, expose the uncertainty in `resolution` rather than hiding it.
