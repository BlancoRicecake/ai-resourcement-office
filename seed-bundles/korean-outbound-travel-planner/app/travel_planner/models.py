from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


CountryCode = str
Pace = Literal["balanced", "budget", "relaxed"]
DataMode = Literal["live", "mixed", "guided_research", "sample"]
ConfidenceGrade = Literal["A", "B", "C", "D", "E"]
ValueStatus = Literal["exact", "reference", "range", "estimated", "unknown"]
ConstraintSource = Literal["explicit", "inferred", "default", "delegated"]
ConstraintStatus = Literal["confirmed", "proposed", "unknown"]
ConstraintHardness = Literal["hard", "soft"]
ReadinessStatus = Literal["blocked", "preview_ready", "search_ready", "complete"]
DestinationSupportStatus = Literal["researching", "provisional", "validated", "unavailable"]
ResearchTaskStatus = Literal["ready", "pending", "blocked"]


class EvidenceRecord(BaseModel):
    id: str
    title: str
    source_name: str
    source_url: str
    source_type: Literal[
        "live_api",
        "official_site",
        "comparison_platform",
        "planning_baseline",
        "editorial",
        "community",
    ]
    confidence: ConfidenceGrade
    value_status: ValueStatus
    observed_at: datetime | None = None
    note: str
    verification_required: bool = True


class VerificationLink(BaseModel):
    category: Literal["flight", "stay", "place", "route", "official"]
    platform: str
    title: str
    url: str
    note: str
    priority: int = Field(default=100, ge=1)


class DestinationSource(BaseModel):
    category: Literal["entry", "safety", "tourism", "airport", "transport", "pricing", "map"]
    name: str
    url: str
    source_type: Literal["official_site", "comparison_platform", "search_guide"] = "official_site"
    status: Literal["verified", "pending"] = "pending"
    observed_at: datetime | None = None
    note: str = ""


class DestinationResearchTask(BaseModel):
    key: str
    label: str
    status: ResearchTaskStatus = "pending"
    reason: str


class DestinationCapabilities(BaseModel):
    flight: Literal["live", "guided", "unavailable"] = "guided"
    stay: Literal["live", "guided", "unavailable"] = "guided"
    places: Literal["live", "guided", "unavailable"] = "guided"
    routes: Literal["live", "guided", "unavailable"] = "guided"


class DestinationPack(BaseModel):
    slug: str
    country_code: str = Field(min_length=2, max_length=2)
    country_name: str
    city_name: str
    city_code: str | None = Field(default=None, min_length=3, max_length=3)
    aliases: list[str] = Field(default_factory=list)
    currency: str | None = None
    timezone: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    summary: str = ""
    status: DestinationSupportStatus = "researching"
    capabilities: DestinationCapabilities = Field(default_factory=DestinationCapabilities)
    sources: list[DestinationSource] = Field(default_factory=list)
    research_tasks: list[DestinationResearchTask] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_verified_at: datetime | None = None


class DestinationBootstrapRequest(BaseModel):
    query: str = Field(min_length=2, max_length=120)


class TravelerProfile(BaseModel):
    budget_krw: int | None = Field(default=None, ge=0)
    stay_types: list[str] = Field(default_factory=lambda: ["hotel"])
    pace: Pace = "balanced"
    interests: list[str] = Field(default_factory=list)
    dietary_needs: list[str] = Field(default_factory=list)
    mobility_needs: list[str] = Field(default_factory=list)
    consent_to_store: bool = False
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FlightPreferences(BaseModel):
    max_stops: int | None = Field(default=None, ge=0, le=3)
    direct_required: bool = False
    baggage_required: bool | None = None


class StayPreferences(BaseModel):
    bed_count: int | None = Field(default=None, ge=1, le=8)
    bed_type: str | None = None
    parking_required: bool = False
    required_amenities: list[str] = Field(default_factory=list)


