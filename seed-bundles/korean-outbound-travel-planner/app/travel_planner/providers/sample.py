from __future__ import annotations

import math
from datetime import datetime, time, timedelta, timezone
from urllib.parse import quote_plus

from .base import PlaceRouteProvider, TravelInventoryProvider
from ..models import FlightOffer, FlightSegment, PlaceCandidate, StayOffer, TripRequest


CITY_CONFIG = {
    "도쿄": {"code": "TYO", "currency": "JPY", "lat": 35.6812, "lng": 139.7671, "timezone": "Asia/Tokyo"},
    "tokyo": {"code": "TYO", "currency": "JPY", "lat": 35.6812, "lng": 139.7671, "timezone": "Asia/Tokyo"},
    "오사카": {"code": "OSA", "currency": "JPY", "lat": 34.6937, "lng": 135.5023, "timezone": "Asia/Tokyo"},
    "osaka": {"code": "OSA", "currency": "JPY", "lat": 34.6937, "lng": 135.5023, "timezone": "Asia/Tokyo"},
    "뉴욕": {"code": "NYC", "currency": "USD", "lat": 40.7527, "lng": -73.9772, "timezone": "America/New_York"},
    "new york": {"code": "NYC", "currency": "USD", "lat": 40.7527, "lng": -73.9772, "timezone": "America/New_York"},
    "로스앤젤레스": {"code": "LAX", "currency": "USD", "lat": 34.0522, "lng": -118.2437, "timezone": "America/Los_Angeles"},
    "los angeles": {"code": "LAX", "currency": "USD", "lat": 34.0522, "lng": -118.2437, "timezone": "America/Los_Angeles"},
}


CITY_PLACES = {
    "TYO": [
        ("센소지", "浅草寺", "attraction", 35.7148, 139.7967, 0, 4.5, 82000, False),
        ("도쿄 국립박물관", "東京国立博物館", "attraction", 35.7188, 139.7765, 9000, 4.5, 26000, True),
        ("메이지 신궁", "明治神宮", "park", 35.6764, 139.6993, 0, 4.6, 39000, False),
        ("시부야 스카이", "SHIBUYA SKY", "attraction", 35.6584, 139.7017, 22000, 4.6, 19000, True),
        ("츠키지 장외시장 식당", "築地場外市場", "restaurant", 35.6655, 139.7707, 25000, 4.3, 15000, True),
        ("우에노 로컬 식당", "上野食堂", "restaurant", 35.7119, 139.7770, 15000, 4.4, 3200, True),
        ("키사텐 카페", "喫茶店", "cafe", 35.6938, 139.7034, 9000, 4.5, 1800, True),
        ("도쿄역 마루노우치", "東京駅丸の内駅舎", "shopping", 35.6812, 139.7671, 0, 4.6, 48000, True),
    ],
    "OSA": [
        ("오사카성", "大阪城", "attraction", 34.6873, 135.5262, 6000, 4.4, 71000, False),
        ("가이유칸", "海遊館", "attraction", 34.6545, 135.4289, 26000, 4.6, 38000, True),
        ("도톤보리", "道頓堀", "shopping", 34.6687, 135.5013, 0, 4.4, 92000, False),
        ("우메다 스카이 빌딩", "梅田スカイビル", "attraction", 34.7053, 135.4900, 15000, 4.5, 34000, True),
        ("쿠로몬 시장 식당", "黒門市場", "restaurant", 34.6653, 135.5066, 22000, 4.2, 26000, True),
        ("오코노미야키 식당", "お好み焼き", "restaurant", 34.6691, 135.5010, 16000, 4.5, 5600, True),
        ("나카자키초 카페", "中崎町カフェ", "cafe", 34.7070, 135.5050, 8000, 4.5, 2100, True),
        ("신세카이", "新世界", "shopping", 34.6525, 135.5063, 0, 4.1, 31000, False),
    ],
    "NYC": [
        ("센트럴 파크", "Central Park", "park", 40.7812, -73.9665, 0, 4.8, 290000, False),
        ("메트로폴리탄 미술관", "The Metropolitan Museum of Art", "attraction", 40.7794, -73.9632, 42000, 4.8, 91000, True),
        ("하이 라인", "The High Line", "park", 40.7480, -74.0048, 0, 4.7, 64000, False),
        ("탑 오브 더 록", "Top of the Rock", "attraction", 40.7593, -73.9794, 62000, 4.7, 58000, True),
        ("첼시 마켓 식당", "Chelsea Market", "restaurant", 40.7424, -74.0061, 32000, 4.5, 53000, True),
        ("코리아타운 로컬 식당", "Koreatown Local Dining", "restaurant", 40.7477, -73.9869, 28000, 4.4, 6300, True),
        ("브라이언트 파크 카페", "Bryant Park Cafe", "cafe", 40.7536, -73.9832, 15000, 4.4, 5100, True),
        ("그랜드 센트럴 터미널", "Grand Central Terminal", "attraction", 40.7527, -73.9772, 0, 4.7, 96000, True),
    ],
    "LAX": [
        ("그리피스 천문대", "Griffith Observatory", "attraction", 34.1184, -118.3004, 0, 4.7, 160000, True),
        ("게티 센터", "The Getty Center", "attraction", 34.0780, -118.4741, 0, 4.8, 34000, True),
        ("산타모니카 피어", "Santa Monica Pier", "attraction", 34.0099, -118.4960, 0, 4.6, 120000, False),
        ("더 브로드", "The Broad", "attraction", 34.0544, -118.2507, 0, 4.7, 17000, True),
        ("그랜드 센트럴 마켓", "Grand Central Market", "restaurant", 34.0509, -118.2487, 28000, 4.5, 51000, True),
        ("코리아타운 식당", "Koreatown Dining", "restaurant", 34.0618, -118.3006, 30000, 4.5, 4400, True),
        ("아트 디스트릭트 카페", "Arts District Cafe", "cafe", 34.0406, -118.2328, 14000, 4.6, 2700, True),
        ("베니스 운하", "Venice Canals", "park", 33.9834, -118.4676, 0, 4.5, 13000, False),
    ],
}


