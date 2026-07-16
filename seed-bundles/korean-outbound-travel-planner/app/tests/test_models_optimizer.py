from __future__ import annotations

import asyncio
from datetime import date

import pytest
from pydantic import ValidationError

from travel_planner.models import TripRequest
from travel_planner.optimizer import build_itineraries, rank_flights, rank_stays
from travel_planner.providers.sample import SampleProvider


def request_for(city: str = "도쿄", country: str = "JP", code: str = "TYO", rooms: int = 1) -> TripRequest:
    return TripRequest(
        destination_country=country,
        destination_city=city,
        destination_code=code,
        origin_airport="ICN",
        departure_date=date(2026, 10, 15),
        return_date=date(2026, 10, 18),
        adults=2 if rooms > 1 else 1,
        rooms=rooms,
        budget_krw=3_000_000,
        checked_baggage=True,
        stay_types=["hotel", "guesthouse"],
    )


def test_return_date_must_follow_departure() -> None:
    with pytest.raises(ValidationError):
        TripRequest(
            destination_country="JP",
            destination_city="도쿄",
            departure_date=date(2026, 10, 15),
            return_date=date(2026, 10, 15),
        )


def test_flight_ranking_accounts_for_baggage_and_stops() -> None:
    provider = SampleProvider()
    request = request_for()
    offers = asyncio.run(provider.search_flights(request))
    ranked = rank_flights(offers, checked_baggage=True)
    assert ranked[0].score >= ranked[-1].score
    assert any("위탁수하물" in reason for reason in ranked[0].score_reasons)
    assert ranked[-1].baggage_status in {"excluded", "unknown", "included"}


def test_stay_ranking_enforces_requested_types() -> None:
    provider = SampleProvider()
    request = request_for()
    offers = asyncio.run(provider.search_stays(request))
    ranked = rank_stays(offers, request)
    assert ranked[0].available is True
    assert all(offer.verified_inventory is False for offer in ranked)
    assert {offer.accommodation_type for offer in ranked} == {"hotel", "guesthouse"}
    assert ranked[0].rooms_requested == 1


def test_optimizer_builds_three_distinct_variants() -> None:
    provider = SampleProvider()
    request = request_for()
    flights = rank_flights(asyncio.run(provider.search_flights(request)), True)
    stays = rank_stays(asyncio.run(provider.search_stays(request)), request)
    places = asyncio.run(provider.search_places(request))
    matrix = asyncio.run(provider.route_matrix(places))
    variants = build_itineraries(request, flights, stays, places, matrix)
    assert [variant.id for variant in variants] == ["balanced", "budget", "relaxed"]
    assert len(variants[0].days) == 4
    assert sum(len(day.stops) for day in variants[2].days) < sum(len(day.stops) for day in variants[0].days)
    assert variants[1].trip_total_krw <= variants[2].trip_total_krw


def test_two_room_request_is_reflected_in_stay_total() -> None:
    provider = SampleProvider()
    one_room = asyncio.run(provider.search_stays(request_for()))[0]
    two_rooms = asyncio.run(provider.search_stays(request_for(city="뉴욕", country="US", code="NYC", rooms=2)))[0]
    assert two_rooms.rooms_requested == 2
    assert two_rooms.total_price_krw > one_room.total_price_krw


def test_la_itinerary_clusters_each_day_and_fills_full_stay() -> None:
    provider = SampleProvider()
    request = TripRequest(
        destination_country="US",
        destination_city="로스앤젤레스",
        destination_code="LAX",
        origin_airport="ICN",
        departure_date=date(2026, 9, 10),
        return_date=date(2026, 9, 16),
        adults=1,
        rooms=1,
        budget_krw=3_500_000,
        checked_baggage=True,
        stay_types=["hotel", "motel", "vacation_rental"],
        interests=["영화", "건축", "해변", "현지 음식", "카페"],
    )
    flights = rank_flights(asyncio.run(provider.search_flights(request)), True)
    stays = rank_stays(asyncio.run(provider.search_stays(request)), request)
    places = asyncio.run(provider.search_places(request))
    matrix = asyncio.run(provider.route_matrix(places))
    variants = build_itineraries(request, flights, stays, places, matrix)
    place_by_id = {place.id: place for place in places}

    assert {stay.accommodation_type for stay in stays} == {"hotel", "motel", "vacation_rental"}
    assert all(day.stops for day in variants[0].days[1:-1])
    assert not variants[0].days[-1].stops
    for day in variants[0].days[:-1]:
        districts = {place_by_id[stop.place_id].district for stop in day.stops}
        assert len(districts) == 1
        assert max((stop.transfer_minutes for stop in day.stops), default=0) <= 35

    signatures = {
        tuple(stop.place_id for day in variant.days for stop in day.stops)
        for variant in variants
    }
    assert len(signatures) == 3
    assert any("영화" in place.interest_tags for place in places)
    for variant in variants:
        assert variant.local_cost_krw == variant.place_cost_krw + variant.local_transport_cost_krw
        assert variant.trip_total_krw == (
            variant.flight_cost_krw
            + variant.stay_cost_krw
            + variant.place_cost_krw
            + variant.local_transport_cost_krw
        )
        assert variant.local_transport_cost_krw > 0
        assert sum(day.daily_cost_krw for day in variant.days) == variant.local_cost_krw
        assert all(stop.latitude and stop.longitude for day in variant.days for stop in day.stops)


def test_place_and_transit_costs_scale_with_traveler_count() -> None:
    provider = SampleProvider()
    one = request_for(city="로스앤젤레스", country="US", code="LAX")
    one.interests = ["영화", "건축", "현지 음식", "카페"]
    two = one.model_copy(update={"adults": 2})

    async def variant_for(request: TripRequest):
        flights = rank_flights(await provider.search_flights(request), request.checked_baggage)
        stays = rank_stays(await provider.search_stays(request), request)
        places = await provider.search_places(request)
        return build_itineraries(request, flights, stays, places, await provider.route_matrix(places))[0]

    one_variant = asyncio.run(variant_for(one))
    two_variant = asyncio.run(variant_for(two))
    assert two_variant.place_cost_krw == one_variant.place_cost_krw * 2
    assert two_variant.local_transport_cost_krw == one_variant.local_transport_cost_krw * 2
