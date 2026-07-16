# Scoring and routing

## Deterministic ranking

Calculate rankings in code. Use the LLM only to explain normalized facts.

- Flight: 40% total price, 25% elapsed time, 15% stops, 10% connection risk, 10% baggage certainty.
- Stay: 30% total price, 25% location efficiency, 20% review confidence, 15% preference fit, 10% cancellation flexibility.
- Balanced places: 35% preference fit, 30% travel efficiency, 20% review confidence, 15% cost.
- Budget places: 25% preference fit, 20% travel efficiency, 15% review confidence, 40% cost.
- Relaxed places: 25% preference fit, 30% travel efficiency, 15% review confidence, 30% low fatigue.

Normalize each dimension to 0–1 and retain the component values for explanations.

## Hard constraints

- Do not schedule outside known opening hours.
- Reserve airport and check-in buffers.
- Do not overlap fixed reservations.
- Keep meal windows unless the user opts out.
- Exclude closed or explicitly rejected places during replanning.
- Schedule every matched must-visit before optional places. During weather replanning, retain it unless closure or safety makes the visit infeasible.

## Failure behavior

- Return partial results when one vertical fails.
- Mark unknown routes and use conservative transfer buffers.
- Do not silently replace live data with samples. Samples must be visually and textually labeled.
- Recalculate only the remaining itinerary during an active-trip replan.