# LA는 넓은 도시권 특성을 검증할 수 있도록 권역·관심사·우천 적합도를 명시한다.
LA_PLACE_RECORDS = [
    # Downtown / Arts District
    {"name": "더 브로드", "local": "The Broad", "category": "attraction", "district": "DTLA·아트 디스트릭트", "lat": 34.0544, "lng": -118.2507, "cost": 0, "rating": 4.7, "reviews": 17000, "rain": True, "tags": ["미술", "건축", "박물관"], "duration": 120},
    {"name": "월트 디즈니 콘서트홀", "local": "Walt Disney Concert Hall", "category": "attraction", "district": "DTLA·아트 디스트릭트", "lat": 34.0553, "lng": -118.2498, "cost": 0, "rating": 4.7, "reviews": 12000, "rain": True, "tags": ["건축", "음악"], "duration": 75},
    {"name": "그랜드 센트럴 마켓", "local": "Grand Central Market", "category": "restaurant", "district": "DTLA·아트 디스트릭트", "lat": 34.0509, "lng": -118.2487, "cost": 28000, "rating": 4.5, "reviews": 51000, "rain": True, "tags": ["현지 음식", "시장"], "duration": 75},
    {"name": "아트 디스트릭트 카페", "local": "Arts District Cafe", "category": "cafe", "district": "DTLA·아트 디스트릭트", "lat": 34.0406, "lng": -118.2328, "cost": 14000, "rating": 4.6, "reviews": 2700, "rain": True, "tags": ["카페", "로컬"], "duration": 60},
    {"name": "전미일본계박물관", "local": "Japanese American National Museum", "category": "attraction", "district": "DTLA·아트 디스트릭트", "lat": 34.0494, "lng": -118.2385, "cost": 24000, "rating": 4.7, "reviews": 2800, "rain": True, "tags": ["역사", "박물관", "건축"], "duration": 120},
    # Hollywood / Los Feliz
    {"name": "그리피스 천문대", "local": "Griffith Observatory", "category": "attraction", "district": "할리우드·로스펠리스", "lat": 34.1184, "lng": -118.3004, "cost": 0, "rating": 4.7, "reviews": 160000, "rain": False, "tags": ["건축", "전망", "과학"], "duration": 120},
    {"name": "할리우드 명예의 거리", "local": "Hollywood Walk of Fame", "category": "shopping", "district": "할리우드·로스펠리스", "lat": 34.1016, "lng": -118.3269, "cost": 0, "rating": 4.0, "reviews": 52000, "rain": False, "tags": ["영화", "할리우드"], "duration": 75},
    {"name": "TCL 차이니즈 시어터", "local": "TCL Chinese Theatre", "category": "attraction", "district": "할리우드·로스펠리스", "lat": 34.1020, "lng": -118.3409, "cost": 35000, "rating": 4.4, "reviews": 21000, "rain": True, "tags": ["영화", "건축", "역사"], "duration": 75},
    {"name": "무소 앤 프랭크 그릴", "local": "Musso & Frank Grill", "category": "restaurant", "district": "할리우드·로스펠리스", "lat": 34.1018, "lng": -118.3354, "cost": 55000, "rating": 4.5, "reviews": 3500, "rain": True, "tags": ["영화", "현지 음식", "역사"], "duration": 90},
    {"name": "로스펠리스 타코 식당", "local": "Los Feliz Taco Dining", "category": "restaurant", "district": "할리우드·로스펠리스", "lat": 34.1067, "lng": -118.2875, "cost": 18000, "rating": 4.5, "reviews": 2100, "rain": True, "tags": ["현지 음식", "로컬"], "duration": 60},
    {"name": "파라마운트 픽처스 스튜디오 투어", "local": "Paramount Pictures Studio Tour", "category": "attraction", "district": "할리우드·로스펠리스", "lat": 34.0833, "lng": -118.3190, "cost": 95000, "rating": 4.6, "reviews": 4300, "rain": False, "tags": ["영화", "스튜디오"], "duration": 120},
    # Museum Row / Mid-City
    {"name": "아카데미 영화 박물관", "local": "Academy Museum of Motion Pictures", "category": "attraction", "district": "뮤지엄 로우·미드시티", "lat": 34.0634, "lng": -118.3607, "cost": 38000, "rating": 4.6, "reviews": 6200, "rain": True, "tags": ["영화", "박물관", "건축"], "duration": 150},
    {"name": "피터슨 자동차 박물관", "local": "Petersen Automotive Museum", "category": "attraction", "district": "뮤지엄 로우·미드시티", "lat": 34.0622, "lng": -118.3611, "cost": 35000, "rating": 4.7, "reviews": 12000, "rain": True, "tags": ["자동차", "박물관", "건축"], "duration": 120},
    {"name": "로스앤젤레스 카운티 미술관", "local": "LACMA", "category": "attraction", "district": "뮤지엄 로우·미드시티", "lat": 34.0638, "lng": -118.3590, "cost": 36000, "rating": 4.6, "reviews": 19000, "rain": True, "tags": ["미술", "박물관", "건축"], "duration": 150},
    {"name": "오리지널 파머스 마켓", "local": "Original Farmers Market", "category": "restaurant", "district": "뮤지엄 로우·미드시티", "lat": 34.0720, "lng": -118.3615, "cost": 30000, "rating": 4.6, "reviews": 26000, "rain": True, "tags": ["현지 음식", "시장"], "duration": 75},
    {"name": "레퓌블리크 카페", "local": "Republique Cafe Bakery", "category": "cafe", "district": "뮤지엄 로우·미드시티", "lat": 34.0641, "lng": -118.3437, "cost": 25000, "rating": 4.5, "reviews": 9600, "rain": True, "tags": ["카페", "건축", "브런치"], "duration": 75},
    # Westside / Brentwood
    {"name": "게티 센터", "local": "The Getty Center", "category": "attraction", "district": "웨스트사이드·브렌트우드", "lat": 34.0780, "lng": -118.4741, "cost": 0, "rating": 4.8, "reviews": 34000, "rain": True, "tags": ["미술", "건축", "박물관"], "duration": 180},
    {"name": "해머 미술관", "local": "Hammer Museum", "category": "attraction", "district": "웨스트사이드·브렌트우드", "lat": 34.0597, "lng": -118.4439, "cost": 0, "rating": 4.5, "reviews": 3100, "rain": True, "tags": ["미술", "박물관"], "duration": 120},
    {"name": "소텔 재팬타운 식당", "local": "Sawtelle Japantown Dining", "category": "restaurant", "district": "웨스트사이드·브렌트우드", "lat": 34.0397, "lng": -118.4425, "cost": 30000, "rating": 4.5, "reviews": 5400, "rain": True, "tags": ["현지 음식", "아시아 음식"], "duration": 75},
    {"name": "웨스트우드 로컬 카페", "local": "Westwood Local Cafe", "category": "cafe", "district": "웨스트사이드·브렌트우드", "lat": 34.0619, "lng": -118.4468, "cost": 15000, "rating": 4.5, "reviews": 1900, "rain": True, "tags": ["카페", "로컬"], "duration": 60},
    {"name": "UCLA 조각 정원", "local": "UCLA Franklin D. Murphy Sculpture Garden", "category": "park", "district": "웨스트사이드·브렌트우드", "lat": 34.0725, "lng": -118.4403, "cost": 0, "rating": 4.6, "reviews": 950, "rain": False, "tags": ["미술", "건축", "산책"], "duration": 75},
    # Santa Monica / Venice
    {"name": "산타모니카 피어", "local": "Santa Monica Pier", "category": "attraction", "district": "산타모니카·베니스", "lat": 34.0099, "lng": -118.4960, "cost": 0, "rating": 4.6, "reviews": 120000, "rain": False, "tags": ["해변", "전망"], "duration": 120},
    {"name": "베니스 운하", "local": "Venice Canals", "category": "park", "district": "산타모니카·베니스", "lat": 33.9834, "lng": -118.4676, "cost": 0, "rating": 4.5, "reviews": 13000, "rain": False, "tags": ["해변", "건축", "산책"], "duration": 75},
    {"name": "서드 스트리트 프롬나드", "local": "Third Street Promenade", "category": "shopping", "district": "산타모니카·베니스", "lat": 34.0154, "lng": -118.4973, "cost": 0, "rating": 4.5, "reviews": 17000, "rain": False, "tags": ["쇼핑", "거리"], "duration": 90},
    {"name": "애벗 키니 카페", "local": "Abbot Kinney Cafe", "category": "cafe", "district": "산타모니카·베니스", "lat": 33.9906, "lng": -118.4644, "cost": 16000, "rating": 4.6, "reviews": 2400, "rain": True, "tags": ["카페", "로컬"], "duration": 60},
    {"name": "산타모니카 시푸드 식당", "local": "Santa Monica Seafood Dining", "category": "restaurant", "district": "산타모니카·베니스", "lat": 34.0180, "lng": -118.4898, "cost": 45000, "rating": 4.5, "reviews": 5100, "rain": True, "tags": ["현지 음식", "해산물"], "duration": 90},
    {"name": "뮤지엄 오브 플라잉", "local": "Museum of Flying", "category": "attraction", "district": "산타모니카·베니스", "lat": 34.0155, "lng": -118.4496, "cost": 20000, "rating": 4.6, "reviews": 1600, "rain": True, "tags": ["항공", "박물관"], "duration": 90},
    # Studio / Valley
    {"name": "워너브라더스 스튜디오 투어", "local": "Warner Bros. Studio Tour Hollywood", "category": "attraction", "district": "스튜디오·밸리", "lat": 34.1482, "lng": -118.3380, "cost": 105000, "rating": 4.7, "reviews": 12000, "rain": True, "tags": ["영화", "스튜디오"], "duration": 180},
    {"name": "유니버설 스튜디오 할리우드", "local": "Universal Studios Hollywood", "category": "attraction", "district": "스튜디오·밸리", "lat": 34.1381, "lng": -118.3534, "cost": 155000, "rating": 4.6, "reviews": 150000, "rain": False, "tags": ["영화", "스튜디오", "테마파크"], "duration": 360},
    {"name": "오트리 미국 서부 박물관", "local": "Autry Museum of the American West", "category": "attraction", "district": "스튜디오·밸리", "lat": 34.1487, "lng": -118.2828, "cost": 22000, "rating": 4.7, "reviews": 2100, "rain": True, "tags": ["역사", "박물관"], "duration": 120},
    {"name": "스튜디오 시티 카페", "local": "Studio City Cafe", "category": "cafe", "district": "스튜디오·밸리", "lat": 34.1394, "lng": -118.3871, "cost": 15000, "rating": 4.5, "reviews": 1800, "rain": True, "tags": ["카페", "영화"], "duration": 60},
    {"name": "유니버설 시티워크 식당", "local": "Universal CityWalk Dining", "category": "restaurant", "district": "스튜디오·밸리", "lat": 34.1362, "lng": -118.3543, "cost": 35000, "rating": 4.4, "reviews": 9800, "rain": True, "tags": ["현지 음식", "영화"], "duration": 90},
]


