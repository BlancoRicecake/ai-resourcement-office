# Web research fallback

Use this reference when a live flight, stay, place, or route provider is unavailable.

## Mode selection

1. Use `live` when every displayed offer comes from a current provider response.
2. Use `mixed` when at least one vertical is live and another uses estimates or web references.
3. Use `guided_research` when no travel API is available. Keep itinerary numbers as planning estimates and provide verification links.
4. Use `sample` only for an explicitly requested UI demo.

## Source order

1. Government, transport operator, attraction, hotel, or airline official site
2. Contracted travel provider or established comparison platform
3. Official destination marketing organization
4. Reputable editorial source
5. Community source for qualitative context only

Cross-check volatile or consequential claims. Prefer the page that directly shows the fact over search snippets.

## Confidence and value status

- `A / exact`: current API response matching the request
- `B / exact or reference`: current official page matching the relevant date or condition
- `C / reference or range`: visible comparison-platform result requiring checkout verification
- `D / estimated`: deterministic planning assumption or multi-source range
- `E / unknown`: not verified

Show source, URL, checked time, inclusions, and unknowns. Lower the price weight for C or D data. Never rank E values by price.

## Allowed web facts

- Official hours, closures, admission prices, reservation needs, accessibility notices
- Published transport fares, passes, service notices, and route guidance
- Dated public flight or hotel reference prices when the query conditions are visible
- Review aggregates when display and attribution rules permit

## Prohibited claims

- `현재 최저가`, `마지막 좌석`, or `마지막 객실` from snippets
- Final taxes, baggage, cancellation, or refund terms not visible on the exact offer
- Live Airbnb inventory without authorized access
- Automated booking or checkout

## Verification handoff

Provide at least two comparison surfaces plus the direct supplier where known. Pre-fill origin, destination, dates, traveler count, and room count when the platform supports stable parameters. Tell the user to compare the same fare family or room type and the final checkout total.

If the user supplies a chosen flight or stay, replace its estimate with the supplied exact time and total, mark it user-confirmed, and recalculate the itinerary.
