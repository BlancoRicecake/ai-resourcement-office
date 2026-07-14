# RESEARCH

Sources and references behind the knowledge nodes. **No verbatim source text is stored** — only
short citations and grades. The node bodies restate the ideas in the worker's own words; this list
is for re-checking and audit.

Citation format: `Author/Org (year). Title. Source. URL. [grade A/B/C]` -> `[[node]]`

## Law & privacy (for docs/security-notes.md and the guardrails)

- Regulation (EU) 2016/679 (GDPR) — Art. 6 lawful basis / Art. 17 right to erasure / Art. 21 right
  to object. https://eur-lex.europa.eu/eli/reg/2016/679/oj [A] -> [[slow-readonly-default]], erasure
- Korea. Personal Information Protection Act (PIPA), 개인정보 보호법.
  https://www.law.go.kr/LSW/eng/engLsSc.do?query=Personal+Information+Protection+Act [A] -> erasure
- Korea. Act on Promotion of Information and Communications Network Utilization (Network Act),
  정보통신망법 — §22 (consent to collect), §50 (restrictions on advertising transmission).
  https://www.law.go.kr/LSW/eng/engLsSc.do?query=Network+Act [A] -> [[contact-channel-trust]]
- United States. CAN-SPAM Act, 15 U.S.C. §7701 et seq.; FTC compliance guide.
  https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business [A] -> outreach legality
- Canada. Anti-Spam Legislation (CASL), S.C. 2010, c. 23.
  https://crtc.gc.ca/eng/internet/anti.htm [A] -> outreach legality
- hiQ Labs, Inc. v. LinkedIn Corp., 9th Cir. (2019/2022 on remand) — scraping of public data and the
  CFAA. https://www.eff.org/cases/hiq-v-linkedin [B, case summary] -> [[slow-readonly-default]]
- robots.txt / Robots Exclusion Protocol — RFC 9309.
  https://www.rfc-editor.org/rfc/rfc9309.html [A] -> [[channel-tactics]], [[slow-readonly-default]]

## ICP, intent & lead qualification

- Peppers & Rogers / practitioner canon on Ideal Customer Profile (identity + fit vs intent).
  Common B2B framing: ICP = firmographic/identity fit, buying-intent = behavioral signal.
  [C, practitioner synthesis] -> [[two-axis-icp]], [[intent-signal-strength]]
- Bosworth, N. Solution Selling / demand-signal reading (pain -> latent -> active demand).
  [C, practitioner] -> [[intent-signal-strength]], [[demand-false-positive]]
- BANT / intent-tiering practice (strong/medium/weak signal grading with recency). [C, practitioner]
  -> [[intent-signal-strength]], [[fit-scoring-rubric]]

## Identity resolution, dedup & language

- Entity resolution / record linkage — Fellegi–Sunter model (probabilistic matching, confirmed vs
  probable). Fellegi, I. & Sunter, A. (1969). A Theory for Record Linkage. JASA. [A] ->
  [[identity-resolution]], [[dedup-key-normalization]]
- Email address normalization / canonicalization (provider-specific dot & +tag folding, generic
  local parts). Practitioner + RFC 5321/5322 local-part semantics.
  https://www.rfc-editor.org/rfc/rfc5321 [A/B] -> [[dedup-key-normalization]]
- Public Suffix List (registrable-domain normalization). https://publicsuffix.org/ [A] ->
  [[dedup-key-normalization]]
- Language identification limits on short/code-mixed text — CLD / fastText langid known to degrade
  on short strings. Joulin et al. (2016), fastText. https://fasttext.cc/docs/en/language-identification.html
  [B] -> [[language-detection-confidence]]

## Discovery tooling (proper names kept as-is)

- Exa — neural/semantic web search API. https://exa.ai/ [tool] -> [[channel-tactics]]
- Jina Reader — URL-to-clean-text extraction. https://jina.ai/reader/ [tool] -> [[channel-tactics]],
  [[contact-channel-trust]]
- Agent-Reach — CLI for social discovery against the user's own sessions (X, Reddit, LinkedIn,
  Instagram, Xiaohongshu, Threads, TikTok). [tool] -> [[channel-tactics]], [[slow-readonly-default]]
- insane-search — fallback discovery channel. [tool] -> [[channel-tactics]]

## Notes

- Legal summaries in `docs/security-notes.md` are **not legal advice**; the legality of any outreach
  the user sends is the user's responsibility. Statute links above are primary sources; the hiQ
  entry is a case summary (B) pending the reader consulting the primary opinion.
- Practitioner-canon items ([C]) are widely-used framings, not peer-reviewed results; nodes citing
  them carry `confidence: medium` and hedge accordingly.
