from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from .base import TravelInventoryProvider, normalize_accommodation_type
from .sample import city_config
from ..config import Settings
from ..models import FlightOffer, StayOffer, TripRequest


BOOKING_AIRPORTS = {"TYO": "HND", "OSA": "KIX", "NYC": "JFK", "LAX": "LAX"}


def _amount(value) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    if isinstance(value, dict):
        for key in ("book", "total", "amount", "value", "accommodation", "base"):
            if key in value:
                found = _amount(value[key])
                if found:
                    return found
    return 0.0


def _first_text(value, fallback: str) -> str:
    if isinstance(value, str) and value:
        return value
    if isinstance(value, dict):
        for key in ("name", "text", "description"):
            if isinstance(value.get(key), str) and value[key]:
                return value[key]
    return fallback


class BookingProvider(TravelInventoryProvider):
    name = "booking"

    def __init__(self, settings: Settings):
        self.settings = settings

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.booking_api_key}",
            "X-Affiliate-Id": self.settings.booking_affiliate_id,
            "Content-Type": "application/json",
        }

    async def search_flights(self, request: TripRequest) -> list[FlightOffer]:
        # Demand API does not expose a consumer flight-search vertical in this bundle.
        return []

    async def _city_id(self, client: httpx.AsyncClient, request: TripRequest) -> int:
        cfg = city_config(request)
        airport = BOOKING_AIRPORTS.get(request.destination_code or cfg["code"], request.destination_code or cfg["code"])
        response = await client.post(
            f"{self.settings.booking_base_url}/common/locations/cities",
            headers=self._headers(),
            json={"airport": airport, "languages": ["ko", "en-gb"], "rows": 10},
        )
        response.raise_for_status()
        cities = response.json().get("data", [])
        if not cities:
            raise RuntimeError("Booking.com city id not found")
        target = request.destination_city.lower()
        for city in cities:
            text = str(city).lower()
            if target in text:
                return int(city["id"])
        return int(cities[0]["id"])

    async def search_stays(self, request: TripRequest) -> list[StayOffer]:
        async with httpx.AsyncClient(timeout=30) as client:
            city_id = await self._city_id(client, request)
            response = await client.post(
                f"{self.settings.booking_base_url}/accommodations/search",
                headers=self._headers(),
                json={
                    "booker": {"country": "kr", "platform": "desktop"},
                    "checkin": request.departure_date.isoformat(),
                    "checkout": request.return_date.isoformat(),
                    "city": city_id,
                    "currency": "KRW",
                    "extras": ["extra_charges", "products"],
                    "guests": {
                        "number_of_adults": request.adults,
                        "number_of_children": request.children,
                        "number_of_rooms": request.rooms,
                    },
                    "rows": 20,
                },
            )
            response.raise_for_status()
            rows = response.json().get("data", [])
        cfg = city_config(request)
        observed = datetime.now(timezone.utc)
        results = []
        for raw in rows:
            products = raw.get("products") or []
            product = products[0] if products else {}
            price = product.get("price") or raw.get("price") or {}
            total = _amount(price)
            if total <= 0:
                continue
            currency = price.get("currency", raw.get("currency", "KRW")) if isinstance(price, dict) else "KRW"
            total_krw = round(total) if currency == "KRW" else round(total * (1380 if currency == "USD" else 9.2))
            accommodation_id = str(raw.get("id", raw.get("accommodation", "unknown")))
            coordinates = raw.get("coordinates") or raw.get("location") or {}
            cancellation = product.get("policies", {}).get("cancellation") or raw.get("cancellation")
            deep_link = raw.get("deep_link_url") or raw.get("url") or product.get("deep_link_url")
            results.append(
                StayOffer(
                    id=f"booking-{accommodation_id}-{product.get('id', 'best')}",
                    provider="Booking.com",
                    name=_first_text(raw.get("name"), f"Booking.com 숙소 {accommodation_id}"),
                    accommodation_type=normalize_accommodation_type(raw.get("accommodation_type"), request.destination_country),
                    address=_first_text(raw.get("address"), request.destination_city),
                    latitude=float(coordinates.get("latitude", cfg["lat"])),
                    longitude=float(coordinates.get("longitude", cfg["lng"])),
                    total_price=total,
                    currency=currency,
                    total_price_krw=total_krw,
                    taxes_included=None,
                    rooms_requested=request.rooms,
                    available=True,
                    room_description=_first_text(product.get("room"), "Booking.com 최저가 객실"),
                    cancellation_policy=_first_text(cancellation, "예약 페이지에서 확인"),
                    rating=raw.get("review_score") or raw.get("rating"),
                    review_count=raw.get("review_count"),
                    booking_url=deep_link or f"https://www.booking.com/searchresults.ko.html?ss={quote_plus(request.destination_city)}",
                    observed_at=observed,
                    verified_inventory=True,
                )
            )
        return results
