---
id: navigation-depth-rules
title: 내비게이션 깊이 규칙
tags:
  - navigation
  - ia
  - mobile
source: seed
confidence: high
created: 2026-07-13
---
얕은 구조(넓고 얕음)와 깊은 구조(좁고 깊음)는 트레이드오프다. **얕을수록 클릭은 적지만 한 층의 선택지가 많고, 깊을수록 선택은 단순하지만 길을 잃기 쉽다.**

리뷰 관점:

- 모바일은 얕은 구조가 유리하다(스크롤·탭이 클릭보다 싸다). 데스크톱 대형 사이트는 메가메뉴로 깊이를 평평하게 편다.
- 깊은 구조에는 **브레드크럼**으로 "현재 위치"를 보강한다. [[breadcrumbs-pattern]]
- 한 층의 항목이 과다하면 Hick 부담이 커진다 — 그룹핑으로 청크화한다.
- 사용자가 3클릭 안에 목표에 닿는지보다 "매 단계 선택이 명확한지"가 중요하다(3클릭 규칙은 절대 법칙이 아니다).
- 내비 구조는 IA의 표현이다 — 라벨·분류가 사용자 언어인지 먼저 본다. [[information-architecture-basics]]

깊이 자체가 문제가 아니라 "길 잃음"이 문제다 — 위치 표시와 되돌아갈 길을 본다.

출처: NN/g IA Study Guide — https://www.nngroup.com/articles/ia-study-guide/
