---
id: korean-market-ux-patterns
title: 한국 시장 UX 관습
tags:
  - korea
  - convention
  - localization
source: seed
confidence: medium
created: 2026-07-13
---
**적용 조건: 이 노드는 인테이크에서 대상 시장이 한국으로 확인된 경우에만 적용한다.** 기본값은 시장 중립이며, 확인 전에는 보편 원칙만 쓴다. 한국 사용자를 대상으로 하는 서비스로 확인되면 로컬 관습을 함께 보고, 글로벌 베스트 프랙티스와 어긋날 때 한국 사용자의 기대를 우선할지 판단한다. **[H11]**

- **검색창 최상단 배치** — 네이버·야놀자·인터파크 등에서 굳어진 관습. 탐색보다 검색으로 시작하는 사용자가 많아, 검색 서비스는 검색바를 눈에 띄게 상단에 둔다. [[search-vs-browse]]
- **KRDS 필터 표준(전자정부)** — 정렬(정확도/최신/인기순), 기간 필터(1일/1주일/1개월+커스텀) 같은 공공 표준 패턴. 공공·정보 서비스 리뷰의 참고선.
- **토스(Toss) 원칙** — 공개 자료 기준으로 **신중 인용**한다: (1) 3초 안에 답할 수 없으면 어려운 질문 (2) 단순함 (3) 기능은 비용(최소 기능) (4) 임팩트 집중(빌드-배포-측정-학습). TDS가 디자인-개발 공통 언어 역할.

리뷰 관점:

- 관습을 절대 규칙으로 강요하지 않는다 — 타깃·서비스 성격에 맞는지 판단한다(글로벌 타깃이면 다르다).
- 토스 원칙 등은 특정 회사의 공개 방법론이므로 "OO의 공개 원칙에 따르면"으로 출처를 밝혀 인용한다.
- 폼·회원가입은 한국 관습(휴대폰 인증 등)과 마찰을 함께 본다. [[form-ux-best-practices]] · IA는 [[information-architecture-basics]].

출처: KRDS(전자정부 UI/UX 가이드) — https://uiux.egovframe.go.kr/guide/service/service_02_05.html , 토스 기술블로그 — https://toss.tech/article/insurance-claim-process
