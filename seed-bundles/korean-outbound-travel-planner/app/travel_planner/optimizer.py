from __future__ import annotations

import json
from datetime import timedelta
from math import sqrt
from pathlib import Path

from .models import (
    FlightOffer,
    ItineraryDay,
    ItineraryStop,
    ItineraryVariant,
    Pace,
    PlaceCandidate,
    StayOffer,
    TripRequest,
)
from .providers.sample import city_config, haversine_km


SCORING = json.loads((Path(__file__).resolve().parents[1] / "config" / "scoring.json").read_text(encoding="utf-8"))


def _low_is_good(value: float, values: list[float]) -> float:
    minimum, maximum = min(values), max(values)
    return 1.0 if maximum == minimum else 1 - (value - minimum) / (maximum - minimum)


def _high_is_good(value: float, values: list[float]) -> float:
    minimum, maximum = min(values), max(values)
    return 1.0 if maximum == minimum else (value - minimum) / (maximum - minimum)


def rank_flights(offers: list[FlightOffer], checked_baggage: bool) -> list[FlightOffer]:
    if not offers:
        return []
    prices = [offer.total_price_krw for offer in offers]
    durations = [offer.duration_minutes for offer in offers]
    for offer in offers:
        price_score = _low_is_good(offer.total_price_krw, prices)
        duration_score = _low_is_good(offer.duration_minutes, durations)
        stop_score = max(0.0, 1 - offer.stops * 0.4)
        risk_score = max(0.0, 1 - offer.stops * 0.25 - (0.4 if offer.airport_change else 0))
        baggage_score = {"included": 1.0, "unknown": 0.45, "excluded": 0.1}[offer.baggage_status]
        if not checked_baggage:
            baggage_score = max(baggage_score, 0.75)
        weights = SCORING["flight"]
        offer.score = round(
            price_score * weights["price"]
            + duration_score * weights["duration"]
            + stop_score * weights["stops"]
            + risk_score * weights["connection_risk"]
            + baggage_score * weights["baggage_certainty"],
            4,
        )
        offer.score_reasons.extend(
            [
                f"총액 {offer.total_price_krw:,}원",
                f"총 {offer.duration_minutes // 60}시간 {offer.duration_minutes % 60}분",
                f"환승 {offer.stops}회",
                f"위탁수하물 {offer.baggage_status}",
            ]
        )
    return sorted(offers, key=lambda offer: offer.score or 0, reverse=True)


def rank_stays(offers: list[StayOffer], request: TripRequest) -> list[StayOffer]:
    requested_types = set(request.stay_types)
    offers = [offer for offer in offers if offer.accommodation_type in requested_types]
    if not offers:
        return []
    prices = [offer.total_price_krw for offer in offers]
    ratings = [offer.rating or 0 for offer in offers]
    cfg = city_config(request)
    distances = [haversine_km(offer.latitude, offer.longitude, cfg["lat"], cfg["lng"]) for offer in offers]
    for index, offer in enumerate(offers):
        price_score = _low_is_good(offer.total_price_krw, prices)
        location_score = _low_is_good(distances[index], distances)
        rating_score = _high_is_good(offer.rating or 0, ratings)
        review_confidence = min(1.0, sqrt(offer.review_count or 0) / 50) if offer.rating else 0.25
        review_score = rating_score * 0.7 + review_confidence * 0.3
        preference = 1.0
        cancellation = 0.8 if "무료" in offer.cancellation_policy else 0.45
        availability = 1.0 if offer.available and offer.verified_inventory else (0.25 if offer.available else 0.05)
        weights = SCORING["stay"]
        offer.score = round(
            (
                price_score * weights["price"]
                + location_score * weights["location_efficiency"]
                + review_score * weights["review_confidence"]
                + preference * weights["preference_fit"]
                + cancellation * weights["cancellation_flexibility"]
            )
            * availability,
            4,
        )
        offer.score_reasons = [
            f"{request.rooms}객실 총 {offer.total_price_krw:,}원",
            f"중심부 약 {distances[index]:.1f}km",
            f"평점 {offer.rating if offer.rating is not None else '확인 필요'}",
            f"침대 {offer.bed_count}개" if offer.bed_count else "침대 수 확인 필요",
            (
                "주차 무료" if offer.parking_available and offer.parking_cost_krw_per_night == 0
                else (f"주차 1박 {offer.parking_cost_krw_per_night:,}원" if offer.parking_cost_krw_per_night else "주차 조건 확인 필요")
            ),
            "실시간 재고 확인" if offer.verified_inventory else "가격·재고 미검증",
        ]
    return sorted(offers, key=lambda offer: offer.score or 0, reverse=True)