INTEREST_ALIASES = {
    "영화": ("영화", "cinema", "movie", "스튜디오", "studio", "할리우드"),
    "건축": ("건축", "architecture", "디자인"),
    "해변": ("해변", "바다", "beach", "coast"),
    "현지 음식": ("현지 음식", "맛집", "음식", "food", "restaurant"),
    "카페": ("카페", "coffee", "cafe"),
    "미술": ("미술", "art", "박물관", "museum"),
}


def _interest_match(tags: list[str], interests: list[str], category: str) -> float:
    requested = " ".join(interests).lower()
    if not requested:
        return 0.6
    matched = 0
    for tag in tags:
        aliases = INTEREST_ALIASES.get(tag, (tag,))
        if any(alias.lower() in requested for alias in aliases):
            matched += 1
    if category == "restaurant" and any(word in requested for word in ("음식", "맛집", "food")):
        matched += 1
    if category == "cafe" and any(word in requested for word in ("카페", "coffee", "cafe")):
        matched += 1
    return min(1.0, 0.55 + matched * 0.35)


def city_config(request: TripRequest) -> dict:
    key = request.destination_city.strip().lower()
    config = CITY_CONFIG.get(key)
    if config:
        return config
    code = request.destination_code or ("TYO" if request.destination_country == "JP" else "NYC")
    fallback = CITY_CONFIG["도쿄" if request.destination_country == "JP" else "뉴욕"].copy()
    fallback["code"] = code
    return fallback


