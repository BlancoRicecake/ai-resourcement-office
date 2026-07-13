---
id: wcag-aa-checklist
title: WCAG 2.2 AA 접근성 하한
tags:
  - accessibility
  - contrast
  - wcag
source: seed
confidence: high
created: 2026-07-13
---
접근성은 "있으면 좋은 것"이 아니라 **하한선**이다. 아래는 웹 리뷰에서 가장 자주 걸리는 WCAG 2.2 AA 항목이다. **[H7]**

- **1.4.3 대비(최소)** — 본문 텍스트 **4.5:1**, 큰 텍스트(약 24px 이상 또는 굵은 18.66px) **3:1**. 가장 흔한 실패 항목이다. 연회색 본문·저대비 플레이스홀더를 특히 본다.
- **1.4.11 비텍스트 대비** — UI 컴포넌트(버튼 경계·아이콘·입력 필드 테두리) **3:1**.
- **2.5.8 타깃 크기(신규)** — 최소 **24×24 CSS px**. 관행 권장은 더 크다(iOS 44pt, Material 48dp). [[touch-target-size]]
- **2.4.7 포커스 가시성(AA 기준선)** — 키보드 포커스 표시가 **보여야** 한다(Focus Visible). ※ 포커스 표시의 대비 **3:1**·최소 둘레 커버리지까지 요구하는 강화 기준은 **2.4.13 Focus Appearance로 AAA**이며 AA 하한이 아니라 상향 목표다. (혼동 주의: 2.4.11은 *Focus Not Obscured*로 별개 항목.)

리뷰 관점:

- 실제 색값·대비비를 얻을 수 없으면 단정하지 말고 "대비 부족으로 보임 — 실측 검증 필요(목표 4.5:1)"로 표기한다.
- 색만으로 정보를 전달하지 않는가(색맹 고려), 이미지 대체텍스트·폼 레이블이 있는가도 함께 본다.
- 접근성 위반은 심각도가 높다 — 일부 사용자에게 **진행 불가(4)**가 될 수 있다. 절차는 [[heuristic-evaluation-process]].

출처: WCAG 2.2 체크리스트 — https://getwcag.com/en/blog/wcag-2-2-checklist , WebAIM Contrast — https://webaim.org/articles/contrast/