class GroundTransportPreferences(BaseModel):
    mode: Literal["undecided", "transit", "rental_car", "mixed"] = "undecided"
    rental_class: str | None = None
    sports_model_preferred: bool = False
    driver_age: int | None = Field(default=None, ge=18, le=99)
    parking_required: bool = False


class DiningPreferences(BaseModel):
    special_meals_per_day: int = Field(default=0, ge=0, le=3)
    special_meal_budget_krw: int | None = Field(default=None, ge=0)


class CrowdPreferences(BaseModel):
    avoid_crowds: Literal["low", "medium", "high"] = "low"
    must_visit_places: list[str] = Field(default_factory=list)


class TripRequest(BaseModel):
    destination_country: CountryCode
    destination_city: str = Field(min_length=2, max_length=80)
    destination_code: str | None = Field(default=None, min_length=3, max_length=3)
    origin_airport: str = Field(default="ICN", min_length=3, max_length=3)
    departure_date: date
    return_date: date
    date_flexibility_days: int = Field(default=0, ge=0, le=7)
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=8)
    traveler_ages: list[int] = Field(default_factory=list)
    rooms: int = Field(default=1, ge=1, le=5)
    budget_krw: int = Field(default=2_000_000, ge=100_000)
    checked_baggage: bool = False
    cabin_class: Literal["ECONOMY", "PREMIUM_ECONOMY", "BUSINESS"] = "ECONOMY"
    stay_types: list[str] = Field(default_factory=lambda: ["hotel"])
    pace: Pace = "balanced"
    interests: list[str] = Field(default_factory=lambda: ["명소", "현지 음식"])
    dietary_needs: list[str] = Field(default_factory=list)
    mobility_needs: list[str] = Field(default_factory=list)
    must_visit_places: list[str] = Field(default_factory=list)
    flight_preferences: FlightPreferences = Field(default_factory=FlightPreferences)
    stay_preferences: StayPreferences = Field(default_factory=StayPreferences)
    ground_transport: GroundTransportPreferences = Field(default_factory=GroundTransportPreferences)
    dining_preferences: DiningPreferences = Field(default_factory=DiningPreferences)
    crowd_preferences: CrowdPreferences = Field(default_factory=CrowdPreferences)
    save_profile: bool = False

    @field_validator("destination_code", "origin_airport")
    @classmethod
    def uppercase_iata(cls, value: str | None) -> str | None:
        return value.upper() if value else value

    @field_validator("destination_country")
    @classmethod
    def normalize_country_code(cls, value: str) -> str:
        normalized = value.strip().upper()
        if len(normalized) != 2 or not normalized.isalpha():
            raise ValueError("목적지 국가는 ISO 2자리 코드여야 합니다.")
        return normalized

    @field_validator("stay_types")
    @classmethod
    def require_stay_type(cls, value: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(item.strip().lower() for item in value if item.strip()))
        if not normalized:
            raise ValueError("숙소 유형을 하나 이상 선택해야 합니다.")
        return normalized

    @field_validator("must_visit_places")
    @classmethod
    def normalize_must_visits(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(item.strip() for item in value if item.strip()))

    @model_validator(mode="after")
    def validate_trip(self) -> "TripRequest":
        if self.return_date <= self.departure_date:
            raise ValueError("귀국일은 출국일 이후여야 합니다.")
        if (self.return_date - self.departure_date).days > 30:
            raise ValueError("v1은 최대 30일 여행을 지원합니다.")
        if self.children and self.traveler_ages and len(self.traveler_ages) != self.children:
            raise ValueError("아동 나이는 아동 수와 같아야 합니다.")
        if self.flight_preferences.direct_required:
            self.flight_preferences.max_stops = 0
        combined_must_visits = [*self.must_visit_places, *self.crowd_preferences.must_visit_places]
        self.must_visit_places = list(dict.fromkeys(item.strip() for item in combined_must_visits if item.strip()))
        if self.checked_baggage and self.flight_preferences.baggage_required is None:
            self.flight_preferences.baggage_required = True
        if self.ground_transport.parking_required:
            self.stay_preferences.parking_required = True
        return self


