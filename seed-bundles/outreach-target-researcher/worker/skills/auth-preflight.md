---
name: auth-preflight
description: Use before per-channel discovery to verify channel authentication. Covers agent-reach doctor, the exclude-vs-login branch for unauthenticated channels, and mid-run handling of "authentication required".
---

# Auth preflight

Before spending any discovery budget, confirm which channels are actually reachable. A channel that
is not logged in will return nothing — and that "nothing" must be reported as **`unauthenticated`**,
never as `0 results` ([[slow-readonly-default]], and see docs/limitations.md).

## Steps

1. Run `agent-reach doctor`. Record, per channel: authenticated / not authenticated / not installed.
2. For each channel in the ICP that is **not authenticated**, present a branch to the
   user (in their language):
   - **(A) Exclude** this channel from this run (it will show as `unauthenticated` in the channel
     status of the insight report).
   - **(B) Log in** using the dedicated discovery sub-account, then continue.
3. Only proceed to discovery on channels that are authenticated (or web channels that need no login).
4. For web (Exa/Jina) and `insane-search`, confirm the fetch path works; if not, mark those channels
   `discovery-failed` and continue with what works.

## Mid-run: "authentication required"

If a channel drops to `authentication required` **during** a run (session expired, challenge
presented):

- **Stop that channel immediately** — do not retry aggressively; repeated failed auth looks like an
  attack and risks a ban.
- Surface the branch again (exclude / re-login), and record how many leads were gathered before the
  drop so the channel status can be reported as `partial`.
- This is the workflow-step-2 branch referenced by `worker/agent.md` ③ step 10.

## Never

- Never store or ask to store passwords. Agent-Reach uses the interactive session.
- Never brute-force or bypass a login wall, CAPTCHA, or challenge. If a channel is gated, it is
  excluded, not forced.
