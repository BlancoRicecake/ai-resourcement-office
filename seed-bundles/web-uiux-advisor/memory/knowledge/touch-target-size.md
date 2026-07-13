---
id: touch-target-size
title: 터치 타깃 크기
tags:
  - mobile
  - touch
  - accessibility
source: seed
confidence: high
created: 2026-07-13
---
누를 수 있는 요소는 손가락으로 안정적으로 맞출 만큼 커야 한다. 기준이 여럿이니 혼동하지 않는다.

- **WCAG 2.2 (2.5.8)**: 최소 **24×24 CSS px** — 이건 접근성 **하한선**이다. [[wcag-aa-checklist]]
- **Apple HIG**: **44×44 pt** 권장.
- **Material Design**: **48×48 dp** 권장.
- 인접 타깃 간 **간격 최소 ~12pt** — 크기만큼 간격도 오조작을 좌우한다.

리뷰 관점:

- 24px는 통과선일 뿐, 실제 설계는 44/48을 목표로 한다. 24~28px대 탭 타깃은 "하한은 넘지만 권장 미달"로 지적한다.
- 작은 아이콘 버튼(닫기 ×, 좋아요)일수록 위험하다 — 시각 크기가 작아도 터치 영역(hit area)을 패딩으로 키운다.
- 촘촘히 붙은 링크 목록·인접 버튼은 오조작 위험으로 표기한다.
- 하단 배치·엄지 도달성과 함께 판단한다. [[thumb-zone-mobile]]

실제 픽셀값을 못 얻으면 "타깃 24px 미만으로 보임 — 실측 검증 필요"로 표기한다.

출처: WCAG 2.5.8 Target Size; Apple HIG; Material Design 3 — https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
