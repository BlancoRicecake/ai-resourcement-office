from __future__ import annotations

import calendar
import re
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from .destinations import catalog_by_country, country_match, resolve_destination
from .models import (
    ConstraintChange,
    ConstraintHardness,
    ConstraintPatch,
    ConstraintValue,
    CrowdPreferences,
    DiningPreferences,
    FlightPreferences,
    GroundTransportPreferences,
    PlanningMessage,
    PlanningPreview,
    PlanningSession,
    QuestionCard,
    QuestionOption,
    StayPreferences,
    TripRequest,
)


COUNTRY_CANDIDATES = {
    code: [{"city": item.city_name, "summary": item.summary} for item in catalog_by_country(code) if item.status == "validated"]
    for code in ("JP", "US")
}

HARD_WORDS = ("꼭", "절대", "무조건", "필수", "반드시", "경유 없이")
DELEGATE_WORDS = ("잘 모르겠", "모르겠어", "추천해줘", "알아서", "적당히")
DEPENDENCIES = {
    "destination_country": ["flight", "stay", "ground_transport", "itinerary"],
    "destination_city": ["flight", "stay", "ground_transport", "itinerary"],
    "destination_status": ["flight", "stay", "ground_transport", "itinerary"],
    "departure_date": ["flight", "stay", "itinerary"],
    "return_date": ["flight", "stay", "itinerary"],
    "origin_airport": ["flight"],
    "adults": ["flight", "stay", "ground_transport", "itinerary"],
    "rooms": ["stay"],
    "bed_count": ["stay"],
    "parking_required": ["stay", "ground_transport", "itinerary"],
    "ground_mode": ["ground_transport", "itinerary"],
    "sports_model_preferred": ["ground_transport", "itinerary"],
    "must_visit_places": ["itinerary"],
    "avoid_crowds": ["itinerary"],
}


