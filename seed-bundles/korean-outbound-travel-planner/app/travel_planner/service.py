from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import uuid4

from .config import Settings
from .conversation import (
    apply_llm_constraints,
    apply_message,
    apply_patch,
    build_preview,
    build_trip_request,
    compute_readiness,
    create_session,
)
from .database import Database
from .destinations import DestinationRegistry
from .models import (
    ConstraintPatch,
    ConstraintValue,
    DestinationPack,
    EvidenceRecord,
    PlanningMessageRequest,
    PlanningSession,
    PlanningSessionCreate,
    ProviderHealth,
    ReplanRequest,
    TravelerProfile,
    TripRequest,
    TripResult,
)
from .optimizer import build_itineraries, match_must_visit_places, rank_flights, rank_stays
from .providers.amadeus import AmadeusProvider
from .providers.booking import BookingProvider
from .providers.google import GooglePlaceRouteProvider
from .providers.openai import OpenAILLMProvider
from .providers.sample import SampleProvider
from .providers.skyscanner import SkyscannerProvider
from .research import build_guided_research_evidence, build_verification_links


class TravelPlannerService:
    def __init__(self, settings: Settings, database: Database):
        self.settings = settings
        self.database = database
        self.sample = SampleProvider()
        self.amadeus = AmadeusProvider(settings)
        self.booking = BookingProvider(settings)
        self.skyscanner = SkyscannerProvider(settings)
        self.google = GooglePlaceRouteProvider(settings)
        self.llm = OpenAILLMProvider(settings)
        self.destinations = DestinationRegistry(database)
        self.sessions: dict[str, PlanningSession] = {}

    def _attach_destination_pack(self, session: PlanningSession) -> PlanningSession:
        city = session.constraints.get("destination_city")
        if not city or not city.value:
            return session
        pack = self.destinations.bootstrap(str(city.value))
        session.destination_pack = pack
        for key, value, reason in (
            ("destination_country", pack.country_code, "목적지 조사 팩의 국가 코드"),
            ("destination_code", pack.city_code, "목적지 조사 팩의 도시·공항 코드"),
            ("destination_slug", pack.slug, "목적지 조사 팩 연결"),
            ("destination_status", pack.status, "현재 목적지 지원·검증 상태"),
        ):
            if value is not None and (key not in session.constraints or key in {"destination_slug", "destination_status"}):
                session.constraints[key] = ConstraintValue(
                    key=key,
                    value=value,
                    source="inferred",
                    status="proposed",
                    confidence=0.95,
                    reason=reason,
                )
        session.readiness = compute_readiness(session)
        session.preview = build_preview(session)
        if session.preview:
            session.preview.destination_status = pack.status
            session.preview.research_tasks = pack.research_tasks
            session.preview.research_sources = pack.sources
        return session

    async def create_planning_session(self, payload: PlanningSessionCreate) -> PlanningSession:
        session = create_session(payload.message, payload.locale, payload.timezone, payload.consent_to_store)
        if self.settings.openai_enabled:
            try:
                apply_llm_constraints(session, await self.llm.extract_constraints(payload.message))
            except Exception:
                session.assumptions.append("자유문장 보강 분석에 실패해 결정론적 조건 추출 결과로 계속합니다.")
        self._attach_destination_pack(session)
        self.sessions[session.id] = session
        self.database.save_planning_session(session)
        return session

    def get_planning_session(self, session_id: str) -> PlanningSession | None:
        session = self.sessions.get(session_id) or self.database.get_planning_session(session_id)
        if session:
            self.sessions[session.id] = session
        return session

    async def add_planning_message(self, session_id: str, payload: PlanningMessageRequest) -> PlanningSession | None:
        session = self.get_planning_session(session_id)
        if not session:
            return None
        apply_message(session, payload.text)
        if self.settings.openai_enabled:
            try:
                apply_llm_constraints(session, await self.llm.extract_constraints(payload.text))
            except Exception:
                session.assumptions.append("추가 문장의 보강 분석에 실패해 규칙 기반 결과만 반영했습니다.")
        self._attach_destination_pack(session)
        self.database.save_planning_session(session)
        return session

    def patch_planning_constraints(self, session_id: str, payload: ConstraintPatch) -> PlanningSession | None:
        session = self.get_planning_session(session_id)
        if not session:
            return None
        apply_patch(session, payload)
        self._attach_destination_pack(session)
        self.database.save_planning_session(session)
        return session

    async def finalize_planning_session(self, session_id: str) -> TripResult | None:
        session = self.get_planning_session(session_id)
        if not session:
            return None
        result = await self.create_trip(build_trip_request(session))
        session.final_trip_id = result.id
        session.invalidated_sections = []
        self.database.save_planning_session(session)
        return result

    def delete_planning_session(self, session_id: str) -> bool:
        existed = bool(self.get_planning_session(session_id))
        self.sessions.pop(session_id, None)
        self.database.delete_planning_session(session_id)
        return existed

    def provider_health(self) -> list[ProviderHealth]:
        return [
            ProviderHealth(
                name="Amadeus",
                configured=self.settings.amadeus_enabled,
                mode="live" if self.settings.amadeus_enabled else "research",
                detail="항공·숙소 실시간 검색" if self.settings.amadeus_enabled else "키 없음 — 계획용 추정치와 가격 비교 링크 제공",
            ),
            ProviderHealth(
                name="Google Places & Routes",
                configured=self.settings.google_enabled,
                mode="live" if self.settings.google_enabled else "research",
                detail="장소·이동시간 실시간 조회" if self.settings.google_enabled else "키 없음 — 공식 관광·교통 검증 링크와 예상 경로 제공",
            ),
            ProviderHealth(
                name="OpenAI",
                configured=self.settings.openai_enabled,
                mode="live" if self.settings.openai_enabled else "sample",
                detail="설명 문장 보강" if self.settings.openai_enabled else "키 없음 — 결정론적 설명 사용",
            ),
            ProviderHealth(
                name="Booking.com",
                configured=self.settings.booking_enabled,
                mode="live" if self.settings.booking_enabled else "partner-unavailable",
                detail="숙소 검색·외부 예약 연결" if self.settings.booking_enabled else "파트너 승인 키 필요",
            ),
            ProviderHealth(
                name="Skyscanner",
                configured=self.settings.skyscanner_enabled,
                mode="live" if self.settings.skyscanner_enabled else "partner-unavailable",
                detail="항공·숙소 실시간 검색" if self.settings.skyscanner_enabled else "파트너 승인 키 필요",
            ),
        ]

    async def create_trip(self, request: TripRequest, trip_id: str | None = None) -> TripResult:
        trip_id = trip_id or str(uuid4())
        destination_pack = self.destinations.bootstrap(request.destination_city)
        if destination_pack.status != "validated":
            return self._destination_research_result(request, destination_pack, trip_id)
        warnings: list[str] = []
        sample_verticals: list[str] = []

        async def collect(providers, method_name: str, label: str):
            if not providers:
                return []
            responses = await asyncio.gather(
                *(getattr(provider, method_name)(request) for provider in providers), return_exceptions=True
            )
            combined = []
            for provider, response in zip(providers, responses):
                if isinstance(response, Exception):
                    warnings.append(f"{provider.name} {label} 검색에 실패해 다른 공급자 결과로 계속합니다.")
                elif not response:
                    warnings.append(f"{provider.name}에서 조건에 맞는 {label} 결과를 찾지 못했습니다.")
                else:
                    combined.extend(response)
            return combined

        flight_providers = []
        stay_providers = []
        if self.settings.amadeus_enabled:
            flight_providers.append(self.amadeus)
            stay_providers.append(self.amadeus)
        if self.settings.booking_enabled:
            stay_providers.append(self.booking)
        if self.settings.skyscanner_enabled:
            flight_providers.append(self.skyscanner)
            stay_providers.append(self.skyscanner)

        flights, stays = await asyncio.gather(
            collect(flight_providers, "search_flights", "항공"),
            collect(stay_providers, "search_stays", "숙소"),
        )
        if not flights:
            flights = await self.sample.search_flights(request)
            sample_verticals.append("항공")
            warnings.append("실시간 항공 결과가 없어 일정 계산용 추정치를 표시합니다. 비교 플랫폼에서 동일 조건을 재검색하세요.")
        max_stops = request.flight_preferences.max_stops
        if max_stops is not None:
            permitted_flights = [flight for flight in flights if flight.stops <= max_stops]
            if not permitted_flights:
                warnings.append(f"환승 {max_stops}회 이하 강제 조건을 만족하는 항공편을 찾지 못했습니다. 조건 완화 전에는 다른 항공편을 추천하지 않습니다.")
            flights = permitted_flights
        requested_stay_types = set(request.stay_types)
        matching_stays = [stay for stay in stays if stay.accommodation_type in requested_stay_types]
        if stays and not matching_stays:
            warnings.append("연결된 공급자 결과에 선택한 숙소 유형이 없어 해당 결과를 제외했습니다.")
        stays = matching_stays
        if not stays:
            stays = await self.sample.search_stays(request)
            sample_verticals.append("숙소")
            warnings.append("실시간 숙소 결과가 없어 일정 계산용 추정치를 표시합니다. 객실 재고와 결제 총액은 비교 링크에서 확인하세요.")
        stay_preferences = request.stay_preferences
        constrained_stays = [
            stay
            for stay in stays
            if (stay_preferences.bed_count is None or (stay.bed_count or 0) >= stay_preferences.bed_count)
            and (not stay_preferences.parking_required or stay.parking_available is True)
            and all(amenity in stay.amenities for amenity in stay_preferences.required_amenities)
        ]
        if stays and not constrained_stays:
            details = []
            if stay_preferences.bed_count:
                details.append(f"침대 {stay_preferences.bed_count}개")
            if stay_preferences.parking_required:
                details.append("주차 가능")
            if stay_preferences.required_amenities:
                details.append("어메니티 " + ", ".join(stay_preferences.required_amenities))
            warnings.append("숙소 강제 조건을 만족하는 결과가 없습니다: " + " · ".join(details) + ". 조건 완화 여부를 확인하세요.")
        stays = constrained_stays

        place_provider = self.google if self.settings.google_enabled else self.sample
        try:
            places = await place_provider.search_places(request)
            if not places:
                raise RuntimeError("empty place result")
        except Exception:
            places = await self.sample.search_places(request)
            place_provider = self.sample
            sample_verticals.append("장소")
            warnings.append("Google Places 조회에 실패해 장소만 샘플 데이터로 대체했습니다.")
        if not self.settings.google_enabled and "장소" not in sample_verticals:
            sample_verticals.append("장소")
            warnings.append("Google Maps 키가 없어 장소·경로는 대표도시 계획 기준값입니다. 공식 관광정보와 지도 링크를 함께 확인하세요.")

        active_places = [place for place in places if place.business_status not in {"CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"}][:40]
        try:
            matrix = await place_provider.route_matrix(active_places)
        except Exception:
            matrix = await self.sample.route_matrix(active_places)
            if "장소" not in sample_verticals:
                sample_verticals.append("경로")
            warnings.append("Google Routes 조회에 실패해 직선거리 기반 예상 이동시간을 사용했습니다.")

        sample_verticals = list(dict.fromkeys(sample_verticals))
        if "항공" in sample_verticals:
            for flight in flights:
                flight.price_status = "estimated"
                flight.confidence = "D"
        if "숙소" in sample_verticals:
            for stay in stays:
                stay.price_status = "estimated"
                stay.confidence = "D"
                stay.verified_inventory = False
        if "장소" in sample_verticals:
            for place in places:
                place.confidence = "D"

        now = datetime.now(timezone.utc)
        stale_seconds = self.settings.price_stale_minutes * 60
        for item in [*flights, *stays]:
            item.is_stale = (now - item.observed_at).total_seconds() > stale_seconds
        flights = rank_flights(flights, request.checked_baggage)[:5]
        stays = rank_stays(stays, request)[:5]
        matched_must_visits = match_must_visit_places(request, active_places)
        for requested_name in request.must_visit_places:
            requested_key = requested_name.replace(" ", "").lower()
            if not any(
                requested_key in candidate.replace(" ", "").lower()
                or candidate.replace(" ", "").lower() in requested_key
                for place in matched_must_visits
                for candidate in [place.name, place.local_name or ""]
                if candidate
            ):
                warnings.append(f"필수 방문지 ‘{requested_name}’를 장소 후보에서 확인하지 못했습니다. 정확한 이름으로 다시 입력하세요.")
        itineraries = build_itineraries(request, flights, stays, active_places, matrix)
        if itineraries:
            empty_full_days = [
                day
                for day in itineraries[0].days[1:-1]
                if not day.stops
            ]
            if empty_full_days:
                warnings.append("장소 후보가 부족해 일부 체류일이 비어 있습니다. 관심사나 검색 범위를 넓혀 다시 검색하세요.")

        unresolved = [
            "예약 페이지에서 최종 총액·수하물·취소 조건 재확인",
            "외교부 해외안전여행과 목적지 공식 입국 사이트에서 최신 요건 확인",
            "영업시간과 예약 필요 여부는 방문 당일 재확인",
        ]
        if itineraries and itineraries[0].trip_total_krw > request.budget_krw:
            warnings.append(
                f"균형형 예상 총액이 입력 예산 {request.budget_krw:,}원을 초과합니다. "
                "비용 절약형을 비교하거나 날짜·숙소 조건을 조정하세요."
            )
        if request.dietary_needs:
            unresolved.append("식당에 식이·알레르기 조건을 현지 언어로 직접 확인")
        if request.mobility_needs:
            unresolved.append("장소·교통 운영사에 접근성 조건과 엘리베이터 운행 여부 직접 확인")
        if request.ground_transport.mode == "rental_car":
            unresolved.append("렌터카 공식 예약 화면에서 차종 보장·운전자 나이·보험·세금·보증금 확인")
            unresolved.append("방문 당일 지도 교통량과 각 장소의 공식 주차요금 재확인")
        if request.dining_preferences.special_meals_per_day:
            unresolved.append("특별식은 공식 메뉴의 세금·팁 포함 총액이 설정 상한 이내인지 예약 전에 확인")
        live_vertical_present = bool(flight_providers or stay_providers or self.settings.google_enabled)
        if not sample_verticals:
            data_mode = "live"
        elif live_vertical_present:
            data_mode = "mixed"
        else:
            data_mode = "guided_research"
            unresolved.insert(0, "현재 화면의 금액은 계획용 추정치이며 웹 비교 링크의 날짜·인원 조건으로 실제 가격 확인")
        verification_links = build_verification_links(request)
        evidence = build_guided_research_evidence(request, sample_verticals) if sample_verticals else []
        result = TripResult(
            id=trip_id,
            status="ready" if flights and stays and itineraries else "partial",
            request=request,
            flights=flights,
            stays=stays,
            places=active_places,
            itineraries=itineraries,
            warnings=warnings,
            unresolved_checks=unresolved,
            sample_mode=bool(sample_verticals),
            data_mode=data_mode,
            sample_verticals=sample_verticals,
            evidence=evidence,
            verification_links=verification_links,
        )
        if self.settings.openai_enabled:
            try:
                result.narrative = await self.llm.summarize(
                    {
                        "destination": request.destination_city,
                        "best_flight": flights[0].model_dump(mode="json") if flights else None,
                        "best_stay": stays[0].model_dump(mode="json") if stays else None,
                        "variants": [
                            {"name": item.name, "total": item.trip_total_krw, "pros": item.pros, "cons": item.cons}
                            for item in itineraries
                        ],
                        "warnings": warnings,
                    }
                )
            except Exception:
                result.warnings.append("OpenAI 설명 생성에 실패해 코드가 만든 비교 결과만 표시합니다.")
        self.database.save_trip(result)
        if request.save_profile:
            self.database.save_profile(
                TravelerProfile(
                    budget_krw=request.budget_krw,
                    stay_types=request.stay_types,
                    pace=request.pace,
                    interests=request.interests,
                    dietary_needs=request.dietary_needs,
                    mobility_needs=request.mobility_needs,
                    consent_to_store=True,
                )
            )
        return result

    def _destination_research_result(self, request: TripRequest, pack: DestinationPack, trip_id: str) -> TripResult:
        verification_links = build_verification_links(request)
        evidence = []
        for index, source in enumerate(pack.sources):
            if source.source_type not in {"official_site", "comparison_platform"}:
                continue
            evidence.append(
                EvidenceRecord(
                    id=f"destination-source-{index}",
                    title=source.name,
                    source_name=source.name,
                    source_url=source.url,
                    source_type=source.source_type,
                    confidence="B" if source.source_type == "official_site" else "C",
                    value_status="reference",
                    observed_at=source.observed_at,
                    note=source.note or "목적지 초기세팅에서 확인할 출처입니다.",
                    verification_required=True,
                )
            )
        result = TripResult(
            id=trip_id,
            status="partial",
            request=request,
            flights=[],
            stays=[],
            places=[],
            itineraries=[],
            warnings=[
                f"{pack.city_name}은 아직 {('조사 중' if pack.status == 'researching' else '임시 지원')} 목적지입니다.",
                "검증되지 않은 다른 도시의 샘플 가격·장소·동선을 대신 표시하지 않습니다.",
                "공식 출처 조사와 공급자 지원 확인 후 목적지 팩을 검증 상태로 전환해야 최종 동선을 계산합니다.",
            ],
            unresolved_checks=[task.label + " — " + task.reason for task in pack.research_tasks if task.status != "ready"],
            sample_mode=False,
            data_mode="guided_research",
            evidence=evidence,
            verification_links=verification_links,
        )
        self.database.save_trip(result)
        return result

    async def refresh_trip(self, trip_id: str) -> TripResult | None:
        existing = self.database.get_trip(trip_id)
        if not existing:
            return None
        refreshed = await self.create_trip(existing.request, trip_id=trip_id)
        refreshed.created_at = existing.created_at
        refreshed.updated_at = datetime.now(timezone.utc)
        self.database.save_trip(refreshed)
        return refreshed

    async def replan_trip(self, trip_id: str, context: ReplanRequest) -> TripResult | None:
        refreshed = await self.refresh_trip(trip_id)
        if not refreshed:
            return None
        places = [place for place in refreshed.places if place.id not in set(context.closed_place_ids)]
        if context.weather and any(word in context.weather.lower() for word in ["비", "rain", "폭우"]):
            must_visit_ids = {place.id for place in match_must_visit_places(refreshed.request, places)}
            dry_places = [place for place in places if place.rain_suitable or place.id in must_visit_ids]
            if len(dry_places) >= 3:
                places = dry_places
                refreshed.warnings.append("우천 조건을 반영해 실내·우천 적합 장소를 우선하되 필수 방문지는 유지했습니다.")
        matrix = await self.sample.route_matrix(places)
        refreshed.places = places
        refreshed.itineraries = build_itineraries(
            refreshed.request, refreshed.flights, refreshed.stays, places, matrix
        )
        context_bits = [bit for bit in [context.current_location, context.weather, context.notes] if bit]
        if context_bits:
            refreshed.warnings.append("현지 재계획 조건: " + " · ".join(context_bits))
        refreshed.updated_at = datetime.now(timezone.utc)
        self.database.save_trip(refreshed)
        return refreshed
