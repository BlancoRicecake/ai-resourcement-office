# Build Log

## Source Problem

"타깃 고객을 찾아 리스트를 만든다"는 일은 보통 **닥치는 대로 긁는 스크레이핑**으로 귀결된다. 그러나 실제로
필요한 것은 양이 아니라 **연락하면 실제로 답할 사람** — 우리가 원하는 정체성(identity)을 갖고, 우리가 파는
것을 원한다는 신호(demand-intent)를 스스로 드러낸 사람이다. 이메일 만 개보다 근거(링크+인용) 붙은 3명이
낫다. 이 채널은 팀에 없었다: 스크레이퍼가 아니라 **근거 기반으로 사람을 골라내는 리서처**.

## MVP Scope

**발송하지 않는** 리드 디스커버리 전문 직원을 만든다. 대상 정의(2축 ICP)를 인터뷰로 확정하고 → 채널별로
느리고 read-only하게 탐색 → 인라인 dedup 게이트 → 연락처 추출 → 6축 투명 스코어링 → **리드 CSV +
비즈니스 워크 리포트**를 넘긴다. 접근 각도(approach angle)까지만 도출하고 **아웃리치 카피 작성·발송은
범위 밖**이다. 발송 합법성은 사용자 책임임을 문서에 못박는다.

## Design Inputs (2026-07-15)

- **파이프라인 (job-analyst → research → maker → training-camp)**: 직무 분석가가 직무·성공기준을
  설계 → 리서치가 ICP/intent/dedup/언어감지/법규 소스를 조사 → maker가 agent.md + 14노드 지식그래프 +
  8스킬 + 메모리 루프로 번들을 적재 → training-camp가 **감사(audit) + 졸업시험(exam)**으로 검수했다.
  이 패치 패스는 training-camp 단계에서 나온 지적을 반영한 것이다.
- **7개 확정 결정(locked decisions)**:
  1. **2축 ICP** — 리드는 정체성 축과 수요-의도 축의 **교차점**에만 존재한다. 한 축만 있으면 weak lead.
     ([H1] · [[two-axis-icp]])
  2. **품질 우선 상한(ceiling, not floor)** — 요청 수량은 바닥이 아니라 **천장**이다. 부족하면 채우지
     말고 qualified 소수를 넘긴 뒤 (A) 임계 완화 / (B) 탐색 확장을 사용자에게 묻는다.
  3. **개인/소규모 1인 브랜드 = PLUS (③ 교정)** — 초안은 "브랜드 = 감점"이었으나, 1인이 운영하는 소규모
     브랜드(예: 혼자 만드는 수제 네일팁 브랜드 페이지)는 **연락 가능한 사람**이므로 감점이 아니라 **가점**으로
     교정했다. 감점 대상은 봇·몰개성 대형브랜드·리셀러·MLM·스팸으로 한정한다. ([H3] · [[human-vs-solo-brand-vs-bot]])
  4. **근거 없으면 리드 없음** — 모든 리드는 링크+인용(양 축) 근거를 갖는다. 없으면 셀을 비우고 이유를
     남기되 **날조하지 않는다**. ([H1]/[H8] · S1/S2)
  5. **6축 투명 스코어링** — 정체성·의도·실존인물신뢰·연락가능성·최신성·필터적합의 6축으로 분해하고
     **블랙박스 총점 금지**. ([H8] · [[fit-scoring-rubric]])
  6. **느리고 read-only, 자동발송 금지** — 밴은 채널의 영구 상실이다. 요청 간격은 보수적으로, 자동 DM/이메일
     0, 비밀번호 저장 0. ([H14] · [[slow-readonly-default]])
  7. **엔진 없는 지식 그래프** — bundle-standard §2.5에 따라 지식을 `[[위키링크]]` 노드 + INDEX로만
     적재(런타임 0). 세션 시작 시 INDEX만 읽고 필요한 노드만 연다. (14노드)