def _place_score(place: PlaceCandidate, variant: Pace, center: tuple[float, float]) -> float:
    rating = (place.rating or 3.5) / 5
    review_confidence = min(1.0, sqrt(place.review_count or 0) / 300)
    review_score = rating * 0.75 + review_confidence * 0.25
    distance = haversine_km(place.latitude, place.longitude, center[0], center[1])
    travel_efficiency = max(0.0, 1 - distance / 25)
    cost_score = max(0.0, 1 - place.estimated_cost_krw / 100_000)
    duration_factor = max(0.35, 1 - max(0, place.visit_duration_minutes - 60) / 420)
    fatigue_score = duration_factor * 0.7 + (0.3 if place.rain_suitable else 0.15)
    weights = SCORING["places"][variant]
    dimensions = {
        "preference_fit": place.interest_match,
        "travel_efficiency": travel_efficiency,
        "review_confidence": review_score,
        "cost": cost_score,
        "low_fatigue": fatigue_score,
    }
    return sum(dimensions[key] * weight for key, weight in weights.items())


def _district_key(place: PlaceCandidate) -> str:
    if place.district:
        return place.district
    # 공급자가 권역명을 주지 않으면 약 8~11km 단위의 지리 버킷으로 묶는다.
    return f"geo:{round(place.latitude, 1)}:{round(place.longitude, 1)}"


def _normalized_place_name(value: str) -> str:
    return "".join(value.lower().split())


def match_must_visit_places(request: TripRequest, places: list[PlaceCandidate]) -> list[PlaceCandidate]:
    matched: list[PlaceCandidate] = []
    for requested_name in request.must_visit_places:
        needle = _normalized_place_name(requested_name)
        match = next(
            (
                place
                for place in places
                if needle in _normalized_place_name(place.name)
                or needle in _normalized_place_name(place.local_name or "")
                or _normalized_place_name(place.name) in needle
                or (_normalized_place_name(place.local_name or "") and _normalized_place_name(place.local_name or "") in needle)
            ),
            None,
        )
        if match and match.id not in {item.id for item in matched}:
            matched.append(match)
    return matched


