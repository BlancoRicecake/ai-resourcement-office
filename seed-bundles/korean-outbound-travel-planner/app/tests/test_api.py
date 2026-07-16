from __future__ import annotations

from fastapi.testclient import TestClient

from travel_planner import main
from travel_planner.config import Settings
from travel_planner.database import Database
from travel_planner.service import TravelPlannerService


def test_health_and_trip_api(tmp_path, monkeypatch) -> None:
    settings = Settings(
        db_path=str(tmp_path / "api.db"),
        openai_api_key="",
        amadeus_client_id="",
        amadeus_client_secret="",
        google_maps_api_key="",
        booking_api_key="",
        booking_affiliate_id="",
        skyscanner_api_key="",
    )
    database = Database(settings.db_path)
    monkeypatch.setattr(main, "database", database)
    monkeypatch.setattr(main, "planner", TravelPlannerService(settings, database))
    client = TestClient(main.app)
    assert client.get("/health").json() == {"status": "ok"}
    page = client.get("/")
    assert page.status_code == 200
    assert 'id="route-map"' in page.text
    assert "leaflet@1.9.4" in page.text
    response = client.post(
        "/api/trips",
        json={
            "destination_country": "JP",
            "destination_city": "도쿄",
            "destination_code": "TYO",
            "origin_airport": "ICN",
            "departure_date": "2026-10-15",
            "return_date": "2026-10-18",
            "adults": 1,
            "rooms": 1,
            "budget_krw": 1500000,
        },
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["sample_mode"] is True
    assert payload["data_mode"] == "guided_research"
    assert payload["verification_links"]
    assert payload["evidence"]
    assert len(payload["itineraries"]) == 3
    assert client.get(f"/api/trips/{payload['id']}").status_code == 200
