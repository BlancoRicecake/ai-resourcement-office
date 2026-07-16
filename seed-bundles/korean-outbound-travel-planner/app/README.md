# App

## Run

```powershell
pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn travel_planner.main:app --reload
```

The app runs at `http://127.0.0.1:8000`; OpenAPI docs are at `/docs`.

The default UI starts with a natural-language planning session. It extracts confirmed and proposed constraints, asks one high-impact question at a time, and only materializes a final `TripRequest` when flight search is ready. The original detailed form and `POST /api/trips` remain available.

Planning-session API:

- `POST /api/planning-sessions`
- `GET /api/planning-sessions/{id}`
- `POST /api/planning-sessions/{id}/messages`
- `PATCH /api/planning-sessions/{id}/constraints`
- `POST /api/planning-sessions/{id}/finalize`
- `DELETE /api/planning-sessions/{id}`

Sessions stay in process memory unless the user explicitly consents to local persistence. Final trip calculations support hard nonstop and bed/parking constraints plus planning estimates for rental-car, fuel, and parking costs.

Without travel API keys the app enters `guided_research` mode: it uses clearly labeled planning estimates and generates parameterized comparison and official verification links. It does not scrape search-result pages or claim live inventory. A host agent with a supported web-search tool follows the bundled travel skill to collect current official facts. Configure Amadeus and Google keys in `app/.env` to activate live adapters.
