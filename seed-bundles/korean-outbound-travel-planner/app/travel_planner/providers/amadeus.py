from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import httpx

from .base import TravelInventoryProvider
from .sample import city_config
from ..config import Settings
from ..models import FlightOffer, FlightSegment, StayOffer, TripRequest


def duration_minutes(value: str) -> int:
    match = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?", value or "")
    if not match:
        return 0
    days, hours, minutes = (int(part or 0) for part in match.groups())
    return days * 1440 + hours * 60 + minutes


class AmadeusProvider(TravelInventoryProvider):
    name = "amadeus"

    def __init__(self, settings: Settings):
        self.settings = settings
        self._token: str | None = None

    async def _headers(self, client: httpx.AsyncClient) -> dict[str, str]:
        if not self._token:
            response = await client.post(
                f"{self.settings.amadeus_base_url}/v1/security/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.amadeus_client_id,
                    "client_secret": self.settings.amadeus_client_secret,
                },
            )
            response.raise_for_status()
            self._token = response.json()["access_token"]
        return {"Authorization": f"Bearer {self._token}"}

    async def search_flights(self, request: TripRequest) -> list[FlightOffer]:
        cfg = city_config(request)
        destination = request.destination_code or cfg["code"]
        params = {
            "originLocationCode": request.origin_airport,
            "destinationLocationCode": destination,
            "departureDate": request.departure_date.isoformat(),
            "returnDate": request.return_date.isoformat(),
            "adults": request.adults,
            "children": request.children or None,
            "travelClass": request.cabin_class,
            "currencyCode": "KRW",
            "max": 12,
        }
        async with httpx.AsyncClient(timeout=25) as client:
            headers = await self._headers(client)
            response = await client.get(
                f"{self.settings.amadeus_base_url}/v2/shopping/flight-offers",
                params={key: value for key, value in params.items() if value is not None},
                headers=headers,
            )
            response.raise_for_status()
            payload = response.json()
        carriers = payload.get("dictionaries", {}).get("carriers", {})
        observed = datetime.now(timezone.utc)
        results: list[FlightOffer] = []
        for item in payload.get("data", []):
            segments: list[FlightSegment] = []
            stops = 0
            airport_change = False
            previous_destination = None
            for itinerary in item.get("itineraries", []):
                itinerary_segments = itinerary.get("segments", [])
                stops += max(0, len(itinerary_segments) - 1)
                for raw in itinerary_segments:
                    origin = raw["departure"]["iataCode"]
                    if previous_destination and previous_destination != origin:
                        airport_change = True
                    arrival_code = raw["arrival"]["iataCode"]
                    previous_destination = arrival_code
                    carrier_code = raw.get("carrierCode", "")
                    segments.append(
                        FlightSegment(
                            origin=origin,
                            destination=arrival_code,
                            departure_at=datetime.fromisoformat(raw["departure"]["at"]),
                            arrival_at=datetime.fromisoformat(raw["arrival"]["at"]),
                            carrier=carriers.get(carrier_code, carrier_code),
                            flight_number=f"{carrier_code}{raw.get('number', '')}",
                            duration_minutes=duration_minutes(raw.get("duration", "")),
                        )
                    )
            bag_quantities = []
            for traveler in item.get("travelerPricings", []):
                for detail in traveler.get("fareDetailsBySegment", []):
                    bags = detail.get("includedCheckedBags", {})
                    if "quantity" in bags:
                        bag_quantities.append(int(bags["quantity"]))
            baggage = "unknown" if not bag_quantities else ("included" if min(bag_quantities) > 0 else "excluded")
            price = item.get("price", {})
            total = float(price.get("grandTotal", price.get("total", 0)))
            currency = price.get("currency", "KRW")
            total_krw = round(total) if currency == "KRW" else round(total * (1380 if currency == "USD" else 9.2))
            total_duration = sum(duration_minutes(it.get("duration", "")) for it in item.get("itineraries", []))
            results.append(
                FlightOffer(
                    id=f"amadeus-{item['id']}",
                    provider="Amadeus",
                    total_price=total,
                    currency=currency,
                    total_price_krw=total_krw,
                    taxes_included=True,
                    baggage_status=baggage,
                    stops=stops,
                    airport_change=airport_change,
                    duration_minutes=total_duration,
                    change_policy="운임 규정은 예약 페이지에서 최종 확인",
                    cancellation_policy="운임 규정은 예약 페이지에서 최종 확인",
                    segments=segments,
                    booking_url=f"https://www.google.com/travel/flights?q={quote_plus(request.origin_airport + ' to ' + destination + ' ' + str(request.departure_date))}",
                    observed_at=observed,
                )
            )
        return results

    async def search_stays(self, request: TripRequest) -> list[StayOffer]:
        cfg = city_config(request)
        city_code = request.destination_code or cfg["code"]
        async with httpx.AsyncClient(timeout=30) as client:
            headers = await self._headers(client)
            hotel_list_response = await client.get(
                f"{self.settings.amadeus_base_url}/v1/reference-data/locations/hotels/by-city",
                params={"cityCode": city_code, "radius": 20, "radiusUnit": "KM", "hotelSource": "ALL"},
                headers=headers,
            )
            hotel_list_response.raise_for_status()
            hotels = hotel_list_response.json().get("data", [])[:16]
            hotel_ids = [hotel["hotelId"] for hotel in hotels]
            if not hotel_ids:
                return []
            offer_response = await client.get(
                f"{self.settings.amadeus_base_url}/v3/shopping/hotel-offers",
                params={
                    "hotelIds": ",".join(hotel_ids),
                    "adults": request.adults + request.children,
                    "checkInDate": request.departure_date.isoformat(),
                    "checkOutDate": request.return_date.isoformat(),
                    "roomQuantity": request.rooms,
                    "currency": "KRW",
                    "bestRateOnly": "true",
                },
                headers=headers,
            )
            offer_response.raise_for_status()
            data = offer_response.json().get("data", [])
        observed = datetime.now(timezone.utc)
        results = []
        for item in data:
            hotel = item.get("hotel", {})
            offers = item.get("offers", [])
            if not offers:
                continue
            offer = offers[0]
            price = offer.get("price", {})
            total = float(price.get("total", 0))
            currency = price.get("currency", "KRW")
            total_krw = round(total) if currency == "KRW" else round(total * (1380 if currency == "USD" else 9.2))
            policies = offer.get("policies", {})
            cancellation = policies.get("cancellation", {}).get("description", {}).get("text", "확인 필요")
            room = offer.get("room", {})
            results.append(
                StayOffer(
                    id=f"amadeus-{offer.get('id', hotel.get('hotelId'))}",
                    provider="Amadeus",
                    name=hotel.get("name", "이름 확인 필요"),
                    accommodation_type="hotel",
                    address=request.destination_city,
                    latitude=float(hotel.get("latitude", cfg["lat"])),
                    longitude=float(hotel.get("longitude", cfg["lng"])),
                    total_price=total,
                    currency=currency,
                    total_price_krw=total_krw,
                    taxes_included=all(tax.get("included", False) for tax in price.get("taxes", [])) if price.get("taxes") else None,
                    rooms_requested=request.rooms,
                    available=bool(item.get("available", True)),
                    room_description=room.get("description", {}).get("text", "객실 설명 확인 필요"),
                    cancellation_policy=cancellation,
                    booking_url=f"https://www.google.com/travel/hotels/{quote_plus(hotel.get('name', request.destination_city))}",
                    observed_at=observed,
                )
            )
        return results

