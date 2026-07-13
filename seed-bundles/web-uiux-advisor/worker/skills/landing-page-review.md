---
name: landing-page-review
description: Use when reviewing a landing page or marketing/home page. Covers the section-by-section checklist (above-fold, mid, bottom), the four layout types with their best-fit conditions, and common failure patterns.
---

# 랜딩페이지 리뷰 프레임

랜딩페이지는 "제작" 스킬을 **평가 프레임으로 역변환**해 본다. 만들 때의 체크리스트를 "이게 있는가/제 위치에 있는가"로 뒤집어 진단한다.

## 섹션별 체크

### Above-fold (폴드 위) — 5요소
스크롤 없이 5초 안에 회상돼야 한다. 빠진 요소가 최우선 미스다. [[above-the-fold-priority]]

1. **가치제안 헤드라인** — 이 문장만 읽어도 무엇을·누구에게 파는지 아는가? 슬로건처럼 읽히면 명확성 미스.
2. **서브헤드** — 헤드라인을 한 겹 보강하는가?
3. **단일 1차 CTA** — 목표 행동 하나가 명확·크게 있는가? 경쟁 CTA 과다는 Hick 미스. [[hicks-law]]
4. **제품 비주얼/데모** — 무엇인지 즉시 보이는가?
5. **신뢰 신호** — 로고·후기·수치가 폴드 근처에 있는가?

### Mid (본문)
- 혜택 중심 설명(기능 나열이 아니라 "그래서 사용자가 얻는 것").
- 오브젝션 해소(가격·신뢰·난이도 반론을 발생 지점에서).
- 사회적 증거(후기·사례)가 결정 지점 근처에 배치됐는가.
- 정보 위계가 스캔 가능한가. [[visual-hierarchy]]

### Bottom (하단)
- 재확인 CTA(폴드에서 결정 못 한 사용자를 위한 두 번째 기회).
- FAQ(질문으로 위장한 반론 목록).
- 푸터 신뢰 요소(회사 정보·정책·연락처).

## 4개 레이아웃 타입과 적합 조건

| 타입 | 특징 | Best when |
| --- | --- | --- |
| **Hero-centric** | 큰 히어로 + 단일 CTA | 단일 제품·단일 전환 목표가 명확할 때 |
| **Long-form scroll** | 스크롤텔링으로 설득을 쌓음 | 고관여·고가·설명이 필요한 제품 |
| **Split / feature-grid** | 좌우 분할·기능 그리드 | 다기능 SaaS, 기능 비교가 핵심일 때 |
| **Directory / catalog** | 카드·필터 중심 | 항목 탐색이 목적(마켓·리스팅), 검색·필터가 1차 [[search-vs-browse]] |

레이아웃이 서비스 목표와 어긋나면(예: 탐색형 서비스에 Hero-centric) 그 자체가 구조 미스다.

## 공통 실패 패턴

- **CTA 과다·경쟁** — 폴드 위 1차 CTA가 여럿이라 무엇을 눌러야 할지 모른다. [[hicks-law]]
- **모호한 가치제안** — 헤드라인이 슬로건·자화자찬이라 무엇을 파는지 모른다.
- **증거 하단 매몰** — 후기·수치가 폴드에서 멀어 신뢰가 결정 지점에 없다.
- **낮은 대비·약한 위계** — 중요한 것과 덜 중요한 것이 같은 무게. [[wcag-aa-checklist]]
- **hover 의존** — 데스크톱에서만 보이는 메뉴·정보가 터치에서 사라진다. [[thumb-zone-mobile]]
- **빈 상태 방치** — 무결과·최초 진입 화면에 안내가 없다. [[empty-state-onboarding]]

구조 참고: MengTo/Skills `landing-page` (MIT)의 제작용 구조(Before-you-design 질문지·Core structure·Layout types·Common pitfalls)를 제작→평가 프레임으로 역변환.