def haversine_km(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
    radius = 6371.0
    p1, p2 = math.radians(a_lat), math.radians(b_lat)
    dp = math.radians(b_lat - a_lat)
    dl = math.radians(b_lng - a_lng)
    value = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


class SampleProvider(TravelInventoryProvider, PlaceRouteProvider):
    name = "sample"

    async def search_flights(self, request: TripRequest) -> list[FlightOffer]:
        cfg = city_config(request)
        now = datetime.now(timezone.utc)
        destination = cfg["code"]
        long_haul = request.destination_country == "US"
        base = 1_250_000 if long_haul else 430_000
        traveler_multiplier = request.adults + request.children * 0.75
        options = [
            ("균형 직항", base, 0, 850 if long_haul else 150, "included" if request.checked_baggage else "unknown"),
            ("절약 경유", int(base * 0.82), 1, 1080 if long_haul else 310, "excluded"),
            ("편안한 직항", int(base * 1.18), 0, 820 if long_haul else 140, "included"),
        ]
        offers: list[FlightOffer] = []
        for index, (label, amount, stops, duration, baggage) in enumerate(options, 1):
            departure = datetime.combine(request.departure_date, time(9 + index, 10), tzinfo=timezone.utc)
            arrival = departure + timedelta(minutes=duration)
            total_krw = int(amount * traveler_multiplier)
            offers.append(
                FlightOffer(
                    id=f"sample-flight-{destination}-{index}",
                    provider="샘플 데이터",
                    total_price=total_krw,
                    currency="KRW",
                    total_price_krw=total_krw,
                    taxes_included=True,
                    baggage_status=baggage,
                    stops=stops,
                    duration_minutes=duration,
                    change_policy="샘플 조건 — 실제 운임 확인 필요",
                    cancellation_policy="샘플 조건 — 실제 운임 확인 필요",
                    segments=[
                        FlightSegment(
                            origin=request.origin_airport,
                            destination=destination,
                            departure_at=departure,
                            arrival_at=arrival,
                            carrier="SAMPLE",
                            flight_number=str(100 + index),
                            duration_minutes=duration,
                        )
                    ],
                    booking_url=f"https://www.google.com/travel/flights?q={quote_plus(request.origin_airport + ' to ' + destination + ' ' + str(request.departure_date))}",
                    observed_at=now,
                    score_reasons=[label, "API 키가 없어 가격·재고가 검증되지 않은 예시입니다."],
                )
            )
        return offers

    async def search_stays(self, request: TripRequest) -> list[StayOffer]:
        cfg = city_config(request)
        now = datetime.now(timezone.utc)
        nights = (request.return_date - request.departure_date).days
        nightly = 240_000 if request.destination_country == "US" else 130_000
        catalog = {
            "hotel": ("시티 센터 호텔", 1.0),
            "motel": ("실속형 모텔", 0.72),
            "guesthouse": ("로컬 게스트하우스", 0.62),
            "ryokan": ("료칸 검색", 1.28),
            "hostel": ("호스텔", 0.48),
            "vacation_rental": ("휴가용 임대 검색", 1.12),
            "apartment": ("서비스드 아파트", 1.08),
        }
        selected = [(stay_type, *catalog[stay_type]) for stay_type in request.stay_types if stay_type in catalog]
        offers: list[StayOffer] = []
        for index, (stay_type, label, factor) in enumerate(selected, 1):
            total = int(nightly * factor * nights * request.rooms)
            vacation = stay_type == "vacation_rental"
            offers.append(
                StayOffer(
                    id=f"sample-stay-{cfg['code']}-{index}",
                    provider="Airbnb 검색 링크" if vacation else "샘플 데이터",
                    name=f"{request.destination_city} {label}",
                    accommodation_type=stay_type,
                    address=f"{request.destination_city} 중심부 예시 위치",
                    latitude=cfg["lat"] + index * 0.006,
                    longitude=cfg["lng"] - index * 0.004,
                    total_price=total,
                    currency="KRW",
                    total_price_krw=total,
                    taxes_included=None if vacation else True,
                    rooms_requested=request.rooms,
                    available=True,
                    room_description=f"객실 {request.rooms}개 기준 샘플",
                    bed_count=2 if stay_type in {"hotel", "motel"} else 1,
                    amenities=["무료 Wi-Fi", "냉장고"] + (["피트니스"] if stay_type == "hotel" else []),
                    parking_available=True if stay_type in {"hotel", "motel"} else None,
                    parking_cost_krw_per_night=0 if stay_type == "motel" else (28_000 if stay_type == "hotel" else None),
                    cancellation_policy="가격·재고 미검증" if vacation else "샘플 조건 — 예약 페이지 확인 필요",
                    rating=None if vacation else round(4.1 + index * 0.12, 1),
                    review_count=None if vacation else 180 * index,
                    review_summary="샘플 리뷰 지표이며 실제 리뷰가 아닙니다.",
                    booking_url=(
                        f"https://www.airbnb.com/s/{quote_plus(request.destination_city)}/homes"
                        if vacation
                        else f"https://www.google.com/travel/hotels/{quote_plus(request.destination_city)}"
                    ),
                    observed_at=now,
                    verified_inventory=False,
                )
            )
        return offers

    async def search_places(self, request: TripRequest) -> list[PlaceCandidate]:
        cfg = city_config(request)
        now = datetime.now(timezone.utc)
        if cfg["code"] == "LAX":
            return [
                PlaceCandidate(
                    id=f"sample-place-LAX-{index}",
                    provider="샘플 데이터",
                    name=record["name"],
                    local_name=record["local"],
                    category=record["category"],
                    address=f"{record['district']} 예시 위치",
                    latitude=record["lat"],
                    longitude=record["lng"],
                    rating=record["rating"],
                    review_count=record["reviews"],
                    price_level=min(4, max(0, record["cost"] // 15000)),
                    estimated_cost_krw=record["cost"],
                    opening_hours=["샘플 영업시간 — 방문 전 공식 페이지 확인"],
                    weekday_hours=(
                        {0: [], 1: ["12:00-22:00"], 2: ["12:00-22:00"], 3: ["12:00-22:00"], 4: ["12:00-22:00"], 5: ["10:00-22:00"], 6: ["10:00-22:00"]}
                        if record["local"] == "Griffith Observatory"
                        else ({day: ["09:00-22:00"] for day in range(7)} if record["local"] == "Universal Studios Hollywood" else {})
                    ),
                    parking_cost_krw=(
                        56_000 if record["local"] == "Universal Studios Hollywood"
                        else (35_000 if record["local"] == "The Getty Center" else 0)
                    ),
                    business_status="OPERATIONAL",
                    maps_url=f"https://www.google.com/maps/search/?api=1&query={quote_plus(record['local'])}",
                    observed_at=now,
                    interest_match=_interest_match(record["tags"], request.interests, record["category"]),
                    rain_suitable=record["rain"],
                    district=record["district"],
                    interest_tags=record["tags"],
                    visit_duration_minutes=record["duration"],
                )
                for index, record in enumerate(LA_PLACE_RECORDS, 1)
            ]
        raw_places = CITY_PLACES.get(cfg["code"], CITY_PLACES["TYO" if request.destination_country == "JP" else "NYC"])
        result = []
        for index, (name, local, category, lat, lng, cost, rating, reviews, rain) in enumerate(raw_places, 1):
            result.append(
                PlaceCandidate(
                    id=f"sample-place-{cfg['code']}-{index}",
                    provider="샘플 데이터",
                    name=name,
                    local_name=local,
                    category=category,
                    address=f"{request.destination_city} 예시 주소",
                    latitude=lat,
                    longitude=lng,
                    rating=rating,
                    review_count=reviews,
                    price_level=min(4, max(0, cost // 15000)),
                    estimated_cost_krw=cost,
                    opening_hours=["샘플 영업시간 — 방문 전 공식 페이지 확인"],
                    business_status="OPERATIONAL",
                    maps_url=f"https://www.google.com/maps/search/?api=1&query={quote_plus(local)}",
                    observed_at=now,
                    interest_match=0.8 if category in {"attraction", "restaurant"} else 0.65,
                    rain_suitable=rain,
                )
            )
        return result

    async def route_matrix(
        self, places: list[PlaceCandidate], mode: str = "TRANSIT"
    ) -> dict[tuple[str, str], tuple[int, float]]:
        speed = 4.5 if mode == "WALK" else 18.0
        matrix: dict[tuple[str, str], tuple[int, float]] = {}
        for origin in places:
            for destination in places:
                distance = haversine_km(origin.latitude, origin.longitude, destination.latitude, destination.longitude)
                minutes = 0 if origin.id == destination.id else max(8, round(distance / speed * 60 + 5))
                matrix[(origin.id, destination.id)] = (minutes, round(distance, 2))
        return matrix
