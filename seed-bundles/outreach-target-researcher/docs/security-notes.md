# Security Notes

**This is not legal advice.** It is a plain-language summary to help you act responsibly. The
**legality of any outreach you send is your responsibility**, not this worker's. When in doubt,
consult a qualified lawyer for your jurisdiction. Primary-source links are consolidated in
`memory/RESEARCH.md`.

## What this worker does and does not do

- It discovers **public business / creator contact points** for **review**, with provenance.
- It is **read-only** and **never sends outreach**, never stores passwords, and excludes private
  personal accounts, leaked data, and sources whose robots.txt / ToS forbid access.
- Collecting a public contact is a different act from **sending** to it. Sending is where most law
  applies — and that step is yours.

## Guardrails the worker enforces

- **Provenance required** — every lead carries a source URL + capture timestamp so you can verify.
- **DNC / erasure suppression** — a do-not-contact list is checked inline by the dedup gate and a
  suppressed key can never be re-collected (`worker/skills/erasure-handling.md`).
- **Exclude private personal accounts** — public business/creator only.
- **Producer-vs-consumer role check**, evidence on both ICP axes, and honest channel status.

## Jurisdiction summaries (high level, not exhaustive)

- **GDPR (EU/EEA).** Processing personal data needs a lawful basis (Art. 6; B2B outreach often relies
  on "legitimate interests," which requires a balancing test). Data subjects have the **right to
  erasure** (Art. 17) and the **right to object** (Art. 21). Honor opt-outs; keep only what you need.
- **Korea — PIPA (개인정보 보호법).** Governs collection/use of personal information and provides
  rights including deletion. Be cautious collecting and using personal data of Korean individuals.
- **Korea — Network Act (정보통신망법).** §22 concerns consent for collecting personal information;
  **§50 restricts sending advertising information** (opt-in / labeling / opt-out rules for commercial
  messages). Sending marketing messages to Korean recipients has specific requirements.
- **CAN-SPAM (US).** Commercial email must not use deceptive headers/subject lines, must identify
  itself as an ad where applicable, include a valid physical address, and honor opt-outs promptly.
  It does **not** require prior consent but strictly governs the send.
- **CASL (Canada).** Generally requires **consent** (express or implied) before sending commercial
  electronic messages, plus identification and a working unsubscribe. Stricter than CAN-SPAM.

## Public data scraping — the contested area

Courts have wrestled with scraping public data. In **hiQ Labs v. LinkedIn**, the Ninth Circuit
indicated that scraping **publicly available** data likely does not violate the CFAA's
"unauthorized access" provision — but this is fact-specific, addresses one statute, and does **not**
bless ignoring a site's Terms of Service, copyright, or privacy law. The conservative posture this
worker takes: **public-only, read-only, ToS/robots-respecting, slow, and provenance-stamped.**

## Data hygiene in memory

- The per-target ledger stores **public business contacts + provenance** — not private personal PII.
- The suppression list stores only the **normalized key** needed to *not* re-contact someone, which
  serves the erasure intent rather than working against it.
- Never persist passwords, private/gated content, or leaked data into `memory/`. Cite sources; do not
  store verbatim copyrighted text.

## Reliability note

This worker's output drives who you contact. That is why it mandates evidence on both axes, marks
unverifiable items honestly (`unknown` language, `probable` resolution), distinguishes a tool failure
from "no results," and never fabricates a lead. Final decisions — and their legality — are yours.
