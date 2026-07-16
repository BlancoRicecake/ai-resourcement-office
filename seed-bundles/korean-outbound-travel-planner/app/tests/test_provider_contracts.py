from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

from travel_planner.config import Settings
from travel_planner.models import TripRequest
from travel_planner.providers import amadeus as amadeus_module
from travel_planner.providers import google as google_module
from travel_planner.providers.amadeus import AmadeusProvider, duration_minutes
from travel_planner.providers.google import GooglePlaceRouteProvider


FIXTURES = Path(__file__).parent / "fixtures"


def fixture(name: str):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def trip() -> TripRequest:
    return TripRequest(
        destination_country="JP",
        destination_city="도쿄",
        destination_code="TYO",
        origin_airport="ICN",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 18),
        adults=1,
        rooms=1,
        budget_krw=1_500_000,
    )


class DummyResponse:
    def __init__(self, payload):
        self.payload = payload
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self.payload


class DummyAmadeusClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        return DummyResponse({"access_token": "fixture-token"})

    async def get(self, url, **kwargs):
        return DummyResponse(fixture("amadeus_flights.json"))


class DummyGoogleClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        if "distanceMatrix" in url:
            return DummyResponse(fixture("google_routes.json"))
        return DummyResponse(fixture("google_places.json"))


def test_amadeus_flight_fixture_normalization(monkeypatch) -> None:
    monkeypatch.setattr(amadeus_module.httpx, "AsyncClient", lambda **kwargs: DummyAmadeusClient())
    provider = AmadeusProvider(
        Settings(amadeus_client_id="fixture", amadeus_client_secret="fixture", openai_api_key="", google_maps_api_key="")
    )
    offers = asyncio.run(provider.search_flights(trip()))
    assert duration_minutes("PT2H25M") == 145
    assert len(offers) == 1
    assert offers[0].total_price_krw == 512000
    assert offers[0].baggage_status == "included"
    assert offers[0].duration_minutes == 300
    assert offers[0].segments[0].carrier == "Korean Air"


def test_google_places_and_routes_fixture_normalization(monkeypatch) -> None:
    monkeypatch.setattr(google_module.httpx, "AsyncClient", lambda **kwargs: DummyGoogleClient())
    provider = GooglePlaceRouteProvider(Settings(google_maps_api_key="fixture", openai_api_key=""))
    places = asyncio.run(provider.search_places(trip()))
    assert len(places) == 1
    assert places[0].rating == 4.7
    assert places[0].price_level == 2
    assert "wheelchairAccessibleEntrance" in places[0].accessibility
    matrix = asyncio.run(provider.route_matrix(places))
    assert matrix[(places[0].id, places[0].id)] == (0, 0.0)