def _transfer(
    origin: PlaceCandidate,
    destination: PlaceCandidate,
    matrix: dict[tuple[str, str], tuple[int, float]],
) -> tuple[int, float]:
    fallback_distance = haversine_km(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
    return matrix.get(
        (origin.id, destination.id),
        (max(10, round(fallback_distance / 18 * 60 + 5)), round(fallback_distance, 2)),
    )


def _pick_in_district(
    candidates: list[PlaceCandidate],
    category: str | None,
    used: set[str],
    scores: dict[str, float],
    previous: PlaceCandidate | None,
    matrix: dict[tuple[str, str], tuple[int, float]],
) -> PlaceCandidate | None:
    available = [
        place
        for place in candidates
        if place.id not in used and place.business_status not in {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}
        and (previous is None or place.visit_duration_minutes <= 180)
    ]
    category_matches = [place for place in available if category is None or place.category == category]
    options = category_matches or available
    standard_duration = [place for place in options if place.visit_duration_minutes <= 240]
    options = standard_duration or options
    if not options:
        return None

    def selection_score(place: PlaceCandidate) -> float:
        transfer_penalty = 0.0
        if previous:
            minutes, _ = _transfer(previous, place, matrix)
            transfer_penalty = min(0.45, minutes / 180)
        return scores[place.id] + place.interest_match * 0.1 - transfer_penalty

    selected = max(options, key=selection_score)
    used.add(selected.id)
    return selected


def _day_pattern(day_index: int, day_count: int, variant: Pace) -> list[tuple[str, str | None]]:
    if day_index == day_count - 1:
        return []
    if variant == "relaxed":
        if day_index == 0:
            return [("16:00", "cafe"), ("18:30", "restaurant")]
        return [("10:00", "attraction"), ("13:30", "restaurant")]
    if variant == "budget":
        if day_index == 0:
            return [("15:30", None), ("18:30", "restaurant")]
        return [("09:00", "attraction"), ("12:30", "restaurant"), ("14:30", None)]
    if day_index == 0:
        return [("15:30", "attraction"), ("18:30", "restaurant")]
    return [("09:30", "attraction"), ("12:30", "restaurant"), ("14:30", "cafe"), ("16:00", "attraction")]


def _minutes(value: str) -> int:
    hours, mins = (int(part) for part in value.split(":"))
    return hours * 60 + mins


def _format_minutes(value: int) -> str:
    return f"{(value // 60) % 24:02d}:{value % 60:02d}"


def _fit_opening_hours(place: PlaceCandidate, current_date, proposed_start: int) -> int | None:
    if not place.weekday_hours:
        return proposed_start
    windows = place.weekday_hours.get(current_date.weekday(), [])
    if not windows:
        return None
    for window in windows:
        try:
            opening, closing = window.split("-", 1)
            start = max(proposed_start, _minutes(opening))
            if start + place.visit_duration_minutes <= _minutes(closing):
                return start
        except (TypeError, ValueError):
            continue
    return None


def _choose_district(
    remaining: list[PlaceCandidate],
    used_districts: set[str],
    variant: Pace,
    center: tuple[float, float],
    scores: dict[str, float],
    arrival_day: bool,
    priority_place: PlaceCandidate | None = None,
) -> tuple[str, list[PlaceCandidate]] | None:
    groups: dict[str, list[PlaceCandidate]] = {}
    for place in remaining:
        groups.setdefault(_district_key(place), []).append(place)
    if not groups:
        return None
    if priority_place:
        priority_district = _district_key(priority_place)
        if priority_district in groups:
            return priority_district, groups[priority_district]
    unused = {key: value for key, value in groups.items() if key not in used_districts}
    candidates = unused or groups

    def group_score(item: tuple[str, list[PlaceCandidate]]) -> float:
        _, district_places = item
        ranked = sorted((scores[place.id] for place in district_places), reverse=True)
        quality = sum(ranked[:4]) / min(4, len(ranked))
        coverage = len({place.category for place in district_places}) / 5
        centroid_lat = sum(place.latitude for place in district_places) / len(district_places)
        centroid_lng = sum(place.longitude for place in district_places) / len(district_places)
        center_distance = haversine_km(centroid_lat, centroid_lng, center[0], center[1])
        if arrival_day:
            return quality + coverage * 0.15 - center_distance / 25
        if variant == "budget":
            average_cost = sum(place.estimated_cost_krw for place in district_places) / len(district_places)
            return quality + coverage * 0.2 - average_cost / 180_000
        compactness = sum(
            haversine_km(place.latitude, place.longitude, centroid_lat, centroid_lng) for place in district_places
        ) / len(district_places)
        if variant == "relaxed":
            return quality + coverage * 0.1 - compactness / 12
        return quality + coverage * 0.25 - compactness / 20

    district, district_places = max(candidates.items(), key=group_score)
    return district, district_places


def _select_inventory(
    variant: Pace, flights: list[FlightOffer], stays: list[StayOffer]
) -> tuple[FlightOffer, StayOffer]:
    available_stays = [stay for stay in stays if stay.available and stay.verified_inventory] or stays
    if variant == "budget":
        return min(flights, key=lambda item: item.total_price_krw), min(available_stays, key=lambda item: item.total_price_krw)
    if variant == "relaxed":
        flight = min(flights, key=lambda item: (item.stops, item.duration_minutes, -int(item.baggage_status == "included")))
        stay = max(available_stays, key=lambda item: (item.rating or 0, item.score or 0))
        return flight, stay
    return flights[0], available_stays[0]


def build_itineraries(
    request: TripRequest,
    flights: list[FlightOffer],
    stays: list[StayOffer],
    places: list[PlaceCandidate],
    matrix: dict[tuple[str, str], tuple[int, float]],
) -> list[ItineraryVariant]:
    if not flights or not stays or not places:
        return []
    cfg = city_config(request)
    center = (cfg["lat"], cfg["lng"])
    day_count = (request.return_date - request.departure_date).days + 1
    cost_config = SCORING["cost_assumptions"]
    traveler_cost_units = request.adults + request.children * cost_config["child_cost_multiplier"]
    transit_per_boarding = cost_config["local_transit_per_boarding_krw"][request.destination_country]
    must_visit_places = match_must_visit_places(request, places)
    must_visit_ids = {place.id for place in must_visit_places}
    definitions: list[tuple[Pace, str, str, list[str], list[str]]] = [
        (
            "balanced",
            "균형형",
            "취향 적합도와 이동 효율을 함께 최적화한 기본 추천",
            ["대표 명소·식사·카페의 균형", "이동시간과 평점 신뢰도를 함께 반영"],
            ["최저 비용만을 목표로 한 일정은 아님", "인기 장소는 혼잡할 수 있음"],
        ),
        (
            "budget",
            "비용 절약형",
            "무료·저가 장소와 저렴한 이동 및 숙박을 우선한 대안",
            ["세 가지 안 중 예상비용이 가장 낮음", "무료 명소와 실속형 식사 비중이 높음"],
            ["이동시간이나 환승이 늘 수 있음", "숙소·항공 편의 조건이 낮을 수 있음"],
        ),
        (
            "relaxed",
            "여유형",
            "하루 장소 수와 이동 부담을 줄이고 휴식 시간을 확보한 대안",
            ["일정 사이 여유와 회복 시간이 큼", "환승과 도보 부담을 낮춤"],
            ["방문 장소 수가 적음", "편의성 우선 선택으로 비용이 높아질 수 있음"],
        ),
    ]
    variants = []
    for variant_id, name, summary, pros, cons in definitions:
        scores = {place.id: _place_score(place, variant_id, center) for place in places}
        selected_flight, selected_stay = _select_inventory(variant_id, flights, stays)
        used: set[str] = set()
        used_districts: set[str] = set()
        days: list[ItineraryDay] = []
        for day_index in range(day_count):
            current_date = request.departure_date + timedelta(days=day_index)
            stops: list[ItineraryStop] = []
            previous: PlaceCandidate | None = None
            pattern = _day_pattern(day_index, day_count, variant_id)
            remaining = [place for place in places if place.id not in used]
            priority_place = next((place for place in must_visit_places if place.id not in used), None)
            if day_index == 0 and priority_place and priority_place.visit_duration_minutes > 240:
                priority_place = None
            chosen_district = _choose_district(
                remaining,
                used_districts,
                variant_id,
                center,
                scores,
                arrival_day=day_index == 0,
                priority_place=priority_place,
            ) if pattern else None
            district_name = chosen_district[0] if chosen_district else None
            district_places = chosen_district[1] if chosen_district else []
            if district_name:
                used_districts.add(district_name)

            previous_end = 0
            for planned_start, category in pattern:
                is_priority_stop = bool(priority_place and priority_place.id not in used)
                if is_priority_stop:
                    place = priority_place
                    used.add(place.id)
                else:
                    place = _pick_in_district(district_places, category, used, scores, previous, matrix)
                if not place:
                    break
                transfer_minutes, transfer_distance = (0, 0.0)
                if previous:
                    transfer_minutes, transfer_distance = _transfer(previous, place, matrix)
                    if request.ground_transport.mode == "rental_car":
                        transfer_minutes = max(10, round(transfer_distance / 22 * 60 * 1.35))
                    if transfer_minutes > 35 and len(stops) >= 3:
                        used.discard(place.id)
                        break
                actual_start = max(_minutes(planned_start), previous_end + transfer_minutes + (15 if previous else 0))
                actual_start = _fit_opening_hours(place, current_date, actual_start)
                if actual_start is None:
                    used.discard(place.id)
                    break
                if actual_start >= 20 * 60:
                    used.discard(place.id)
                    break
                duration = place.visit_duration_minutes
                end_minutes = actual_start + duration
                rental_car = request.ground_transport.mode == "rental_car"
                transfer_mode = "자동차" if rental_car and previous else ("대중교통" if transfer_distance >= 1 else "도보")
                place_cost = round(place.estimated_cost_krw * traveler_cost_units)
                transfer_cost = (
                    round(transit_per_boarding * traveler_cost_units)
                    if previous and transfer_mode == "대중교통"
                    else 0
                )
                parking_cost = place.parking_cost_krw if rental_car else 0
                stops.append(
                    ItineraryStop(
                        start_time=_format_minutes(actual_start),
                        end_time=_format_minutes(end_minutes),
                        place_id=place.id,
                        place_name=f"{place.name}" + (f" ({place.local_name})" if place.local_name and place.local_name != place.name else ""),
                        category=place.category,
                        transfer_mode=transfer_mode,
                        transfer_minutes=transfer_minutes,
                        transfer_distance_km=transfer_distance,
                        latitude=place.latitude,
                        longitude=place.longitude,
                        district=place.district,
                        unit_place_cost_krw=place.estimated_cost_krw,
                        place_cost_krw=place_cost,
                        transfer_cost_krw=transfer_cost,
                        parking_cost_krw=parking_cost,
                        estimated_cost_krw=place_cost + transfer_cost + parking_cost,
                        booking_required=place.category == "attraction" and place.estimated_cost_krw >= 20_000,
                        reason=(
                            "사용자가 지정한 필수 방문지로 고정 배치"
                            if place.id in must_visit_ids
                            else (
                                (
                                    f"하루 특별식 예산 {request.dining_preferences.special_meal_budget_krw:,}원 이내 후보"
                                    if place.category == "restaurant"
                                    and request.dining_preferences.special_meals_per_day
                                    and request.dining_preferences.special_meal_budget_krw
                                    else f"{place.district or '인접 지역'} 권역에서 {name} 점수·관심사 "
                                    f"({', '.join(place.interest_tags[:2]) or '일반'})를 반영"
                                )
                            )
                        ),
                        drawback=(
                            f"이전 장소에서 이동 {transfer_minutes}분 — 교통상황 재확인 필요"
                            if transfer_minutes >= 40
                            else (
                                "혼잡도가 낮은 시간대로 배치했지만 당일 혼잡을 재확인해야 함"
                                if request.crowd_preferences.avoid_crowds == "high"
                                else "혼잡·영업시간·입장 조건은 당일 재확인 필요"
                            )
                        ),
                        rain_alternative=(
                            "필수 장소 — 우천 시 운영 여부를 확인하고 시간만 조정"
                            if place.id in must_visit_ids and not place.rain_suitable
                            else ("우천 시에도 이용 가능한 후보" if place.rain_suitable else "우천 시 실내 카페·박물관 후보로 교체")
                        ),
                        maps_url=place.maps_url,
                    )
                )
                previous = place
                previous_end = end_minutes
            daily_place_cost = sum(stop.place_cost_krw for stop in stops)
            daily_parking_cost = sum(stop.parking_cost_krw for stop in stops)
            driving_distance = sum(stop.transfer_distance_km for stop in stops)
            rental_car = request.ground_transport.mode == "rental_car"
            if rental_car and stops:
                hotel_to_first = haversine_km(selected_stay.latitude, selected_stay.longitude, stops[0].latitude, stops[0].longitude)
                last_to_hotel = haversine_km(stops[-1].latitude, stops[-1].longitude, selected_stay.latitude, selected_stay.longitude)
                driving_distance += hotel_to_first + last_to_hotel
            fuel_efficiency_km_l = 9.3 if request.ground_transport.sports_model_preferred else 11.0
            fuel_price_krw_l = 2_100 if request.destination_country == "US" else 1_750
            daily_fuel_cost = round(driving_distance / fuel_efficiency_km_l * fuel_price_krw_l) if rental_car else 0
            nightly_parking = selected_stay.parking_cost_krw_per_night or 0
            if rental_car and day_index < day_count - 1:
                daily_parking_cost += nightly_parking
            rental_daily_cost = (140_000 if request.ground_transport.sports_model_preferred else 90_000) if rental_car else 0
            daily_transport_cost = sum(stop.transfer_cost_krw for stop in stops) + daily_fuel_cost + daily_parking_cost + rental_daily_cost
            daily_cost = daily_place_cost + daily_transport_cost
            notes = []
            if day_index == 0:
                notes.append("입국·공항 이동 지연을 고려해 오후부터 시작")
            if district_name and not district_name.startswith("geo:"):
                notes.append(f"권역 중심 동선: {district_name}")
            if day_index == day_count - 1:
                notes.append("공항 이동과 출국 수속 시간을 별도로 확보")
            days.append(
                ItineraryDay(
                    date=current_date,
                    title=f"{day_index + 1}일차 · {name}",
                    local_timezone=cfg["timezone"],
                    stops=stops,
                    place_cost_krw=daily_place_cost,
                    local_transport_cost_krw=daily_transport_cost,
                    driving_distance_km=round(driving_distance, 1),
                    fuel_cost_krw=daily_fuel_cost,
                    parking_cost_krw=daily_parking_cost,
                    daily_cost_krw=daily_cost,
                    notes=notes,
                )
            )
        place_cost = sum(day.place_cost_krw for day in days)
        local_transport_cost = sum(day.local_transport_cost_krw for day in days)
        fuel_cost = sum(day.fuel_cost_krw for day in days)
        parking_cost = sum(day.parking_cost_krw for day in days)
        rental_cost = (140_000 if request.ground_transport.sports_model_preferred else 90_000) * day_count if request.ground_transport.mode == "rental_car" else 0
        local_cost = place_cost + local_transport_cost
        excluded_costs = ["공항↔숙소 이동", "보험·eSIM·쇼핑 등 선택 지출"]
        if selected_flight.taxes_included is not True:
            excluded_costs.append("항공 세금·수수료 중 공급자가 포함 여부를 확정하지 않은 금액")
        if selected_stay.taxes_included is not True:
            excluded_costs.append("숙소 세금·리조트피 중 공급자가 포함 여부를 확정하지 않은 금액")
        variants.append(
            ItineraryVariant(
                id=variant_id,
                name=name,
                summary=summary,
                pros=pros,
                cons=cons,
                days=days,
                flight_cost_krw=selected_flight.total_price_krw,
                stay_cost_krw=selected_stay.total_price_krw,
                place_cost_krw=place_cost,
                local_transport_cost_krw=local_transport_cost,
                rental_cost_krw=rental_cost,
                fuel_cost_krw=fuel_cost,
                parking_cost_krw=parking_cost,
                local_cost_krw=local_cost,
                trip_total_krw=selected_flight.total_price_krw + selected_stay.total_price_krw + local_cost,
                cost_assumptions=[
                    f"장소비는 성인 {request.adults}명과 아동 {request.children}명(성인의 70%) 기준",
                    (
                        f"렌터카는 1일 {140_000 if request.ground_transport.sports_model_preferred else 90_000:,}원 계획값, "
                        f"연비 {9.3 if request.ground_transport.sports_model_preferred else 11.0}km/L 기준"
                        if request.ground_transport.mode == "rental_car"
                        else f"대중교통은 탑승 1회당 {transit_per_boarding:,}원 상당으로 추정"
                    ),
                    (
                        "숙소 출발·복귀 거리와 장소·숙소 주차비를 포함"
                        if request.ground_transport.mode == "rental_car"
                        else "도보는 0원, 첫 장소까지의 숙소 출발 이동은 미포함"
                    ),
                ],
                excluded_costs=excluded_costs,
                selected_flight_id=selected_flight.id,
                selected_stay_id=selected_stay.id,
            )
        )
    return variants
