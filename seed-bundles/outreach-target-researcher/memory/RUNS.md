# RUNS

The job inbox. Log each discovery run here, then promote generalizable lessons to a `knowledge/`
node (leaving a `-> [[node-id]]` back-reference). A repeatedly-confirmed lesson raises an existing
node's confidence instead of spawning a new one (merge; contradictions go to the user).

## Entry format

```txt
### YYYY-MM-DD — target: <slug> (run N)

- Scope: channels run, keywords/hashtags, filters, target count (ceiling)
- Auth: which channels authenticated / excluded / unauthenticated
- Yield: candidates seen -> passed gate -> qualified (and why below ceiling, if so)
- Channel status: success / partial / failed / unauthenticated per channel
- Notable leads: top fits with role + resolution + approach angle
- Duplicates/suppressed: counts dropped by the gate (S3 proof)
- Learnings: reusable lessons for the next run
- Promotion candidate: -> [[node-id]] (if a generalizable lesson, else omit)
```

## Run history

(None yet — logged as candidates as runs happen. No auto-commit.)
