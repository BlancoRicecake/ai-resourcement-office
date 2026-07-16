from __future__ import annotations

import asyncio
from datetime import date

import pytest

from travel_planner.config import Settings
from travel_planner.database import Database
from travel_planner.models import ReplanRequest, TravelerProfile, TripRequest
from travel_planner.service import TravelPlannerService


def sample_settings(tmp_path) -> Settings:
    return Settings(
        db_path=str(tmp_path / "planner.db"),
        openai_api_key="",
        amadeus_client_id="",
        amadeus_client_secret="",
        google_maps_api_key="",
        booking_api_key="",
        booking_affiliate_id="",
        skyscanner_api_key="",
    )


def trip(city: str, country: str, code: str, origin: str = "ICN", rooms: int = 1) -> TripRequest:
    return TripRequest(
        destination_country=country,
        destination_city=city,
        destination_code=code,
        origin_airport=origin,
        departure_date=date(2026, 11, 2),
        return_date=date(2026, 11, 5),
        adults=2,
        rooms=rooms,
        budget_krw=4_000_000,
        stay_types=["hotel", "ryokan" if country == "JP" else "motel"],
    )


def test_profile_requires_consent_and_can_be_deleted(tmp_path) -> None:
    database = Database(str(tmp_path / "privacy.db"))
    database.save_profile(TravelerProfile(interests=["미술관"], consent_to_store=False))
    assert database.get_profile() is None
    database.save_profile(TravelerProfile(interests=["미술관"], consent_to_store=True))
    assert database.get_profile().interests == ["미술관"]
    database.delete_profile()
    assert database.get_profile() is None


@pytest.mark.parametrize(
    ("city", "country", "code", "origin", "rooms"),
    [
        ("도쿄", "JP", "TYO", "ICN", 1),
        ("오사카", "JP", "OSA", "PUS", 1),
        ("뉴욕", "US", "NYC", "ICN", 2),
        ("로스앤젤레스", "US", "LAX", "ICN", 1),
    ],
)
def test_representative_trip_scenarios(tmp_path, city, country, code, origin, rooms) -> None:
    settings = sample_settings(tmp_path)
    service = TravelPlannerService(settings, Database(settings.db_path))
    result = asyncio.run(service.create_trip(trip(city, country, code, origin, rooms)))
    assert result.status == "ready"
    assert result.sample_mode is True
    assert len(result.flights) == 3
    assert {stay.accommodation_type for stay in result.stays} == set(result.request.stay_types)
    assert len(result.itineraries) == 3
    assert all(stay.rooms_requested == rooms for stay in result.stays)


def test_rain_replan_prefers_rain_suitable_places(tmp_path) -> None:
    settings = sample_settings(tmp_path)
    service = TravelPlannerService(settings, Database(settings.db_path))
    created = asyncio.run(service.create_trip(trip("로스앤젤레스", "US", "LAX")))
    replanned = asyncio.run(service.replan_trip(created.id, ReplanRequest(weather="폭우", notes="실내 우선")))
    assert replanned is not None
    assert replanned.itineraries
    assert all(place.rain_suitable for place in replanned.places)
    assert any("우천" in warning for warning in replanned.warnings)
