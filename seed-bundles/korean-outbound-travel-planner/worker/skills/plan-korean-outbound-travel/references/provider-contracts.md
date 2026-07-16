# Provider contracts

## Shared rules

- Keep provider responses behind normalized flight, stay, place, and route interfaces.
- Preserve the provider name, offer identifier, source currency, observed timestamp, and redirect URL.
- Distinguish `included`, `excluded`, and `unknown` for taxes, baggage, meals, and cancellation.
- Treat prices older than 15 minutes as stale and refresh before the user follows a booking link.
- Never expose server API keys to browser code or logs.

## Web research fallback

- Use the host's supported web-search tool; do not scrape search-result pages or bypass access controls.
- Web research may confirm official hours, admission prices, location, transport fares, and dated public notices.
- Do not convert snippets or undated pages into live inventory, remaining-room claims, or checkout totals.
- Keep web-derived facts outside provider offer adapters unless the page visibly matches dates, traveler count, room count, and fare or room conditions.
- Always attach a direct source URL and a parameterized comparison link.

## Amadeus

- Use OAuth client credentials on the server.
- Use Flight Offers Search for current flight offers.
- Use Hotel List followed by Hotel Offers for current room inventory and prices.
- Expect test data in the test environment and disclose that it is not production inventory.
- Re-search an offer before redirecting because availability can change.

## Google Places and Routes

- Request only fields displayed or used for scoring.
- Preserve required attribution and link users to Google Maps for route or place details.
- Do not cache restricted Places or Routes content beyond provider terms; place IDs may be persisted.
- Treat missing opening hours and accessibility information as unknown.

## Booking.com and Skyscanner

- Enable only after the user obtains partner approval and accepts the applicable agreement.
- Implement search-and-redirect, not in-app booking, for this bundle.
- Map provider-specific accommodation types into the shared taxonomy without inventing unavailable categories.

## Airbnb

- Do not claim live Airbnb price or inventory without authorized API access.
- A generated search link is a discovery aid only and must be labeled `가격·재고 미검증`.
