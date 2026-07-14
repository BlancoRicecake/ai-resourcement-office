# Knowledge node INDEX

This file is the list (the index of an engine-less graph) of knowledge nodes. Usage:

- At session start, read **only this INDEX**. Do not pre-load every node body.
- Open only the nodes relevant to the current run, then follow their `[[wikilinks]]` to neighbors.
- When a node is added/removed, update the INDEX too — but propose it as a `memory update candidate`,
  never auto-commit (node and INDEX updated together).
- New knowledge accumulates in `memory/RUNS.md` (the inbox) first; when a generalizable lesson is
  confirmed, promote it to a node and add a one-line entry under "learned nodes" in the same format.

## seed nodes (shipped with the bundle · verified)

> Sources and grades are consolidated in `memory/RESEARCH.md`. Confidence is graded by evidence
> strength: `high` where backed by statute / established method, `medium` where it rests on
> practitioner canon or degrades on edge cases.

- [[two-axis-icp]] Two-axis ICP (identity x demand-intent) — tags: icp, targeting, foundation
- [[intent-signal-strength]] Intent-signal strength & recency decay — tags: intent, grading, demand
- [[human-vs-solo-brand-vs-bot]] Human vs solo-brand vs bot — tags: personhood, filtering, trust
- [[contact-channel-trust]] Contact-channel trust hierarchy — tags: contact, trust, extraction
- [[identity-resolution]] Identity resolution confidence — tags: identity, resolution, merge
- [[dedup-key-normalization]] Dedup key normalization & set-compare — tags: dedup, keys, gate
- [[language-detection-confidence]] Language-detection confidence — tags: language, honesty, soft-filter
- [[fit-scoring-rubric]] Six-axis fit scoring rubric — tags: scoring, transparency, qualification
- [[channel-tactics]] Per-channel discovery tactics — tags: channels, tactics, discovery
- [[approach-angle-derivation]] Approach-angle derivation — tags: angle, evidence, no-copy
- [[demand-false-positive]] Demand false-positive & role confusion — tags: role, producer, consumer
- [[seed-generalization]] Seed generalization — tags: seed, attributes, generalization
- [[cursor-frontier-search]] Cursor-based frontier search — tags: cursor, frontier, efficiency
- [[slow-readonly-default]] Slow, read-only default — tags: safety, ban-risk, read-only

## learned nodes (runtime-promoted)

None yet. A runtime-promoted node is added here in the same `- [[id]] Title — tags: …` format as the
seed nodes above.
