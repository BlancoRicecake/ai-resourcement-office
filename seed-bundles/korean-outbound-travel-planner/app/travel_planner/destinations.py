from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from .models import (
    DestinationCapabilities,
    DestinationPack,
    DestinationResearchTask,
    DestinationSource,
)


CATALOG_PATH = Path(__file__).resolve().parent / "catalog" / "destinations.json"

COUNTRIES = {
    "일본": ("JP", "일본"),
    "미국": ("US", "미국"),
    "프랑스": ("FR", "프랑스"),
    "베트남": ("VN", "베트남"),
    "영국": ("GB", "영국"),
    "태국": ("TH", "태국"),
    "이탈리아": ("IT", "이탈리아"),
    "스페인": ("ES", "스페인"),
    "호주": ("AU", "호주"),
    "캐나다": ("CA", "캐나다"),
    "싱가포르": ("SG", "싱가포르"),
    "대만": ("TW", "대만"),
    "필리핀": ("PH", "필리핀"),
    "인도네시아": ("ID", "인도네시아"),
    "독일": ("DE", "독일"),
    "스위스": ("CH", "스위스"),
    "포르투갈": ("PT", "포르투갈"),
}


def _load_catalog() -> list[dict[str, Any]]:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


def _slug(country_code: str, city_name: str) -> str:
    digest = hashlib.sha1(f"{country_code}:{city_name}".encode("utf-8")).hexdigest()[:10]
    return f"{country_code.lower()}-{digest}"


def _tasks(status: str, has_identity: bool = True) -> list[DestinationResearchTask]:
    if status == "validated":
        return [
            DestinationResearchTask(key="identity", label="도시·공항·통화·시간대", status="ready", reason="번들 기준 데이터 검증 완료"),
            DestinationResearchTask(key="official_sources", label="관광·공항·교통 공식 출처", status="ready", reason="공식 출처 카탈로그 등록 완료"),
            DestinationResearchTask(key="providers", label="항공·숙소·장소 공급자 연결", status="ready", reason="지원 공급자와 샘플 계약 검증 완료"),
            DestinationResearchTask(key="costs", label="교통·숙박·관광 비용 기준", status="ready", reason="계획용 기준값과 계산 규칙 검증 완료"),
            DestinationResearchTask(key="safety", label="입국·안전 최신 정보", status="pending", reason="여행 시점마다 공식 기관에서 재확인"),
        ]
    return [
        DestinationResearchTask(key="identity", label="도시·공항·통화·시간대", status="ready" if has_identity else "pending", reason="카탈로그 기본값" if has_identity else "도시와 국가 코드 확인 필요"),
        DestinationResearchTask(key="entry_safety", label="입국·비자·여행경보", status="pending", reason="외교부와 목적지 정부의 최신 공지 확인 필요"),
        DestinationResearchTask(key="flight_stay", label="항공·숙소 공급자 지원과 가격", status="pending", reason="날짜·인원 조건으로 실시간 재고 확인 필요"),
        DestinationResearchTask(key="transport", label="현지 교통·렌터카·주차·유류비", status="pending", reason="현지 운영사와 공식 요금표 확인 필요"),
        DestinationResearchTask(key="places", label="관광지 운영시간·입장료·혼잡", status="pending", reason="공식 관광청과 시설 사이트 확인 필요"),
        DestinationResearchTask(key="seasonality", label="날씨·성수기·공휴일", status="pending", reason="여행 시기에 맞는 공식 기후·행사 자료 확인 필요"),
    ]


def _sources(raw: dict[str, Any]) -> list[DestinationSource]:
    city = raw["city_name"]
    now = datetime.now(timezone.utc) if raw.get("status") == "validated" else None
    source_status = "verified" if raw.get("status") == "validated" else "pending"
    result = [
        DestinationSource(category="entry", name="외교부 해외안전여행", url="https://www.0404.go.kr/", status="pending", note="입국 가능 여부는 목적지 정부 자료와 함께 여행 직전 재확인"),
        DestinationSource(category="safety", name="외교부 국가별 안전정보", url="https://www.0404.go.kr/", status="pending", note="여행경보와 사건·사고 공지 확인"),
    ]
    for category, key, label in (
        ("tourism", "tourism_url", f"{city} 공식 관광정보"),
        ("airport", "airport_url", f"{city} 주요 공항"),
        ("transport", "transport_url", f"{city} 공식 교통정보"),
    ):
        if raw.get(key):
            result.append(DestinationSource(category=category, name=label, url=raw[key], status=source_status, observed_at=now))
    query = quote_plus(city)
    result.extend(
        [
            DestinationSource(category="pricing", name="Google Flights", url=f"https://www.google.com/travel/flights?q={query}", source_type="comparison_platform", status="pending", note="정확한 날짜·출발지·인원을 입력해 재고 확인"),
            DestinationSource(category="pricing", name="Booking.com", url=f"https://www.booking.com/searchresults.ko.html?ss={query}", source_type="comparison_platform", status="pending", note="세금·수수료와 취소 조건 포함 총액 확인"),
            DestinationSource(category="map", name="Google Maps", url=f"https://www.google.com/maps/search/?api=1&query={query}", source_type="search_guide", status="pending", note="장소 영업 상태와 실제 이동시간 확인"),
        ]
    )
    return result


