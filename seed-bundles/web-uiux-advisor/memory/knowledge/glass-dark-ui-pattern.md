---
id: glass-dark-ui-pattern
title: 다크 글래스모피즘 패턴 체크리스트
tags:
  - visual-style
  - dark-mode
  - accessibility
source: seed
confidence: high
created: 2026-07-13
---
다크 모드 + 글래스모피즘(반투명·블러 표면) 스타일을 리뷰할 때의 판단 기준이다. 이 스타일은 시각적으로 매력적이지만 **대비·가독성**에서 실패하기 쉽다 — 심미가 사용성을 해치지 않는지 본다.

체크리스트(리뷰 관점으로 재구성):

- **블러 뒤 텍스트 대비** — 반투명 표면 위 텍스트가 배경 이미지와 겹쳐 대비가 무너지지 않는가. 표면에 충분한 불투명도·틴트를 줘 4.5:1을 확보한다. [[wcag-aa-checklist]]
- **경계 가시성** — 유리 표면의 경계(그라디언트 보더·미세 하이라이트)가 배경과 구분되는가. 비텍스트 대비 3:1.
- **다크 모드 색** — 순수 검정(#000)보다 살짝 밝은 표면색으로 눈부심·번짐을 줄인다. 채도 높은 색은 다크에서 진동(vibration)하니 낮춘다.
- **깊이 신호** — 그림자·블러로 레이어 위계를 만들되 과하면 노이즈가 된다. [[visual-style-vocabulary]]

리뷰 결론: 이 스타일 구현이 필요하면 구현은 넘긴다(예: MengTo/Skills `glass-dark-ui`). 자문가는 "대비 하한을 지키는가"만 판정한다.

출처: MengTo/Skills `glass-dark-ui` (MIT, Meng To)의 다크모드 체크리스트를 리뷰 판단 기준으로 패러프레이즈 — https://github.com/MengTo/Skills