def _number(text: str) -> int | None:
    words = {"한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5, "여섯": 6, "일곱": 7}
    if text.isdigit():
        return int(text)
    return words.get(text)


def _won_amount(text: str) -> int | None:
    match = re.search(r"([\d,.]+)\s*만\s*원", text)
    if match:
        return int(float(match.group(1).replace(",", "")) * 10_000)
    match = re.search(r"([\d,]+)\s*원", text)
    return int(match.group(1).replace(",", "")) if match else None


def _constraint(
    key: str,
    value: Any,
    *,
    source: str = "explicit",
    status: str = "confirmed",
    hardness: ConstraintHardness = "soft",
    confidence: float = 0.95,
    reason: str,
) -> ConstraintValue:
    return ConstraintValue(
        key=key,
        value=value,
        source=source,
        status=status,
        hardness=hardness,
        confidence=confidence,
        reason=reason,
    )


def extract_constraints(text: str, today: date | None = None) -> dict[str, ConstraintValue]:
    today = today or date.today()
    lowered = text.lower().strip()
    hard = "hard" if any(word in lowered for word in HARD_WORDS) else "soft"
    found: dict[str, ConstraintValue] = {}

    destination = resolve_destination(text)
    if destination:
        found["destination_country"] = _constraint("destination_country", destination.country_code, reason=f"‘{destination.country_name}’ 국가를 확인")
        found["destination_city"] = _constraint("destination_city", destination.city_name, reason=f"‘{destination.city_name}’를 목적지로 확인")
        if destination.city_code:
            found["destination_code"] = _constraint("destination_code", destination.city_code, reason="목적지 공항·도시 코드")
        found["destination_slug"] = _constraint("destination_slug", destination.slug, source="inferred", status="proposed", confidence=0.9, reason="목적지 조사 팩 연결")
        found["destination_status"] = _constraint("destination_status", destination.status, source="inferred", status="proposed", confidence=0.95, reason="현재 목적지 지원·검증 상태")
    else:
        country = country_match(text)
        if country:
            found["destination_country"] = _constraint("destination_country", country[0], reason=f"{country[1]} 여행 요청")

    iso_dates = re.findall(r"(20\d{2})[-./](\d{1,2})[-./](\d{1,2})", lowered)
    if len(iso_dates) >= 2:
        departure = date(*(int(part) for part in iso_dates[0]))
        returning = date(*(int(part) for part in iso_dates[1]))
        found["departure_date"] = _constraint("departure_date", departure.isoformat(), reason="출국일 명시")
        found["return_date"] = _constraint("return_date", returning.isoformat(), reason="귀국일 명시")
    else:
        korean_dates = re.findall(r"(?:(20\d{2})년\s*)?(\d{1,2})월\s*(\d{1,2})일", lowered)
        if korean_dates:
            first_year = int(korean_dates[0][0] or today.year)
            first_month = int(korean_dates[0][1])
            if not korean_dates[0][0] and first_month < today.month:
                first_year += 1
            departure = date(first_year, first_month, int(korean_dates[0][2]))
            found["departure_date"] = _constraint("departure_date", departure.isoformat(), reason="한국어 출국일 명시")
            if len(korean_dates) >= 2:
                second_year = int(korean_dates[1][0] or first_year)
                returning = date(second_year, int(korean_dates[1][1]), int(korean_dates[1][2]))
                found["return_date"] = _constraint("return_date", returning.isoformat(), reason="한국어 귀국일 명시")
        range_match = re.search(r"(?:(20\d{2})년\s*)?(\d{1,2})월\s*(\d{1,2})일(?:부터|\s*[-~]\s*)(\d{1,2})일", lowered)
        if range_match:
            year = int(range_match.group(1) or today.year)
            month = int(range_match.group(2))
            if not range_match.group(1) and month < today.month:
                year += 1
            found["departure_date"] = _constraint("departure_date", date(year, month, int(range_match.group(3))).isoformat(), reason="날짜 범위의 출국일")
            found["return_date"] = _constraint("return_date", date(year, month, int(range_match.group(4))).isoformat(), reason="날짜 범위의 귀국일")
        if "departure_date" not in found:
            month_match = re.search(r"(?:(20\d{2})년?\s*)?(\d{1,2})월", lowered)
            if month_match:
                year = int(month_match.group(1) or today.year)
                month = int(month_match.group(2))
                if not month_match.group(1) and month < today.month:
                    year += 1
                found["travel_month"] = _constraint("travel_month", f"{year:04d}-{month:02d}", reason="여행 월 명시")
            else:
                season_month = next(((token, month) for token, month in (("봄", 4), ("여름", 8), ("가을", 10), ("겨울", 1)) if token in lowered), None)
                if season_month:
                    token, month = season_month
                    year = today.year + (1 if month < today.month else 0)
                    found["travel_month"] = _constraint(
                        "travel_month",
                        f"{year:04d}-{month:02d}",
                        source="inferred",
                        status="proposed",
                        confidence=0.75,
                        reason=f"‘{token}’을 대표 월 {month}월로 제안",
                    )

    duration = re.search(r"(\d+)\s*박\s*(\d+)\s*일", lowered)
    if duration:
        found["nights"] = _constraint("nights", int(duration.group(1)), reason="숙박 일수 명시")
        found["trip_days"] = _constraint("trip_days", int(duration.group(2)), reason="전체 여행일수 명시")
    elif re.search(r"(?:일주일|1주일)", lowered):
        found["nights"] = _constraint("nights", 6, source="inferred", status="proposed", confidence=0.8, reason="일주일을 6박 7일로 제안")
        found["trip_days"] = _constraint("trip_days", 7, source="inferred", status="proposed", confidence=0.8, reason="일주일을 6박 7일로 제안")
    if "departure_date" in found and "return_date" not in found and "nights" in found:
        departure = date.fromisoformat(found["departure_date"].value)
        returning = date.fromordinal(departure.toordinal() + int(found["nights"].value))
        found["return_date"] = _constraint("return_date", returning.isoformat(), source="inferred", status="proposed", confidence=0.85, reason="출국일과 숙박 일수로 귀국일 계산")

    adult_match = re.search(r"(?:성인|남성|여성)[^\d한두세네]{0,8}(\d+|한|두|세|네)\s*명", lowered)
    if adult_match:
        found["adults"] = _constraint("adults", _number(adult_match.group(1)), reason="성인 인원 명시")
    elif "둘이" in lowered or "친구랑" in lowered or "커플" in lowered:
        found["adults"] = _constraint("adults", 2, source="inferred", status="proposed", confidence=0.75, reason="동행 표현에서 2명으로 제안")

    room_match = re.search(r"(?:객실|방)\s*(\d+)\s*개", lowered)
    if room_match:
        found["rooms"] = _constraint("rooms", int(room_match.group(1)), reason="객실 수 명시")

    budget_match = re.search(r"(?:총\s*)?(?:예산|여행비)[^\d]{0,10}([\d,.]+\s*만\s*원|[\d,]+\s*원)", lowered)
    if budget_match:
        found["budget_krw"] = _constraint("budget_krw", _won_amount(budget_match.group(1)), hardness=hard, reason="총예산 명시")
    if any(word in lowered for word in ("저렴", "가성비", "최대한 싸", "싼 게 최고")):
        found["pace"] = _constraint("pace", "budget", reason="비용 우선 요청")

    if "직항" in lowered or "경유 없이" in lowered or "논스톱" in lowered:
        found["direct_required"] = _constraint("direct_required", True, hardness="hard" if hard == "hard" or "경유 없이" in lowered else "soft", reason="직항 요청")
        found["max_stops"] = _constraint("max_stops", 0, hardness=found["direct_required"].hardness, reason="직항은 환승 0회")
    if "위탁수하물" in lowered:
        found["checked_baggage"] = _constraint("checked_baggage", True, reason="위탁수하물 요청")

    bed_match = re.search(r"침대(?:는|가|\s)*\s*(\d+)\s*개", lowered)
    if bed_match:
        found["bed_count"] = _constraint("bed_count", int(bed_match.group(1)), hardness="hard" if hard == "hard" or "사용" in lowered else "soft", reason="침대 수 명시")
    amenities = [label for token, label in (("와이파이", "무료 Wi-Fi"), ("조식", "조식"), ("수영장", "수영장"), ("피트니스", "피트니스")) if token in lowered]
    if amenities:
        found["required_amenities"] = _constraint("required_amenities", amenities, hardness=hard, reason="숙소 어메니티 요청")

    if "렌터카" in lowered or "렌트카" in lowered:
        found["ground_mode"] = _constraint("ground_mode", "rental_car", reason="렌터카 이용 요청")
    elif "대중교통" in lowered:
        found["ground_mode"] = _constraint("ground_mode", "transit", reason="대중교통 이용 요청")
    if "스포츠" in lowered and ("차" in lowered or "모델" in lowered):
        found["sports_model_preferred"] = _constraint("sports_model_preferred", True, reason="스포츠 모델 선호")
        found["rental_class"] = _constraint("rental_class", "sports", source="inferred", status="proposed", confidence=0.85, reason="스포츠 차량 등급으로 제안")
    age_match = re.search(r"(?:운전자|운전자는?|나이)\s*(\d{2})\s*(?:세|살)", lowered)
    if age_match:
        found["driver_age"] = _constraint("driver_age", int(age_match.group(1)), reason="운전자 나이 명시")
    if "주차" in lowered:
        found["parking_required"] = _constraint("parking_required", True, hardness="hard" if hard == "hard" or "필수" in lowered else "soft", reason="주차 조건 요청")

    special_sentence = next((part for part in re.split(r"[.!?。]|그리고", lowered) if "호화" in part or "특별" in part), "")
    if special_sentence:
        found["special_meals_per_day"] = _constraint("special_meals_per_day", 1, reason="하루 특별식 요청")
        amount = _won_amount(special_sentence)
        if amount:
            found["special_meal_budget_krw"] = _constraint("special_meal_budget_krw", amount, hardness=hard, reason="특별식 예산 상한 명시")

    if any(word in lowered for word in ("사람이 너무 많이", "사람이 몰리는", "혼잡", "사람 몰리는", "붐비")):
        found["avoid_crowds"] = _constraint("avoid_crowds", "high", reason="혼잡 회피 요청")

    must_visits = []
    for token, name in (("유니버설", "유니버설 스튜디오 할리우드"), ("그리피스", "그리피스 천문대"), ("게티", "게티 센터")):
        if token in lowered and any(word in lowered for word in ("꼭", "필수", "가고 싶", "가고싶")):
            must_visits.append(name)
    if must_visits:
        found["must_visit_places"] = _constraint("must_visit_places", must_visits, hardness="hard", reason="필수 방문지 명시")

    if "유연" in lowered or "가격에 따라" in lowered or "가장 합리적인 항공권" in lowered:
        found["date_flexibility_days"] = _constraint("date_flexibility_days", 7, reason="가격에 따른 날짜 조정 허용")
    return found


def _apply_defaults(session: PlanningSession) -> None:
    defaults = {
        "origin_airport": ("ICN", "한국 출발 기본 공항으로 인천을 제안"),
        "rooms": (1, "객실 수가 없어 1객실을 제안"),
        "pace": ("balanced", "비용과 이동 피로를 함께 보는 균형형을 제안"),
        "stay_types": (["hotel"], "숙소 유형이 없어 호텔을 제안"),
    }
    for key, (value, reason) in defaults.items():
        if key not in session.constraints:
            session.constraints[key] = _constraint(key, value, source="default", status="proposed", confidence=0.55, reason=reason)


def _merge(session: PlanningSession, incoming: dict[str, ConstraintValue]) -> None:
    for key, value in incoming.items():
        previous = session.constraints.get(key)
        if previous and previous.hardness == "hard" and previous.status == "confirmed" and previous.value != value.value:
            session.assumptions.append(f"‘{key}’ 강제 조건이 이전 값과 달라 최신 요청을 제안 상태로 표시했습니다.")
            value.status = "proposed"
        session.constraints[key] = value


def _invalidate(session: PlanningSession, keys: list[str]) -> None:
    if not session.final_trip_id:
        session.invalidated_sections = []
        return
    invalidated = []
    for key in keys:
        invalidated.extend(DEPENDENCIES.get(key, []))
    session.invalidated_sections = list(dict.fromkeys(invalidated))
    if session.invalidated_sections:
        session.final_trip_id = None


def _value(session: PlanningSession, key: str, default: Any = None) -> Any:
    item = session.constraints.get(key)
    return item.value if item and item.value is not None else default


def compute_readiness(session: PlanningSession) -> dict[str, str]:
    city = bool(_value(session, "destination_city"))
    country = bool(_value(session, "destination_country"))
    dates = bool(_value(session, "departure_date") and _value(session, "return_date"))
    people = bool(_value(session, "adults"))
    origin = bool(_value(session, "origin_airport"))
    support_status = _value(session, "destination_status", "validated" if country in {"JP", "US"} and city else None)
    validated = support_status == "validated"
    destination = "complete" if city and validated else ("preview_ready" if city or country else "blocked")
    flight = "search_ready" if validated and city and dates and people and origin else ("preview_ready" if city and (_value(session, "travel_month") or dates) else "blocked")
    stay = "search_ready" if validated and city and dates and people else ("preview_ready" if city else "blocked")
    ground = "complete" if _value(session, "ground_mode") in {"transit", "mixed"} else "preview_ready"
    if _value(session, "ground_mode") == "rental_car":
        ground = "complete" if _value(session, "driver_age") else "preview_ready"
    itinerary = "search_ready" if validated and city and dates else ("preview_ready" if city and support_status != "researching" else "blocked")
    return {"destination": destination, "flight": flight, "stay": stay, "ground_transport": ground, "itinerary": itinerary}


def build_questions(session: PlanningSession) -> list[QuestionCard]:
    questions: list[QuestionCard] = []

    def add(card: QuestionCard) -> None:
        if card.id not in session.asked_question_ids and not questions:
            questions.append(card)

    if not _value(session, "destination_country"):
        add(QuestionCard(id="destination-vibe", key="destination_country", prompt="어떤 여행에 더 끌리세요?", why_asked="목적지 후보를 좁히면 시기와 예산 범위를 제안할 수 있어요.", options=[
            QuestionOption(label="가깝고 편한 일본", value="일본", recommended=True),
            QuestionOption(label="도시 경험이 큰 미국", value="미국"),
            QuestionOption(label="추천해줘", value="추천해줘"),
        ]))
    elif not _value(session, "destination_city"):
        country = _value(session, "destination_country")
        options = [QuestionOption(label=item["city"], value=item["city"], description=item["summary"], recommended=index == 0) for index, item in enumerate(COUNTRY_CANDIDATES.get(country, []))]
        if not options:
            options.append(QuestionOption(label="도시 직접 입력", value=f"{country} 도시 직접 입력", recommended=True))
        options.append(QuestionOption(label="추천해줘", value="추천해줘"))
        add(QuestionCard(id=f"destination-city-{country}", key="destination_city", prompt="어느 도시가 더 마음에 드세요?", why_asked="도시가 정해지면 항공과 숙소 가격 범위를 만들 수 있어요.", options=options[:3]))
    elif not (_value(session, "travel_month") or _value(session, "departure_date")):
        add(QuestionCard(id="travel-time", key="travel_month", prompt="언제쯤 떠나고 싶으세요?", why_asked="정확한 날짜가 아니어도 계절과 월만 알면 초안을 만들 수 있어요.", options=[
            QuestionOption(label="한 달 안", value="한 달 안", recommended=True),
            QuestionOption(label="여름", value="8월"),
            QuestionOption(label="추천 시기", value="추천해줘"),
        ]))
    elif not (_value(session, "trip_days") or (_value(session, "departure_date") and _value(session, "return_date"))):
        add(QuestionCard(id="trip-duration", key="trip_days", prompt="며칠 정도가 편하세요?", why_asked="여행 길이가 항공·숙소 총액과 일정 밀도를 크게 바꿉니다.", options=[
            QuestionOption(label="3박 4일", value="3박 4일"),
            QuestionOption(label="5박 6일", value="5박 6일", recommended=True),
            QuestionOption(label="6박 7일", value="6박 7일"),
        ]))
    elif not _value(session, "adults"):
        add(QuestionCard(id="traveler-count", key="adults", prompt="여행자는 몇 명인가요?", why_asked="항공·숙소·입장료 총액에 바로 반영됩니다.", options=[
            QuestionOption(label="성인 1명", value="성인 1명"),
            QuestionOption(label="성인 2명", value="성인 2명", recommended=True),
            QuestionOption(label="직접 입력", value="직접 입력"),
        ]))
    elif _value(session, "travel_month") and not _value(session, "departure_date"):
        month = _value(session, "travel_month")
        add(QuestionCard(id="exact-dates", key="departure_date", prompt=f"{month} 안에서 정확한 날짜는 항공 가격을 보고 정할까요?", why_asked="정확한 날짜를 확정해야 실제 항공·숙소 검색을 시작할 수 있어요.", options=[
            QuestionOption(label="가격 좋은 주 추천", value="가격 좋은 주 추천", recommended=True),
            QuestionOption(label="평일 출발 선호", value="평일 출발 선호"),
            QuestionOption(label="날짜 직접 입력", value="날짜 직접 입력"),
        ]))
    elif _value(session, "ground_mode") == "rental_car" and not _value(session, "driver_age"):
        add(QuestionCard(id="driver-age", key="driver_age", prompt="대표 운전자의 나이는 어떻게 되나요?", why_asked="렌터카 가능 차종과 만 25세 미만 추가요금에 영향을 줍니다.", options=[
            QuestionOption(label="만 25세 이상", value="운전자 25세", recommended=True),
            QuestionOption(label="만 21~24세", value="운전자 23세"),
            QuestionOption(label="렌터카 안 함", value="대중교통"),
        ]))
    elif "safety_checked" not in session.constraints:
        add(QuestionCard(id="safety-needs", key="safety_checked", prompt="음식 알레르기나 이동 제약이 있나요?", why_asked="식당과 이동 경로를 안전하게 추천하기 위한 마지막 확인입니다.", options=[
            QuestionOption(label="없음", value="제약 없음", recommended=True),
            QuestionOption(label="식이 조건 있음", value="식이 조건 있음"),
            QuestionOption(label="이동 제약 있음", value="이동 제약 있음"),
        ]))
    return questions


def build_preview(session: PlanningSession) -> PlanningPreview | None:
    country = _value(session, "destination_country")
    city = _value(session, "destination_city")
    if not (country or city):
        return None
    country_names = {"JP": "일본", "US": "미국"}
    destination = city or country_names.get(country, country or "목적지")
    timing = _value(session, "departure_date") or _value(session, "travel_month") or "시기 미정"
    days = _value(session, "trip_days")
    travelers = _value(session, "adults")
    detail = " · ".join(part for part in [str(timing), f"{days}일" if days else None, f"성인 {travelers}명" if travelers else None] if part)
    assumptions = [item.reason for item in session.constraints.values() if item.status == "proposed" or item.source in {"default", "delegated"}]
    candidates = COUNTRY_CANDIDATES.get(country, []) if not city else []
    ready = [key for key, status in session.readiness.items() if status in {"preview_ready", "search_ready", "complete"}]
    support_status = _value(session, "destination_status")
    summary = f"{detail or '기본 조건을 정리하는 중'} 기준으로 먼저 뼈대를 만들고 있어요. 미확정 조건은 예약 가격으로 표시하지 않습니다."
    if support_status in {"provisional", "researching"}:
        summary += " 처음 조사하는 목적지이므로 공식 출처·공급자 지원·현지 비용 기준을 먼저 확인합니다. 검증 전에는 다른 도시의 샘플 일정으로 대체하지 않습니다."
    return PlanningPreview(
        headline=f"{destination} 여행 가설 초안",
        summary=summary,
        destination_candidates=candidates[:3],
        assumptions=assumptions,
        ready_sections=ready,
        destination_status=support_status,
    )


def _assistant_text(session: PlanningSession) -> str:
    confirmed = sum(item.status == "confirmed" for item in session.constraints.values())
    proposed = sum(item.status == "proposed" for item in session.constraints.values())
    lead = f"말씀에서 확정 조건 {confirmed}개를 정리했어요."
    if proposed:
        lead += f" 제가 제안한 가정 {proposed}개는 오른쪽에서 바로 바꿀 수 있습니다."
    if _value(session, "destination_status") in {"provisional", "researching"}:
        lead += " 이 목적지는 공식 정보를 먼저 수집하는 초기세팅 단계로 시작합니다."
    if session.next_questions:
        return lead + " 초안을 유지한 채, 결과를 가장 크게 바꾸는 한 가지만 여쭐게요."
    return lead + " 이제 세 가지 여행안을 계산할 준비가 됐습니다."


def apply_message(session: PlanningSession, text: str) -> PlanningSession:
    session.messages.append(PlanningMessage(role="user", content=text))
    delegated = any(word in text.lower() for word in DELEGATE_WORDS)
    current_question = session.next_questions[0] if session.next_questions else None
    contextual: dict[str, ConstraintValue] = {}
    if current_question and current_question.key == "departure_date" and any(word in text for word in ("추천", "평일")):
        year, month = (int(part) for part in str(_value(session, "travel_month")).split("-"))
        mondays = [day for day in range(1, calendar.monthrange(year, month)[1] + 1) if date(year, month, day).weekday() == 0]
        preferred_index = 2 if _value(session, "avoid_crowds") == "high" and len(mondays) > 2 else 1
        departure = date(year, month, mondays[preferred_index] if len(mondays) > preferred_index else mondays[0])
        nights = int(_value(session, "nights", max(1, int(_value(session, "trip_days", 6)) - 1)))
        returning = date.fromordinal(departure.toordinal() + nights)
        contextual["departure_date"] = _constraint("departure_date", departure.isoformat(), source="delegated", status="proposed", confidence=0.6, reason="월 중 평일 출발 가설 날짜를 제안")
        contextual["return_date"] = _constraint("return_date", returning.isoformat(), source="delegated", status="proposed", confidence=0.6, reason="여행 기간에 맞춘 가설 귀국일")
    elif current_question and current_question.key == "travel_month" and "한 달 안" in text:
        next_month = date.today().month + 1
        year = date.today().year + (1 if next_month > 12 else 0)
        month = 1 if next_month > 12 else next_month
        contextual["travel_month"] = _constraint("travel_month", f"{year:04d}-{month:02d}", source="delegated", status="proposed", confidence=0.6, reason="한 달 안의 다음 달을 가설 시기로 제안")
    elif current_question and current_question.key == "safety_checked" and "제약 없음" in text:
        contextual["safety_checked"] = _constraint("safety_checked", True, reason="식이·이동 제약 없음 확인")
    if contextual:
        _invalidate(session, list(contextual))
        _merge(session, contextual)
        session.asked_question_ids.append(current_question.id)
    elif delegated and session.next_questions:
        current = session.next_questions[0]
        defaults: dict[str, Any] = {
            "destination_country": "JP",
            "destination_city": "도쿄" if _value(session, "destination_country") == "JP" else "로스앤젤레스",
            "travel_month": f"{date.today().year}-{min(12, date.today().month + 2):02d}",
            "trip_days": 6,
            "adults": 1,
            "driver_age": 25,
            "safety_checked": True,
        }
        value = defaults.get(current.key)
        if value is not None:
            _invalidate(session, [current.key])
            session.constraints[current.key] = _constraint(current.key, value, source="delegated", status="proposed", confidence=0.55, reason=f"‘추천해줘’에 따라 {current.prompt}의 권장값 적용")
            if current.key == "trip_days":
                session.constraints["nights"] = _constraint("nights", 5, source="delegated", status="proposed", confidence=0.55, reason="6일 여행의 숙박을 5박으로 제안")
            session.asked_question_ids.append(current.id)
    else:
        extracted = extract_constraints(text)
        _invalidate(session, list(extracted))
        _merge(session, extracted)
        if session.next_questions:
            session.asked_question_ids.append(session.next_questions[0].id)
    if _value(session, "departure_date") and not _value(session, "return_date") and _value(session, "nights"):
        departure = date.fromisoformat(_value(session, "departure_date"))
        returning = date.fromordinal(departure.toordinal() + int(_value(session, "nights")))
        session.constraints["return_date"] = _constraint("return_date", returning.isoformat(), source="inferred", status="proposed", confidence=0.85, reason="출국일과 숙박 일수로 귀국일 계산")
    _apply_defaults(session)
    session.readiness = compute_readiness(session)
    session.next_questions = build_questions(session)
    session.preview = build_preview(session)
    session.messages.append(PlanningMessage(role="assistant", content=_assistant_text(session)))
    session.updated_at = datetime.now(timezone.utc)
    return session


def create_session(message: str, locale: str, timezone_name: str, consent_to_store: bool) -> PlanningSession:
    session = PlanningSession(id=str(uuid4()), locale=locale, timezone=timezone_name, consent_to_store=consent_to_store)
    return apply_message(session, message)


def apply_patch(session: PlanningSession, patch: ConstraintPatch) -> PlanningSession:
    _invalidate(session, [change.key for change in patch.changes])
    for change in patch.changes:
        previous = session.constraints.get(change.key)
        session.constraints[change.key] = _constraint(
            change.key,
            change.value,
            source="explicit",
            status="confirmed" if change.confirmed else "proposed",
            hardness=change.hardness or (previous.hardness if previous else "soft"),
            confidence=1.0 if change.confirmed else 0.8,
            reason="조건 요약 패널에서 직접 수정",
        )
    _apply_defaults(session)
    session.readiness = compute_readiness(session)
    session.next_questions = build_questions(session)
    session.preview = build_preview(session)
    session.updated_at = datetime.now(timezone.utc)
    return session


def build_trip_request(session: PlanningSession) -> TripRequest:
    required = [key for key in ("destination_country", "destination_city", "departure_date", "return_date", "adults") if not _value(session, key)]
    if required:
        labels = {"destination_country": "국가", "destination_city": "도시", "departure_date": "출국일", "return_date": "귀국일", "adults": "여행자 수"}
        raise ValueError("최종 검색 전에 필요한 조건: " + ", ".join(labels[key] for key in required))
    must_visits = list(_value(session, "must_visit_places", []))
    checked_baggage = bool(_value(session, "checked_baggage", False))
    direct = bool(_value(session, "direct_required", False))
    ground_mode = _value(session, "ground_mode", "undecided")
    return TripRequest(
        destination_country=_value(session, "destination_country"),
        destination_city=_value(session, "destination_city"),
        destination_code=_value(session, "destination_code"),
        origin_airport=_value(session, "origin_airport", "ICN"),
        departure_date=date.fromisoformat(_value(session, "departure_date")),
        return_date=date.fromisoformat(_value(session, "return_date")),
        date_flexibility_days=int(_value(session, "date_flexibility_days", 0)),
        adults=int(_value(session, "adults")),
        children=int(_value(session, "children", 0)),
        rooms=int(_value(session, "rooms", 1)),
        budget_krw=int(_value(session, "budget_krw", 5_000_000 if _value(session, "destination_country") == "US" else 2_000_000)),
        checked_baggage=checked_baggage,
        cabin_class=_value(session, "cabin_class", "ECONOMY"),
        stay_types=list(_value(session, "stay_types", ["hotel"])),
        pace=_value(session, "pace", "balanced"),
        interests=list(_value(session, "interests", ["명소", "현지 음식"])),
        dietary_needs=list(_value(session, "dietary_needs", [])),
        mobility_needs=list(_value(session, "mobility_needs", [])),
        must_visit_places=must_visits,
        flight_preferences=FlightPreferences(max_stops=_value(session, "max_stops"), direct_required=direct, baggage_required=checked_baggage or None),
        stay_preferences=StayPreferences(
            bed_count=_value(session, "bed_count"),
            parking_required=bool(_value(session, "parking_required", False)),
            required_amenities=list(_value(session, "required_amenities", [])),
        ),
        ground_transport=GroundTransportPreferences(
            mode=ground_mode,
            rental_class=_value(session, "rental_class"),
            sports_model_preferred=bool(_value(session, "sports_model_preferred", False)),
            driver_age=_value(session, "driver_age"),
            parking_required=bool(_value(session, "parking_required", False)),
        ),
        dining_preferences=DiningPreferences(
            special_meals_per_day=int(_value(session, "special_meals_per_day", 0)),
            special_meal_budget_krw=_value(session, "special_meal_budget_krw"),
        ),
        crowd_preferences=CrowdPreferences(avoid_crowds=_value(session, "avoid_crowds", "low"), must_visit_places=must_visits),
        save_profile=session.consent_to_store,
    )


def apply_llm_constraints(session: PlanningSession, extracted: dict[str, Any] | None) -> PlanningSession:
    if not extracted:
        return session
    allowed = {
        "destination_country", "destination_city", "destination_code", "travel_month", "departure_date",
        "return_date", "nights", "trip_days", "adults", "children", "rooms", "budget_krw", "pace",
        "direct_required", "max_stops", "checked_baggage", "bed_count", "required_amenities", "ground_mode",
        "rental_class", "sports_model_preferred", "driver_age", "parking_required", "special_meals_per_day",
        "special_meal_budget_krw", "avoid_crowds", "must_visit_places", "dietary_needs", "mobility_needs",
    }
    incoming = {}
    for key, payload in extracted.items():
        if key not in allowed or key in session.constraints or not isinstance(payload, dict) or "value" not in payload:
            continue
        incoming[key] = _constraint(
            key,
            payload["value"],
            source="inferred",
            status="proposed",
            hardness="hard" if payload.get("hardness") == "hard" else "soft",
            confidence=0.72,
            reason=str(payload.get("reason") or "자유문장 문맥에서 제안"),
        )
    _invalidate(session, list(incoming))
    _merge(session, incoming)
    session.readiness = compute_readiness(session)
    session.next_questions = build_questions(session)
    session.preview = build_preview(session)
    session.updated_at = datetime.now(timezone.utc)
    return session