- **영어 문서 / 사용자 언어 산출물 피벗**: 번들을 누구나 내려받아 쓰도록 **문서는 영어**로 통일하되,
  **런타임 상호작용(인터뷰·응답)과 산출물(리포트 산문·CSV 값)은 사용자 언어를 미러링**하도록 재구성했다.
  CSV **컬럼 키만** 안정적인 영어 스키마로 고정하고, 값·서술은 사용자 언어를 따른다. 발견 콘텐츠(게시글·바이오·
  키워드)는 원어 그대로 보존하고 감지 언어 라벨은 정직하게 보고한다([H7]).
- **비즈니스 리포트 포맷**: 인사이트 리포트를 느슨한 노트에서 **7섹션 정식 워크 리포트**로 승격했다 —
  ① Executive Summary ② Objective & Scope ③ Method ④ Results at a Glance(채널 상태·언어·의도 분포
  표) ⑤ Key Findings(세그먼트 인사이트·최고점 리드 근거) ⑥ Recommendations & Next Steps(N vs 목표 M
  → 완화/확장) ⑦ Appendix(0-results vs discovery-failed, provenance, 컴플라이언스). 섹션 헤딩은 안정적
  영어 앵커, 내부 산문은 사용자 언어. `output-assembly.md`와 예시 리포트에 반영했다.
- **training-camp 지적 반영(이번 패치 패스)**:
  - **신뢰도 등급 모순 교정** — `[C] practitioner-source → confidence: medium` 규칙을 위반하던
    `two-axis-icp` / `demand-false-positive` / `fit-scoring-rubric` 노드를 `high` → `medium`으로
    낮추고 각 본문에 한 줄 헤지를 추가했다(intent-signal-strength의 헤지 스타일에 맞춤).
  - **시뮬레이션은 워커의 폴백이 아니다** — 디스커버리 도구가 없거나 미연결이면 해당 채널을
    `discovery-failed`로 보고하고 설치/인증을 안내하되 **리드를 날조·시뮬레이트하지 않는다**. 시뮬레이션은
    사용자가 명시적으로 요청한 테스트/데모 모드일 때만 허용. agent.md·dedup-gate.md·limitations.md에 명문화.
  - **S2 경험적 vs 논리적** — S2(근거 무결성)는 **라이브 조회 후에만** 참으로 주장 가능하며, 미검증/
    시뮬레이션 데이터에 S2 통과를 주장하지 않고 `unverified`로 표기하도록 성공기준을 명료화했다.
  - **fit 점수 척도 명시** — 6축 각 **1-5점, 총점 6-30(max 30)**임을 `fit-scoring-rubric`과
    `qualification-scoring`에 명시(샘플 `id:4 intent:5 human:4 contact:3 recency:4 filter:5`와 정합).
  - **태그 오타 교정** — agent.md S2의 `[H1·[H8]]` → `[H1·H8]`.

## Pipeline Position

기획·마케팅 파이프라인의 **상류(타깃 발굴)**를 담당한다. 대상 정의를 받아 근거 붙은 리드 리스트와 세그먼트
인사이트를 공급하고, **아웃리치 카피 작성·발송은 하류(growth-marketer / web-copy-analyzer)로 넘긴다.**
CRM 입력·딜리버러빌리티·유료 리스트 구매는 범위 밖이다.

## Next Improvements (차기 과제)

- 채널별 밴-리스크·스루풋 수치를 실측 로그로 보정(현재는 보수적 기본값).
- Threads/TikTok fallback 채널의 1급 승격(현재 best-effort).
- 반복되는 role 오분류 패턴을 `RUNS.md`에서 learned 노드로 승격하는 정리 루틴.
- 6축 가중치 프리셋(이메일 캠페인용 contactability 상향 등)을 icp.yaml 템플릿으로 제공.
- SQLite 백엔드 마이그레이션 헬퍼 스크립트(현재는 수동 3단계 안내).
