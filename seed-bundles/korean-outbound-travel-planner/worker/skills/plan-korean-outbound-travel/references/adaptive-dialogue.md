# Adaptive dialogue

## Constraint ledger

- Preserve explicit user values as confirmed.
- Display inferred, default, and delegated values as proposed until confirmed.
- Distinguish hard constraints from soft preferences. Never silently relax a hard constraint.
- Treat `저렴하게` as an optimization preference, not a numeric budget cap.
- Do not infer allergies, accessibility needs, child ages, or driver age.

## Progressive questions

Unlock questions in this order: destination, flight, stay, ground transport, itinerary. Ask only the highest-impact unresolved question and include no more than two optional quick answers. Always show the current draft beside the question.

Use concrete tradeoffs for novice users. Offer `추천해줘` and `잘 모르겠어요` as valid answers; apply a visible recommended default and do not repeat the question.

Minimum preview inputs are destination or supported country plus approximate timing. Exact flight and stay search requires destination city, origin, exact dates, duration, and traveler count.

## Invalidation

- Date changes invalidate flight, stay, opening-hour, and itinerary results.
- Stay changes invalidate ground routes, hotel parking, fuel, and itinerary results.
- Transport changes invalidate route times, rental, fuel, and parking totals.
- Place changes invalidate only affected itinerary days unless dates also change.

When conflicting confirmed hard constraints appear, present the old and new values and ask which to keep. Latest explicit values may replace soft preferences without another question.

## Examples

- `8월에 친구랑 LA 가고 싶어`: infer two adults as proposed, default ICN as proposed, show an LA preview, then ask trip length.
- `경유 절대 싫고 침대 2개 필수`: set maximum stops to zero and bed count to two as hard constraints.
- `추천해줘`: apply the current question's recommended value as delegated and proposed, record the reason, and continue.
