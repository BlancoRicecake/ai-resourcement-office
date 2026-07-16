from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from .base import TravelInventoryProvider, normalize_accommodation_type
from .sample import city_config
from ..config import Settings
from ..models import FlightOffer, StayOffer, TripRequest


def _price(price) -> float:
    if isinstance(price, (int, float, str)):
        try:
            return float(price)
        except ValueError:
            return 0.0
    if not isinstance(price, dict):
        return 0.0
    amount = float(price.get("amount", price.get("value", 0)) or 0)
    if price.get("unit") in {"PRICE_UNIT_MILLI", "MILLI"}:
        amount /= 1000
    return amount


def _values(value) -> list[dict]:
    if isinstance(value, dict):
        return list(value.values())
    return value if isinstance(value, list) else []


class SkyscannerProvider(TravelInventoryProvider):
    name = "skyscanner"

    def __init__(self, settings: Settings):
        self.settings = settings

    @property
    def headers(self) -> dict[str, str]:
        return {"x-api-key": self.settings.skyscanner_api_key, "Content-Type": "application/json"}

    async def _poll(self, client: httpx.AsyncClient, path: str, created: dict) -> dict:
        payload = created
        token = created.get("sessionToken")
        for _ in range(3):
            status = str(payload.get("status", "")).lower()
            if not token or status.endswith(("complete", "completed")):
                break
            response = await client.post(
                f"{self.settings.skyscanner_base_url}{path}/{token}", headers=self.headers, json={}
            )
            response.raise_for_status()
            payload = response.json()
        return payload

    async def search_flights(self, request: TripRequest) -> list[FlightOffer]:
        cabin = f"CABIN_CLASS_{request.cabin_class}"
        destination_code = request.destination_code or city_config(request)["code"]
        legs = [
            {
                "originPlaceId": {"iata": request.origin_airport},
                "destinationPlaceId": {"iata": destination_code},
                "date": {"year": request.departure_date.year, "month": request.departure_date.month, "day": request.departure_date.day},
            },
            {
                "originPlaceId": {"iata": destination_code},
                "destinationPlaceId": {"iata": request.origin_airport},
                "date": {"year": request.return_date.year, "month": request.return_date.month, "day": request.return_date.day},
            },
        ]
        body = {
            "query": {
                "market": "KR",
                "locale": "ko-KR",
                "currency": "KRW",
                "queryLegs": legs,
                "adults": request.adults,
                "childrenAges": request.traveler_ages,
                "cabinClass": cabin,
            }
        }
        async with httpx.AsyncClient(timeout=35) as client:
            response = await client.post(
                f"{self.settings.skyscanner_base_url}/apiservices/v3/flights/live/search/create",
                headers=self.headers,
                json=body,
            )
            response.raise_for_status()
            payload = await self._poll(client, "/apiservices/v3/flights/live/search/poll", response.json())
        content = payload.get("content", {})
        results = content.get("results", {})
        legs_by_id = results.get("legs", {})
        observed = datetime.now(timezone.utc)
        offers = []
        for itinerary in _values(results.get("itineraries", {})):
            leg_items = [legs_by_id.get(leg_id, {}) for leg_id in itinerary.get("legIds", [])]
            options = itinerary.get("pricingOptions") or []
            if not options:
                continue
            option = min(options, key=lambda item: _price(item.get("price")))
            total = _price(option.get("price"))
            if total <= 0:
                continue
            items = option.get("items") or []
            deep_link = items[0].get("deepLink") if items else None
            duration = sum(int(leg.get("durationInMinutes", 0)) for leg in leg_items)
            stops = sum(int(leg.get("stopCount", max(0, len(leg.get("segmentIds", [])) - 1))) for leg in leg_items)
            offers.append(
                FlightOffer(
                    id=f"skyscanner-{itinerary.get('id', len(offers))}",
                    provider="Skyscanner",
                    total_price=total,
                    currency="KRW",
                    total_price_krw=round(total),
                    taxes_included=None,
                    baggage_status="unknown",
                    stops=stops,
                    airport_change=False,
                    duration_minutes=duration,
                    change_policy="공급자 예약 페이지에서 확인",
                    cancellation_policy="공급자 예약 페이지에서 확인",
                    booking_url=deep_link or f"https://www.skyscanner.co.kr/transport/flights/{request.origin_airport.lower()}/{destination_code.lower()}/",
                    observed_at=observed,
                )
            )
        return offers

    async def _hotel_entity_id(self, client: httpx.AsyncClient, request: TripRequest) -> str:
        response = await client.post(
            f"{self.settings.skyscanner_base_url}/apiservices/v3/autosuggest/hotels",
            headers=self.headers,
            json={
                "query": {
                    "market": "KR",
                    "locale": "ko-KR",
                    "searchTerm": request.destination_city,
                    "includedEntityTypes": ["PLACE_TYPE_CITY"],
                },
                "limit": 5,
            },
        )
        response.raise_for_status()
        places = response.json().get("places", [])
        if not places:
            raise RuntimeError("Skyscanner hotel entity id not found")
        return places[0]["entityId"]

    async def search_stays(self, request: TripRequest) -> list[StayOffer]:
        async with httpx.AsyncClient(timeout=35) as client:
            entity_id = await self._hotel_entity_id(client, request)
            response = await client.post(
                f"{self.settings.skyscanner_base_url}/apiservices/v1/hotels/live/search/create",
                headers=self.headers,
                json={
                    "query": {
                        "market": "KR",
                        "locale": "ko-KR",
                        "currency": "KRW",
                        "entityId": entity_id,
                        "checkinDate": {"year": request.departure_date.year, "month": request.departure_date.month, "day": request.departure_date.day},
                        "checkoutDate": {"year": request.return_date.year, "month": request.return_date.month, "day": request.return_date.day},
                        "adults": request.adults,
                        "childrenAges": request.traveler_ages,
                        "rooms": request.rooms,
                    },
                    "initialPageSize": 20,
                },
            )
            response.raise_for_status()
            payload = await self._poll(client, "/apiservices/v1/hotels/live/search/poll", response.json())
        content = payload.get("content", {})
        results = content.get("results", content)
        pricing = _values(results.get("hotelsPricingOptions", {}))
        hotel_content = results.get("hotelContent", content.get("hotelContent", {}))
        cfg = city_config(request)
        observed = datetime.now(timezone.utc)
        offers = []
        for raw in pricing:
            total = _price(raw.get("price"))
            if total <= 0:
                continue
            hotel_id = str(raw.get("hotelId", raw.get("id", "unknown")))
            details = hotel_content.get(hotel_id, {}) if isinstance(hotel_content, dict) else {}
            location = details.get("location", {})
            deep_link = raw.get("deepLink") or raw.get("deeplink")
            rating = details.get("guestRating", details.get("rating"))
            if isinstance(rating, dict):
                rating = rating.get("score")
            offers.append(
                StayOffer(
                    id=f"skyscanner-{raw.get('id', hotel_id)}",
                    provider="Skyscanner",
                    name=details.get("hotelName", details.get("name", f"Skyscanner 숙소 {hotel_id}")),
                    accommodation_type=normalize_accommodation_type(details.get("type"), request.destination_country),
                    address=details.get("address", request.destination_city),
                    latitude=float(location.get("latitude", cfg["lat"])),
                    longitude=float(location.get("longitude", cfg["lng"])),
                    total_price=total,
                    currency="KRW",
                    total_price_krw=round(total),
                    taxes_included=None,
                    rooms_requested=request.rooms,
                    available=True,
                    room_description=raw.get("roomName", "기본 객실"),
                    cancellation_policy=str(raw.get("cancellationPolicy", "예약 페이지에서 확인")),
                    rating=rating,
                    review_count=details.get("reviewCount"),
                    booking_url=deep_link or f"https://www.skyscanner.co.kr/hotels/{quote_plus(request.destination_city)}",
                    observed_at=observed,
                    verified_inventory=True,
                )
            )
        return offers
