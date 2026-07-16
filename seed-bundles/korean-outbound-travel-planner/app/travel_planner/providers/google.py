from __future__ import annotations

import json
from datetime import datetime, timezone

import httpx

from .base import PlaceRouteProvider
from ..config import Settings
from ..models import PlaceCandidate, TripRequest


PRICE_LEVELS = {
    "PRICE_LEVEL_FREE": 0,
    "PRICE_LEVEL_INEXPENSIVE": 1,
    "PRICE_LEVEL_MODERATE": 2,
    "PRICE_LEVEL_EXPENSIVE": 3,
    "PRICE_LEVEL_VERY_EXPENSIVE": 4,
}


class GooglePlaceRouteProvider(PlaceRouteProvider):
    name = "google"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def search_places(self, request: TripRequest) -> list[PlaceCandidate]:
        queries: list[tuple[str, str, list[str]]] = [
            (f"{request.destination_city} 주요 관광명소", "attraction", ["명소"]),
            (f"{request.destination_city} 현지 맛집", "restaurant", ["현지 음식"]),
            (f"{request.destination_city} 카페", "cafe", ["카페"]),
        ]
        for interest in request.interests[:3]:
            normalized = interest.strip()
            if not normalized:
                continue
            category = "restaurant" if any(word in normalized for word in ("음식", "맛집")) else "cafe" if "카페" in normalized else "attraction"
            queries.append((f"{request.destination_city} {normalized}", category, [normalized]))
        fields = ",".join(
            [
                "places.id",
                "places.displayName",
                "places.formattedAddress",
                "places.location",
                "places.rating",
                "places.userRatingCount",
                "places.priceLevel",
                "places.currentOpeningHours",
                "places.businessStatus",
                "places.googleMapsUri",
                "places.websiteUri",
                "places.accessibilityOptions",
                "places.types",
            ]
        )
        headers = {
            "X-Goog-Api-Key": self.settings.google_maps_api_key,
            "X-Goog-FieldMask": fields,
            "Content-Type": "application/json",
        }
        observed = datetime.now(timezone.utc)
        results: dict[str, PlaceCandidate] = {}
        async with httpx.AsyncClient(timeout=20) as client:
            for query, category, interest_tags in queries:
                response = await client.post(
                    "https://places.googleapis.com/v1/places:searchText",
                    headers=headers,
                    json={"textQuery": query, "languageCode": "ko", "maxResultCount": 6},
                )
                response.raise_for_status()
                for raw in response.json().get("places", []):
                    location = raw.get("location") or {}
                    place_id = raw.get("id")
                    if not place_id or "latitude" not in location:
                        continue
                    price_level = PRICE_LEVELS.get(raw.get("priceLevel"))
                    cost = {0: 0, 1: 12000, 2: 28000, 3: 55000, 4: 90000}.get(price_level, 0)
                    access = [key for key, value in (raw.get("accessibilityOptions") or {}).items() if value is True]
                    hours = (raw.get("currentOpeningHours") or {}).get("weekdayDescriptions", [])
                    display = raw.get("displayName", {}).get("text", "이름 확인 필요")
                    results[place_id] = PlaceCandidate(
                        id=f"google-{place_id}",
                        provider="Google Places",
                        name=display,
                        local_name=display,
                        category=category,
                        address=raw.get("formattedAddress", "주소 확인 필요"),
                        latitude=location["latitude"],
                        longitude=location["longitude"],
                        rating=raw.get("rating"),
                        review_count=raw.get("userRatingCount"),
                        price_level=price_level,
                        estimated_cost_krw=cost,
                        opening_hours=hours,
                        business_status=raw.get("businessStatus", "UNKNOWN"),
                        accessibility=access,
                        maps_url=raw.get("googleMapsUri", f"https://www.google.com/maps/place/?q=place_id:{place_id}"),
                        website_url=raw.get("websiteUri"),
                        observed_at=observed,
                        interest_match=0.95 if interest_tags[0] in request.interests else (0.8 if category in {"attraction", "restaurant"} else 0.65),
                        rain_suitable=category in {"restaurant", "cafe"},
                        interest_tags=interest_tags,
                        visit_duration_minutes=90 if category == "attraction" else 60,
                    )
        return list(results.values())

    async def route_matrix(
        self, places: list[PlaceCandidate], mode: str = "TRANSIT"
    ) -> dict[tuple[str, str], tuple[int, float]]:
        if not places:
            return {}
        waypoints = [
            {"waypoint": {"location": {"latLng": {"latitude": place.latitude, "longitude": place.longitude}}}}
            for place in places[:12]
        ]
        headers = {
            "X-Goog-Api-Key": self.settings.google_maps_api_key,
            "X-Goog-FieldMask": "originIndex,destinationIndex,duration,distanceMeters,status,condition",
            "Content-Type": "application/json",
        }
        payload = {
            "origins": waypoints,
            "destinations": waypoints,
            "travelMode": mode,
            "languageCode": "ko",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
        try:
            rows = response.json()
        except json.JSONDecodeError:
            rows = [json.loads(line) for line in response.text.splitlines() if line.strip()]
        if isinstance(rows, dict):
            rows = [rows]
        matrix = {}
        active = places[:12]
        for row in rows:
            origin_index = row.get("originIndex")
            destination_index = row.get("destinationIndex")
            if origin_index is None or destination_index is None or row.get("condition") == "ROUTE_NOT_FOUND":
                continue
            seconds = int(str(row.get("duration", "0s")).removesuffix("s") or 0)
            matrix[(active[origin_index].id, active[destination_index].id)] = (
                max(0, round(seconds / 60)),
                round(row.get("distanceMeters", 0) / 1000, 2),
            )
        return matrix
