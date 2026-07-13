---
name: evidence-based-audit
description: Use when writing any finding in a review report. Covers the claim→evidence linking rule, flagging unverified items, plain-language explanation, and how to compute severity from frequency/impact/persistence.
---

# 근거 기반 감사 원칙

리뷰 리포트의 신뢰는 "모든 주장이 근거에 묶여 있는가"에서 나온다. 이 스킬은 Finding을 쓰는 3단계 규칙이다: **주장 → 증거 연결 → 평문 설명.**

## 1단계 — 주장을 증거에 묶는다

모든 Finding은 다음 4요소를 갖춘다. 하나라도 빠지면 Finding으로 인정하지 않는다.

1. **위치** — 어느 화면·섹션·요소인가(예: "폴드 위 히어로의 1차 CTA").
2. **관찰** — 무엇이 보이는가(사실 서술, 판단 아님).
3. **근거** — 위반한 휴리스틱/법칙/기준을 인용(예: "Fitts의 법칙 — 타깃이 작고 인접 간격 부족" / "WCAG 1.4.3 대비 하한").
4. **개선안** — 실행 가능한 대안(텍스트 와이어프레임·섹션 구조·패턴 이름).

근거 없는 지적("좀 촌스럽다")은 금지다. 근거 노드는 `memory/knowledge/`의 [[heuristic-evaluation-process]]·[[nielsen-10-heuristics]]·[[wcag-aa-checklist]] 등에서 가져온다.

## 2단계 — 검증 못 한 항목은 별도 표기

내가 직접 확인할 수 없는 것은 단정하지 않고 **"검증 필요"**로 표기한다.

- **대비비·색값** — 실제 hex를 못 얻으면 "대비 부족으로 보임 — 실측 검증 필요(목표 4.5:1)"로.
- **로딩 시간·인터랙션 동작** — 정적 스크린샷·묘사만으로는 확인 불가. "Doherty 임계 검증 필요"로.
- **수치·전환율** — 지어내지 않는다. 근거 없으면 창작 금지, 플래그만.

검증된 Finding과 "검증 필요" Finding을 리포트에서 시각적으로 구분한다.

## 3단계 — 평문으로 설명한다

- 전문용어를 쓰면 한 줄로 풀어 준다("Fitts의 법칙 — 버튼이 작고 멀수록 누르기 어렵다").
- "왜 이 사용자에게 이탈 요인인지"를 타깃 맥락으로 설명한다(범용 교과서 복붙 금지).
- 심미 지적은 취향이 아니라 신뢰·사용성 인식에 주는 영향으로 환원한다. [[aesthetic-usability-effect]]

## 심각도 산정 (0~4, 3요소)

심각도는 감이 아니라 3요소로 계산한다. [[severity-rating-scale]]

- **빈도** — 얼마나 많은 사용자·화면에서 발생하나?
- **영향** — 발생 시 목표 달성을 얼마나 막나?(막힘 vs 불편)
- **지속성** — 한 번 겪고 학습되나, 매번 반복되나?

| 척도 | 의미 |
| --- | --- |
| 0 | 문제 아님(참고) |
| 1 | 코스메틱(있으면 좋음) |
| 2 | 경미(불편하나 우회 가능) |
| 3 | 심각(목표 달성 방해, 우선 수정) |
| 4 | 재앙적(진행 불가·접근성 차단) |

우선순위는 `심각도 × 수정난이도`로 정렬한다 — 심각도 높고 수정 쉬운 것이 quick win이다.

구조 참고: MengTo/Skills `audit-verify-explain-grade-5` (MIT)의 감사→증거검증→쉬운설명 3단계를 리뷰 리포트 원칙으로 각색.
