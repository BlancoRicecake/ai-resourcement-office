---
name: plan-korean-outbound-travel
description: Plan Korean-origin overseas trips using current flight, accommodation, place, and route data, and bootstrap unvalidated destinations from official sources. Use when comparing travel options, collecting trip constraints, researching a new destination, building Korean-language day-by-day itineraries, explaining route tradeoffs, refreshing stale prices, or replanning an active trip.
---

# Plan Korean Outbound Travel

## Workflow

1. Extract every explicit constraint from the user's natural-language request before asking anything. Mark inferred and default values as editable proposals.
2. Show a useful hypothesis draft as soon as destination and approximate timing are known. Ask one highest-impact question at a time and never repeat an answered or delegated question.
3. Treat `꼭`, `절대`, `무조건`, `필수`, and `경유 없이` as hard constraints; treat `선호`, `가능하면`, and `되도록` as soft preferences. Ask before relaxing a hard constraint.
4. Progressively unlock flight, stay, ground-transport, and itinerary questions only when the preceding decision makes them relevant. Never request passport, payment, or account credentials.
5. Search configured providers. Normalize currencies, taxes, baggage, beds, parking, inventory, cancellation terms, source, and observation time before comparing results.
6. For an unvalidated destination, create a research pack and resolve official entry, safety, airport, transport, pricing, and tourism sources before routing. Never substitute another city's sample facts. If a live vertical is unavailable, use web research when available; otherwise provide verification links and mark facts pending.
7. Rank and calculate offers in code. Include rental, fuel, parking, and requested meal budgets when applicable.
8. Build exactly three variants: balanced, budget, and relaxed. Treat opening hours, reservations, flight times, check-in or check-out, and named must-visits as hard constraints.
9. Show each stop's local time, duration, transfer, estimated cost, booking need, reason, drawback, and rain alternative. Attach source, confidence, value status, and observed time to changeable facts.
10. Provide external booking links and require final verification before purchase or departure.

## Output Contract

- Start with a concise trip summary and unresolved checks.
- Compare no more than five leading flight and stay offers per category.
- Explain why one option is recommended; do not merely sort by price.
- Present the three itinerary variants with explicit pros and cons.
- Use Korean and KRW by default, while retaining local names, local times, and supplier currency.
- Say `연결된 공급자의 현재 검색 결과 중 최적` rather than claiming a universal lowest price.

## References

- Read [provider-contracts.md](references/provider-contracts.md) before adding or interpreting a live provider.
- Read [korean-traveler-checklist.md](references/korean-traveler-checklist.md) when producing entry, safety, or pre-departure checks.
- Read [scoring-and-routing.md](references/scoring-and-routing.md) when changing rankings, itinerary weights, or failure behavior.
- Read [web-research-fallback.md](references/web-research-fallback.md) whenever a live vertical is unavailable or a web-derived fact is used.
- Read [adaptive-dialogue.md](references/adaptive-dialogue.md) when collecting vague requests, choosing the next question, resolving conflicts, or converting a planning session into a final trip request.
- Read [destination-bootstrap.md](references/destination-bootstrap.md) whenever the requested city is not already validated.
