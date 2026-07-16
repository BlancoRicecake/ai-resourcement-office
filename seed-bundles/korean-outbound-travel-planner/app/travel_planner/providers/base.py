from __future__ import annotations

from abc import ABC, abstractmethod

from ..models import FlightOffer, PlaceCandidate, StayOffer, TripRequest


def normalize_accommodation_type(value: object, country: str) -> str:
    text = str(value or "").lower().replace("_", " ")
    mappings = [
        (("motel",), "motel"),
        (("hostel",), "hostel"),
        (("guesthouse", "guest house"), "guesthouse"),
        (("ryokan", "japanese style"), "ryokan"),
        (("apartment", "serviced apartment"), "apartment"),
        (("vacation rental", "holiday home", "villa"), "vacation_rental"),
        (("hotel", "resort", "inn"), "hotel"),
    ]
    for needles, normalized in mappings:
        if any(needle in text for needle in needles):
            return normalized
    return "ryokan" if country == "JP" and "traditional" in text else "hotel"


class TravelInventoryProvider(ABC):
    name: str

    @abstractmethod
    async def search_flights(self, request: TripRequest) -> list[FlightOffer]: ...

    @abstractmethod
    async def search_stays(self, request: TripRequest) -> list[StayOffer]: ...


class PlaceRouteProvider(ABC):
    name: str

    @abstractmethod
    async def search_places(self, request: TripRequest) -> list[PlaceCandidate]: ...

    @abstractmethod
    async def route_matrix(
        self, places: list[PlaceCandidate], mode: str = "TRANSIT"
    ) -> dict[tuple[str, str], tuple[int, float]]: ...


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def extract_constraints(self, text: str) -> dict | None: ...

    @abstractmethod
    async def summarize(self, normalized_payload: dict) -> str | None: ...