def pack_from_raw(raw: dict[str, Any]) -> DestinationPack:
    status = raw.get("status", "researching")
    capabilities = DestinationCapabilities(
        flight="live" if status == "validated" else "guided",
        stay="live" if status == "validated" else "guided",
        places="live" if status == "validated" else "guided",
        routes="live" if status == "validated" else "guided",
    )
    missing = []
    for field, label in (("city_code", "도시·공항 코드"), ("currency", "통화"), ("timezone", "시간대"), ("latitude", "좌표"), ("tourism_url", "공식 관광정보")):
        if raw.get(field) is None:
            missing.append(label)
    return DestinationPack(
        slug=raw["slug"],
        country_code=raw["country_code"],
        country_name=raw["country_name"],
        city_name=raw["city_name"],
        city_code=raw.get("city_code"),
        aliases=raw.get("aliases", []),
        currency=raw.get("currency"),
        timezone=raw.get("timezone"),
        latitude=raw.get("latitude"),
        longitude=raw.get("longitude"),
        summary=raw.get("summary", ""),
        status=status,
        capabilities=capabilities,
        sources=_sources(raw),
        research_tasks=_tasks(status, not missing),
        missing_fields=missing,
        last_verified_at=datetime.now(timezone.utc) if status == "validated" else None,
    )


CATALOG = [pack_from_raw(item) for item in _load_catalog()]


def country_match(text: str) -> tuple[str, str] | None:
    lowered = text.lower()
    for alias, value in COUNTRIES.items():
        if alias in lowered:
            return value
    return None


def find_catalog_destination(text: str) -> DestinationPack | None:
    lowered = text.strip().lower()
    candidates = sorted(CATALOG, key=lambda item: max((len(alias) for alias in item.aliases), default=0), reverse=True)
    for pack in candidates:
        for alias in sorted(pack.aliases, key=len, reverse=True):
            token = alias.lower()
            if token.isascii() and len(token) <= 3:
                matched = re.search(rf"(?<![a-z]){re.escape(token)}(?![a-z])", lowered)
            else:
                matched = token in lowered
            if matched:
                return pack.model_copy(deep=True)
    return None


def _extract_unknown_place(text: str) -> tuple[str, str, str] | None:
    compact = re.sub(r"\s+", " ", text.strip())
    patterns = [
        r"([가-힣A-Za-zÀ-ÿ][가-힣A-Za-zÀ-ÿ .'-]{1,45}?)(?:로|으로|에)?\s*(?:가고\s*싶|가보고\s*싶|여행하|여행\s*가|떠나)",
        r"(?:목적지는?|여행지는?)\s*([가-힣A-Za-zÀ-ÿ][가-힣A-Za-zÀ-ÿ .'-]{1,45})",
    ]
    candidate = None
    for pattern in patterns:
        match = re.search(pattern, compact, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,'\"")
            break
    if not candidate:
        return None
    candidate = re.sub(r"^(?:처음이라|잘 모르겠어|그냥|이번에는|다음에는)\s*", "", candidate)
    candidate = re.sub(r"(?:으로|로|에)$", "", candidate).strip()
    if candidate.split()[-1] in COUNTRIES:
        return None
    country_code, country_name = "ZZ", "확인 필요"
    for alias, (code, name) in COUNTRIES.items():
        if candidate.startswith(alias):
            country_code, country_name = code, name
            candidate = candidate[len(alias):].strip()
            break
    if not candidate or candidate in COUNTRIES:
        return None
    city_name = candidate.split()[-1] if re.search(r"[가-힣]", candidate) else candidate
    return country_code, country_name, city_name


def resolve_destination(text: str) -> DestinationPack | None:
    known = find_catalog_destination(text)
    if known:
        return known
    unknown = _extract_unknown_place(text)
    if not unknown:
        return None
    country_code, country_name, city_name = unknown
    raw = {
        "slug": _slug(country_code, city_name),
        "country_code": country_code,
        "country_name": country_name,
        "city_name": city_name,
        "aliases": [city_name],
        "summary": "처음 조사하는 목적지입니다. 공식 출처와 공급자 지원 범위를 확인한 뒤 임시 여행안을 준비합니다.",
        "status": "researching",
    }
    return pack_from_raw(raw)


def catalog_by_country(country_code: str) -> list[DestinationPack]:
    return [item.model_copy(deep=True) for item in CATALOG if item.country_code == country_code]


class DestinationRegistry:
    def __init__(self, database: Any):
        self.database = database

    def list(self, include_provisional: bool = True) -> list[DestinationPack]:
        saved = {item.slug: item for item in self.database.list_destination_packs()}
        for item in CATALOG:
            saved.setdefault(item.slug, item.model_copy(deep=True))
        values = list(saved.values())
        if not include_provisional:
            values = [item for item in values if item.status == "validated"]
        return sorted(values, key=lambda item: (item.status != "validated", item.country_name, item.city_name))

    def get(self, slug: str) -> DestinationPack | None:
        saved = self.database.get_destination_pack(slug)
        if saved:
            return saved
        return next((item.model_copy(deep=True) for item in CATALOG if item.slug == slug), None)

    def resolve(self, query: str) -> DestinationPack | None:
        for item in self.list():
            if query.strip().lower() in {item.city_name.lower(), item.slug.lower(), *(alias.lower() for alias in item.aliases)}:
                return item
        return resolve_destination(query)

    def bootstrap(self, query: str) -> DestinationPack:
        pack = self.resolve(query) or resolve_destination(f"{query} 여행 가고 싶어")
        if not pack:
            raw = {
                "slug": _slug("ZZ", query.strip()),
                "country_code": "ZZ",
                "country_name": "확인 필요",
                "city_name": query.strip(),
                "aliases": [query.strip()],
                "summary": "목적지 표준 정보부터 확인해야 합니다.",
                "status": "researching",
            }
            pack = pack_from_raw(raw)
        pack.updated_at = datetime.now(timezone.utc)
        self.database.save_destination_pack(pack)
        return pack
