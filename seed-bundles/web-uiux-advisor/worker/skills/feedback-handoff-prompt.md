---
name: feedback-handoff-prompt
description: Use at the end of a review to convert findings into a copy-pasteable implementation prompt for any LLM or design tool. Covers the GOAL/CONTEXT/LAYOUT/TYPE/COLOR/COPY/CONSTRAINTS handoff frame, severity-ordered fix instructions, what-to-preserve, constraints, and done-criteria.
---

# 핸드오프 프롬프트 생성

리뷰가 끝나면 개선안을 **구현자(어떤 LLM·디자인 툴에든 복붙 가능한 지시 프롬프트)**로 변환해 리포트 말미에 붙인다. 자문가는 구현하지 않는다 — 이 프롬프트가 구현자에게 넘기는 인수인계 문서다.

## 프롬프트에 반드시 포함할 7요소

디자인-우선 스펙 구조(GOAL/CONTEXT/LAYOUT/TYPE/COLOR/COPY/CONSTRAINTS)를 핸드오프 프레임으로 각색한다.

1. **GOAL** — 이 수정으로 달성할 목표(핵심 전환·해결할 사용성 문제).
2. **CONTEXT** — 대상 화면/섹션, 서비스·타깃·플랫폼(인테이크 요약).
3. **수정 지시 (심각도순)** — Finding을 심각도 높은 순으로 나열하고, 각 항목에 **① 무엇을 어떻게 바꿀지 ② 근거 원칙 1줄**을 붙인다(예: "1차 CTA를 하나로 — Hick의 법칙: 경쟁 CTA 축소").
4. **LAYOUT/TYPE/COLOR** — 개선안의 구조·타이포·색 방향(텍스트 와이어프레임 참조). 대비 하한 등 수치 포함.
5. **보존할 것 (Do NOT change)** — 잘 되어 있어 **바꾸지 말 것**(예: 유지할 브랜드 로고 배치, 살아 있는 카피, 지켜진 접근성 요소). 구현자가 멀쩡한 것을 망가뜨리지 않게 명시한다.
6. **CONSTRAINTS** — 브랜드 톤(존댓말 등), 접근성 하한 수치(대비 4.5:1, 타깃 44/48), 기술 스택·바꿀 수 없는 요소.
7. **완료 판정 기준** — 수정 후 재검 포인트(예: "폴드 위 5초 안에 무엇을 파는지 회상되는가", "1차 CTA가 하나로 위계가 잡혔는가").

## 시각 패턴 구현 지목

시각 스타일·패턴 구현이 필요하면 프롬프트 안에 **패턴/스킬 이름을 직접 지목**한다(예: "다크 글래스 표면은 MengTo/Skills `glass-dark-ui` 참고, 단 대비 4.5:1 유지"). 자문가는 코드를 쓰지 않고 이름만 넘긴다.

## 형식 규칙

- 프롬프트는 **하나의 복붙 블록**으로 만든다(코드펜스로 감싸 그대로 붙여넣게).
- 사실이 아닌 수치를 지어내지 않는다 — "검증 필요" 항목은 프롬프트에도 "실측 후 확정" 표기를 남긴다.
- 프롬프트는 구현 지시이지 구현 결과가 아니다 — HTML/CSS를 작성해 넣지 않는다.

구조 참고: MengTo/Skills `design-first-ui-prompting` (MIT)의 스펙 구조(GOAL/FORMAT/LAYOUT/TYPE/COLOR/COPY/CONSTRAINTS)를 리뷰 결과 핸드오프 프레임으로 각색.
