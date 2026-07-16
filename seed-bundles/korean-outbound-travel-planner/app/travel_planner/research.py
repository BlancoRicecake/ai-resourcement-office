from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote_plus, urlencode

from .models import EvidenceRecord, TripRequest, VerificationLink
from .providers.sample import city_config


OFFICIAL_CITY_SOURCES = {
    "TYO": {
        "guide": ("GO TOKYO", "https://www.gotokyo.org/en/"),
        "transport": ("Tokyo Metro", "https://www.tokyometro.jp/en/ticket/index.html"),
    },
    "OSA": {
        "guide": ("Osaka Info", "https://osaka-info.jp/en/"),
        "transport": ("Osaka Metro", "https://subway.osakametro.co.jp/en/guide/fare/"),
    },
    "NYC": {
        "guide": ("New York City Tourism", "https://www.nyctourism.com/"),
        "transport": ("MTA", "https://www.mta.info/fares"),
    },
    "LAX": {
        "guide": ("Discover Los Angeles", "https://www.discoverlosangeles.com/"),
        "transport": ("LA Metro", "https://www.metro.net/riding/fares/"),
    },
}


def _destination_code(request: TripRequest) -> str:
    return (request.destination_code or city_config(request)["code"]).upper()


def _skyscanner_date(value) -> str:
    return value.strftime("%y%m%d")


def build_verification_links(request: TripRequest) -> list[VerificationLink]:
    destination = _destination_code(request)
    origin = request.origin_airport.upper()
    city_query = quote_plus(request.destination_city)
    flight_query = quote_plus(
        f"{origin} to {destination} {request.departure_date.isoformat()} {request.return_date.isoformat()}"
    )
    booking_query = urlencode(
        {
            "ss": request.destination_city,
            "checkin": request.departure_date.isoformat(),
            "checkout": request.return_date.isoformat(),
            "group_adults": request.adults,
            "group_children": request.children,
            "no_rooms": request.rooms,
        }
    )
    official = OFFICIAL_CITY_SOURCES.get(destination)
    if official is None:
        official = {
            "guide": ("공식 관광정보 검색 안내", f"https://www.google.com/search?q={quote_plus(request.destination_city + ' official tourism') }"),
            "transport": ("공식 교통정보 검색 안내", f"https://www.google.com/search?q={quote_plus(request.destination_city + ' official public transport') }"),
        }
    links = [
        VerificationLink(
            category="flight",
            platform="Google Flights",
            title="날짜·노선별 항공편 비교",
            url=f"https://www.google.com/travel/flights?q={flight_query}",
            note="일정과 운임 추세를 비교한 뒤 수하물 포함 여부를 확인하세요.",
            priority=10,
        ),
        VerificationLink(
            category="flight",
            platform="Skyscanner",
            title="다른 판매처 항공권 교차 비교",
            url=(
                "https://www.skyscanner.co.kr/transport/flights/"
                f"{origin.lower()}/{destination.lower()}/{_skyscanner_date(request.departure_date)}/"
                f"{_skyscanner_date(request.return_date)}/"
            ),
            note="표시가가 결제 단계에서도 유지되는지 판매처별로 확인하세요.",
            priority=20,
        ),
        VerificationLink(
            category="flight",
            platform="KAYAK",
            title="시간·환승 조건까지 재비교",
            url=(
                f"https://www.kayak.co.kr/flights/{origin}-{destination}/"
                f"{request.departure_date.isoformat()}/{request.return_date.isoformat()}?sort=bestflight_a"
            ),
            note="같은 운임의 환승·공항 변경·변경 조건을 비교하세요.",
            priority=30,
        ),
        VerificationLink(
            category="flight",
            platform="네이버 항공권",
            title="원화·국내 카드 조건 확인",
            url="https://flight.naver.com/",
            note=f"{origin} → {destination}, {request.departure_date}~{request.return_date} 조건을 입력하세요.",
            priority=40,
        ),
        VerificationLink(
            category="stay",
            platform="Booking.com",
            title="객실 수 기준 숙소 재고·총액 확인",
            url=f"https://www.booking.com/searchresults.ko.html?{booking_query}",
            note="세금·리조트피·취소기한을 결제 직전 총액에서 다시 확인하세요.",
            priority=10,
        ),
        VerificationLink(
            category="stay",
            platform="Google Hotels",
            title="숙소 판매처별 가격 비교",
            url=(
                f"https://www.google.com/travel/hotels/{city_query}?q={city_query}"
                f"&checkin={request.departure_date.isoformat()}&checkout={request.return_date.isoformat()}"
            ),
            note="동일 객실 유형과 취소 조건인지 확인한 뒤 비교하세요.",
            priority=20,
        ),
        VerificationLink(
            category="official",
            platform=official["guide"][0],
            title=f"{request.destination_city} 공식 관광정보 확인",
            url=official["guide"][1],
            note="관광지 운영시간·행사·공식 안내를 우선 확인하세요.",
            priority=10,
        ),
        VerificationLink(
            category="route",
            platform=official["transport"][0],
            title="공식 대중교통 요금·운행 확인",
            url=official["transport"][1],
            note="패스·요금·공사·운휴 정보는 운영사 공지를 기준으로 확인하세요.",
            priority=10,
        ),
        VerificationLink(
            category="place",
            platform="Google Maps",
            title="장소 영업시간과 실제 이동경로 확인",
            url=f"https://www.google.com/maps/search/?api=1&query={city_query}+attractions",
            note="방문 당일 영업 상태와 길찾기 결과를 다시 확인하세요.",
            priority=20,
        ),
    ]
    if request.ground_transport.mode == "rental_car":
        links.extend(
            [
                VerificationLink(
                    category="route",
                    platform="KAYAK 렌터카",
                    title="렌터카 차종·공항 지점 총액 확인",
                    url=f"https://www.kayak.co.kr/cars/{city_query}",
                    note="목적지 지점을 다시 지정하고 차종, 운전자 나이, 보험·세금과 보증금을 최종 화면에서 확인하세요.",
                    priority=20,
                ),
                VerificationLink(
                    category="route",
                    platform="Rentalcars.com",
                    title="렌터카 특가 교차 비교",
                    url=f"https://www.rentalcars.com/SearchResults.do?locationName={city_query}",
                    note="동일 차급·보험·연료정책 조건으로 비교하고 실제 보장 모델인지 확인하세요.",
                    priority=30,
                ),
            ]
        )
    return sorted(links, key=lambda item: (item.category, item.priority))


