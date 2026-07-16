from __future__ import annotations

import asyncio
import json
from datetime import date
from pathlib import Path

from travel_planner.config import Settings
from travel_planner.models import TripRequest
from travel_planner.providers import booking as booking_module
from travel_planner.providers import skyscanner as skyscanner_module
from travel_planner.providers.booking import BookingProvider
from travel_planner.providers.skyscanner import SkyscannerProvider


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


class DummyBookingClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        if url.endswith("/common/locations/cities"):
            return DummyResponse(fixture("booking_cities.json"))
        return DummyResponse(fixture("booking_stays.json"))


class DummySkyscannerClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, url, **kwargs):
        if url.endswith("/autosuggest/hotels"):
            return DummyResponse({"places": [{"entityId": "27542065", "name": "Tokyo"}]})
        if "/hotels/live/" in url:
            return DummyResponse(fixture("skyscanner_hotels.json"))
        return DummyResponse(fixture("skyscanner_flights.json"))


def test_booking_search_and_redirect_fixture(monkeypatch) -> None:
    monkeypatch.setattr(booking_module.httpx, "AsyncClient", lambda **kwargs: DummyBookingClient())
    provider = BookingProvider(
        Settings(
            booking_api_key="fixture",
            booking_affiliate_id="123",
            openai_api_key="",
            amadeus_client_id="",
            amadeus_client_secret="",
            google_maps_api_key="",
            skyscanner_api_key="",
        )
    )
    stays = asyncio.run(provider.search_stays(trip()))
    assert len(stays) == 1
    assert stays[0].provider == "Booking.com"
    assert stays[0].total_price_krw == 310000
    assert stays[0].verified_inventory is True
    assert stays[0].booking_url == "https://example.com/booking-hotel"


def test_skyscanner_flight_and_hotel_fixtures(monkeypatch) -> None:
    monkeypatch.setattr(skyscanner_module.httpx, "AsyncClient", lambda **kwargs: DummySkyscannerClient())
    provider = SkyscannerProvider(
        Settings(
            skyscanner_api_key="fixture",
            openai_api_key="",
            amadeus_client_id="",
            amadeus_client_secret="",
            google_maps_api_key="",
            booking_api_key="",
            booking_affiliate_id="",
        )
    )
    flights = asyncio.run(provider.search_flights(trip()))
    stays = asyncio.run(provider.search_stays(trip()))
    assert len(flights) == 1
    assert flights[0].duration_minutes == 300
    assert flights[0].total_price_krw == 540000
    assert len(stays) == 1
    assert stays[0].name == "Fixture Skyscanner Hotel"
    assert stays[0].total_price_krw == 420000

