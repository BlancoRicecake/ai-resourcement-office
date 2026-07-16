# 한국인 해외여행 설계 에이전트

한국 출발 여행자를 위해 항공권, 숙소, 장소와 이동 동선을 한 화면에서 비교하는 로컬 실행형 FastAPI 번들입니다. 도쿄·오사카·뉴욕·LA는 검증 지원하고, 다른 목적지는 공식 출처와 공급자 범위를 수집하는 초기세팅부터 시작합니다.

## 주요 기능

- Amadeus 항공·숙소 실시간 검색과 샘플 데이터 폴백
- Google Places·Routes 기반 장소 및 이동시간 조회
- 가격, 수하물, 환승 위험, 객실, 취소 조건과 데이터 시각 표시
- 세 가지 일정 변형과 각 경로의 장단점
- 동의한 사용자만 로컬 SQLite에 여행 취향 저장
- 사용자가 요청할 때 가격 새로고침 및 현지 재계획
- 여행 API 미연결 시 계획용 추정치, 공식 출처와 날짜·인원 기반 가격 비교 링크 제공
- 필수 방문지를 일정에 고정하고 우천 재계획에서도 보존
- 예약은 외부 공급자 페이지에서 사용자가 직접 완료
- 신규 목적지는 `조사 중 → 임시 지원 → 검증 지원` 상태로 관리하고 다른 도시의 샘플을 섞지 않음
- 목적지별 입국·안전·공항·교통·가격·관광정보 조사 체크리스트와 출처 제공

## 빠른 시작

```powershell
cd app
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
uvicorn travel_planner.main:app --reload
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. 여행 API 키가 없으면 대표 도시 계획 기준값으로 일정을 계산하고 Google Flights, Skyscanner, KAYAK, 네이버 항공권, Booking.com, Google Hotels와 공식 관광·교통 사이트의 검증 링크를 제공합니다. 표시 금액은 예약 가능한 실시간 상품이 아닙니다.

## API 키

- 기본 LLM: `OPENAI_API_KEY`
- 실시간 항공·숙소: `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET`
- 장소·경로: `GOOGLE_MAPS_API_KEY`
- 선택 공급자: Booking.com과 Skyscanner 파트너 승인 키

Booking.com·Skyscanner 어댑터는 자격 증명과 파트너 계약을 얻은 뒤 키를 설정하면 공통 공급자 인터페이스를 통해 자동으로 검색에 참여합니다.

## 신규 목적지 초기세팅

대화창에 `가을에 파리로 6박 7일 가고 싶어`처럼 입력하면 목적지 팩을 만들고 공식 출처, 공급자 지원, 현지 교통·비용, 관광지 운영정보의 확인 상태를 보여줍니다. 웹 검색 도구가 없는 독립 실행 앱은 자동 수집했다고 표현하지 않고 공식·비교 플랫폼 링크를 제공합니다.

- `GET /api/destinations`: 목적지 팩 목록
- `POST /api/destinations/bootstrap`: 새 목적지 조사 팩 생성
- `GET /api/destinations/{slug}`: 조사 상태와 출처 조회

검증 전 목적지는 가격·장소·동선을 다른 도시의 샘플로 대체하지 않으며 연구용 부분 결과만 반환합니다.

## 공개용 번들 만들기

```powershell
py scripts/build_release.py --check-only
py scripts/build_release.py
```

`dist/`에 허용 목록 기반 ZIP을 생성합니다. `.env`, `.venv`, SQLite DB, 로그와 캐시는 포함하지 않습니다.

## 책임과 한계

이 번들은 호스팅 서비스가 아닙니다. 사용자가 자신의 환경, API 키와 비용으로 실행합니다. 가격과 재고는 검색 후 바뀔 수 있으며, 입국·비자·안전 정보와 실제 예약 조건은 반드시 공식 사이트와 예약 페이지에서 다시 확인해야 합니다.