def build_guided_research_evidence(request: TripRequest, sample_verticals: list[str]) -> list[EvidenceRecord]:
    now = datetime.now(timezone.utc)
    destination = _destination_code(request)
    official = OFFICIAL_CITY_SOURCES.get(destination)
    evidence = [
        EvidenceRecord(
            id="planning-baseline",
            title="계획용 예산·일정 기준값",
            source_name="앱 내 대표도시 샘플 카탈로그",
            source_url="",
            source_type="planning_baseline",
            confidence="D",
            value_status="estimated",
            observed_at=now,
            note=f"{', '.join(sample_verticals)} 영역은 예약 가능한 상품이 아니라 일정 계산용 추정치입니다.",
            verification_required=True,
        ),
    ]
    if official:
        evidence.extend(
            [
                EvidenceRecord(
                    id="official-city-guide",
                    title=f"{request.destination_city} 공식 관광정보 검증처",
                    source_name=official["guide"][0],
                    source_url=official["guide"][1],
                    source_type="official_site",
                    confidence="B",
                    value_status="reference",
                    observed_at=None,
                    note="운영시간·휴무·공식 입장료를 확인할 우선 출처입니다. 앱이 값을 자동 수집한 것은 아닙니다.",
                    verification_required=True,
                ),
                EvidenceRecord(
                    id="official-transport",
                    title="현지 교통요금 검증처",
                    source_name=official["transport"][0],
                    source_url=official["transport"][1],
                    source_type="official_site",
                    confidence="B",
                    value_status="reference",
                    observed_at=None,
                    note="교통비·패스·운휴는 공식 운영사에서 최종 확인해야 합니다.",
                    verification_required=True,
                ),
            ]
        )
    else:
        evidence.append(
            EvidenceRecord(
                id="official-safety-start",
                title=f"{request.destination_city} 입국·안전 조사 시작점",
                source_name="외교부 해외안전여행",
                source_url="https://www.0404.go.kr/",
                source_type="official_site",
                confidence="B",
                value_status="reference",
                observed_at=None,
                note="신규 목적지는 관광·교통 공식 출처가 검증되기 전까지 조사 중으로 표시합니다.",
                verification_required=True,
            )
        )
    return evidence