class ConstraintValue(BaseModel):
    key: str
    value: Any = None
    source: ConstraintSource = "inferred"
    status: ConstraintStatus = "proposed"
    hardness: ConstraintHardness = "soft"
    confidence: float = Field(default=0.5, ge=0, le=1)
    reason: str = ""
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QuestionOption(BaseModel):
    label: str
    value: str
    description: str = ""
    recommended: bool = False


class QuestionCard(BaseModel):
    id: str
    key: str
    prompt: str
    why_asked: str
    options: list[QuestionOption] = Field(default_factory=list, max_length=3)
    allow_free_text: bool = True


class PlanningMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanningPreview(BaseModel):
    headline: str
    summary: str
    destination_candidates: list[dict[str, str]] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    ready_sections: list[str] = Field(default_factory=list)
    destination_status: DestinationSupportStatus | None = None
    research_tasks: list[DestinationResearchTask] = Field(default_factory=list)
    research_sources: list[DestinationSource] = Field(default_factory=list)


class PlanningSession(BaseModel):
    id: str
    locale: str = "ko-KR"
    timezone: str = "Asia/Seoul"
    constraints: dict[str, ConstraintValue] = Field(default_factory=dict)
    messages: list[PlanningMessage] = Field(default_factory=list)
    asked_question_ids: list[str] = Field(default_factory=list)
    readiness: dict[str, ReadinessStatus] = Field(default_factory=dict)
    next_questions: list[QuestionCard] = Field(default_factory=list, max_length=3)
    assumptions: list[str] = Field(default_factory=list)
    preview: PlanningPreview | None = None
    destination_pack: DestinationPack | None = None
    invalidated_sections: list[str] = Field(default_factory=list)
    final_trip_id: str | None = None
    consent_to_store: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PlanningSessionCreate(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    locale: str = "ko-KR"
    timezone: str = "Asia/Seoul"
    consent_to_store: bool = False


class PlanningMessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


class ConstraintChange(BaseModel):
    key: str
    value: Any = None
    hardness: ConstraintHardness | None = None
    confirmed: bool = True


class ConstraintPatch(BaseModel):
    changes: list[ConstraintChange] = Field(min_length=1, max_length=30)


class FlightSegment(BaseModel):
    origin: str
    destination: str
    departure_at: datetime
    arrival_at: datetime
    carrier: str
    flight_number: str
    duration_minutes: int


class FlightOffer(BaseModel):
    id: str
    provider: str
    total_price: float
    currency: str
    total_price_krw: int
    taxes_included: bool | None = None
    baggage_status: Literal["included", "excluded", "unknown"] = "unknown"
    stops: int = 0
    airport_change: bool = False
    duration_minutes: int
    change_policy: str = "확인 필요"
    cancellation_policy: str = "확인 필요"
    segments: list[FlightSegment] = Field(default_factory=list)
    booking_url: str
    observed_at: datetime
    is_stale: bool = False
    price_status: Literal["live", "web_reference", "estimated", "sample"] = "live"
    confidence: ConfidenceGrade = "A"
    score: float | None = None
    score_reasons: list[str] = Field(default_factory=list)


class StayOffer(BaseModel):
    id: str
    provider: str
    name: str
    accommodation_type: str
    address: str
    latitude: float
    longitude: float
    total_price: float
    currency: str
    total_price_krw: int
    taxes_included: bool | None = None
    rooms_requested: int
    available: bool
    room_description: str = "객실 설명 확인 필요"
    bed_count: int | None = None
    amenities: list[str] = Field(default_factory=list)
    parking_available: bool | None = None
    parking_cost_krw_per_night: int | None = None
    cancellation_policy: str = "확인 필요"
    rating: float | None = None
    review_count: int | None = None
    review_summary: str | None = None
    booking_url: str
    observed_at: datetime
    is_stale: bool = False
    verified_inventory: bool = True
    price_status: Literal["live", "web_reference", "estimated", "sample"] = "live"
    confidence: ConfidenceGrade = "A"
    score: float | None = None
    score_reasons: list[str] = Field(default_factory=list)


class PlaceCandidate(BaseModel):
    id: str
    provider: str
    name: str
    local_name: str | None = None
    category: Literal["attraction", "restaurant", "cafe", "park", "shopping", "other"]
    address: str
    latitude: float
    longitude: float
    rating: float | None = None
    review_count: int | None = None
    price_level: int | None = Field(default=None, ge=0, le=4)
    estimated_cost_krw: int = 0
    opening_hours: list[str] = Field(default_factory=list)
    weekday_hours: dict[int, list[str]] = Field(default_factory=dict)
    parking_cost_krw: int = 0
    business_status: str = "UNKNOWN"
    accessibility: list[str] = Field(default_factory=list)
    maps_url: str
    website_url: str | None = None
    observed_at: datetime
    interest_match: float = Field(default=0.5, ge=0, le=1)
    rain_suitable: bool = True
    district: str | None = None
    interest_tags: list[str] = Field(default_factory=list)
    visit_duration_minutes: int = Field(default=90, ge=30, le=480)
    confidence: ConfidenceGrade = "A"


class ItineraryStop(BaseModel):
    start_time: str
    end_time: str
    place_id: str
    place_name: str
    category: str
    transfer_mode: str
    transfer_minutes: int
    transfer_distance_km: float
    latitude: float
    longitude: float
    district: str | None = None
    unit_place_cost_krw: int = 0
    place_cost_krw: int = 0
    transfer_cost_krw: int = 0
    parking_cost_krw: int = 0
    estimated_cost_krw: int
    booking_required: bool
    reason: str
    drawback: str
    rain_alternative: str
    maps_url: str


class ItineraryDay(BaseModel):
    date: date
    title: str
    local_timezone: str
    stops: list[ItineraryStop]
    place_cost_krw: int = 0
    local_transport_cost_krw: int = 0
    driving_distance_km: float = 0
    fuel_cost_krw: int = 0
    parking_cost_krw: int = 0
    daily_cost_krw: int
    notes: list[str] = Field(default_factory=list)


class ItineraryVariant(BaseModel):
    id: Pace
    name: str
    summary: str
    pros: list[str]
    cons: list[str]
    days: list[ItineraryDay]
    flight_cost_krw: int = 0
    stay_cost_krw: int = 0
    place_cost_krw: int = 0
    local_transport_cost_krw: int = 0
    rental_cost_krw: int = 0
    fuel_cost_krw: int = 0
    parking_cost_krw: int = 0
    local_cost_krw: int
    trip_total_krw: int
    cost_assumptions: list[str] = Field(default_factory=list)
    excluded_costs: list[str] = Field(default_factory=list)
    selected_flight_id: str
    selected_stay_id: str


class TripResult(BaseModel):
    id: str
    status: Literal["ready", "partial", "failed"]
    request: TripRequest
    flights: list[FlightOffer]
    stays: list[StayOffer]
    places: list[PlaceCandidate]
    itineraries: list[ItineraryVariant]
    warnings: list[str] = Field(default_factory=list)
    unresolved_checks: list[str] = Field(default_factory=list)
    sample_mode: bool = False
    data_mode: DataMode = "live"
    sample_verticals: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    verification_links: list[VerificationLink] = Field(default_factory=list)
    narrative: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReplanRequest(BaseModel):
    closed_place_ids: list[str] = Field(default_factory=list)
    weather: str | None = None
    current_location: str | None = None
    notes: str | None = None


class ProviderHealth(BaseModel):
    name: str
    configured: bool
    mode: Literal["live", "research", "sample", "partner-unavailable"]
    detail: str
