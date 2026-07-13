---
id: breadcrumbs-pattern
title: 브레드크럼 패턴
tags:
  - navigation
  - ia
  - wayfinding
source: seed
confidence: high
created: 2026-07-13
---
브레드크럼은 "홈 > 카테고리 > 현재" 형태로 **현재 위치와 상위 경로**를 보여 주는 보조 내비게이션이다. 깊은 구조에서 길 잃음을 줄인다.

리뷰 관점:

- **깊은 계층·대형 사이트**(커머스·문서·디렉토리)에서 특히 효과적이다 — 현재 위치 인지와 상위로의 한 번에 이동을 돕는다. [[navigation-depth-rules]]
- 얕은 사이트(1~2단계)에는 불필요하다 — 없다고 미스가 아니다. 구조 깊이에 비추어 판단한다.
- 브레드크럼은 **주 내비게이션의 대체가 아니라 보조**다. 이걸로 전체 내비를 대신하려 하면 미스.
- 각 단계가 실제 클릭 가능한 링크인가, 현재 페이지만 비활성인가.
- 라벨은 IA의 사용자 언어를 따른다. [[information-architecture-basics]]

정적 화면에서 링크 동작을 확인 못 하면 "브레드크럼 링크 동작 검증 필요"로 표기한다.

출처: NN/g, "Breadcrumbs: 11 Design Guidelines" — https://www.nngroup.com/articles/breadcrumbs/
