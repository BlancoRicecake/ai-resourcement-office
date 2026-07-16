from __future__ import annotations

import asyncio
from datetime import date

from travel_planner.config import Settings
from travel_planner.database import Database
from travel_planner.models import ReplanRequest, TripRequest
from travel_planner.service import TravelPlannerService


def settings_without_keys(tmp_path) -> Settings:
    return Settings(
        db_path=str(tmp_path / "research.db"),
        openai_api_key="",
        amadeus_client_id="",
        amadeus_client_secret="",
        google_maps_api_key="",
        booking_api_key="",
        booking_affiliate_id="",
        skyscanner_api_key="",
    )


def la_trip(*, must_visits: list[str] | None = None) -> TripRequest:
    return TripRequest(
        destination_country="US",
        destination_city="로스앤젤레스",
        destination_code="LAX",
        origin_airport="ICN",
        departure_date=date(2026, 11, 2),
        return_date=date(2026, 11, 5),
        adults=1,
        rooms=1,
        budget_krw=3_000_000,
        stay_types=["hotel"],
        must_visit_places=must_visits or [],
    )


def test_no_key_mode_exposes_estimates_evidence_and_verification_links(tmp_path) -> None:
    settings = settings_without_keys(tmp_path)
    service = TravelPlannerService(settings, Database(settings.db_path))

    result = asyncio.run(service.create_trip(la_trip()))

    assert result.data_mode == "guided_research"
    assert set(result.sample_verticals) >= {"항공", "숙소", "장소"}
    assert all(offer.price_status == "estimated" and offer.confidence == "D" for offer in result.flights)
    assert all(offer.price_status == "estimated" and not offer.verified_inventory for offer in result.stays)
    assert any(item.source_type == "planning_baseline" for item in result.evidence)
    platforms = {item.platform for item in result.verification_links}
    assert {"Google Flights", "Skyscanner", "KAYAK", "네이버 항공권", "Booking.com", "Google Hotels"} <= platforms
    google_flights = next(item for item in result.verification_links if item.platform == "Google Flights")
    assert "ICN" in google_flights.url and "LAX" in google_flights.url
    assert "2026-11-02" in google_flights.url and "2026-11-05" in google_flights.url


def test_must_visit_is_hard_constraint_and_survives_rain_replan(tmp_path) -> None:
    settings = settings_without_keys(tmp_path)
    service = TravelPlannerService(settings, Database(settings.db_path))

    created = asyncio.run(service.create_trip(la_trip(must_visits=["그리피스 천문대"])))

    assert not any("확인하지 못했습니다" in warning for warning in created.warnings)
    for variant in created.itineraries:
        stops = [stop for day in variant.days for stop in day.stops]
        griffith = next(stop for stop in stops if "그리피스 천문대" in stop.place_name)
        assert "필수 방문지" in griffith.reason

    replanned = asyncio.run(
        service.replan_trip(created.id, ReplanRequest(weather="폭우", notes="필수 장소 유지"))
    )
    assert replanned is not None
    assert any(place.name == "그리피스 천문대" for place in replanned.places)
    assert all(
        any("그리피스 천문대" in stop.place_name for day in variant.days for stop in day.stops)
        for variant in replanned.itineraries
    )
    assert any("필수 방문지는 유지" in warning for warning in replanned.warnings)
