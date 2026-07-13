# RESEARCH

지식 노드의 근거·참고문헌이다. **원문 본문은 저장하지 않는다** — 짧은 출처 표기와 등급만 남긴다. 노드 본문의 아이디어는 자기 언어로 재서술됐고, 여기 목록은 재확인·감사용이다.

출처 표기 형식: `저자/기관(연도). 제목. 출처. URL. [등급 A/B/C]`

## 참고문헌 (2026-07-13 훈련소 감사 기준)

### A급 — 원리 근거 (권위·표준)
- Nielsen Norman Group. 10 Usability Heuristics for User Interface Design. https://www.nngroup.com/articles/ten-usability-heuristics/ [A] → [[nielsen-10-heuristics]]
- Nielsen Norman Group. How to Conduct a Heuristic Evaluation. https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/ [A] → [[heuristic-evaluation-process]]
- Nielsen Norman Group. Severity Ratings for Usability Problems. https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/ [A] → [[severity-rating-scale]]
- Nielsen Norman Group. IA Study Guide. https://www.nngroup.com/articles/ia-study-guide/ [A] → [[information-architecture-basics]], [[navigation-depth-rules]]
- Nielsen Norman Group. Breadcrumbs: 11 Design Guidelines. https://www.nngroup.com/articles/breadcrumbs/ [A] → [[breadcrumbs-pattern]]
- Nielsen Norman Group. Search vs. Navigation. https://www.nngroup.com/articles/search-vs-navigation/ [A] → [[search-vs-browse]]
- Nielsen Norman Group. Empty State Interface Design. https://www.nngroup.com/articles/empty-state-interface-design/ [A] → [[empty-state-onboarding]]
- Nielsen Norman Group. Scrolling and Attention (조회 시간 폴드 집중). https://www.nngroup.com/articles/scrolling-and-attention/ [A] → [[above-the-fold-priority]]
- Nielsen Norman Group. Visual Hierarchy (UX 정의). https://www.nngroup.com/articles/visual-hierarchy-ux-definition/ [A] → [[visual-hierarchy]]
- Nielsen(2006) 최초 발견 · Pernice, K.(2017). F-Shaped Pattern of Reading on the Web: Misunderstood, But Still Relevant (Even on Mobile). NN/g. https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/ [A] → [[f-pattern-z-pattern]] (blurtest 블로그 C급 출처를 1차 NN/g로 교체, 2026-07-13)
- W3C. WCAG 2.2 — Contrast (Minimum) 1.4.3 / Non-text Contrast 1.4.11 / Target Size (Minimum) 2.5.8 / Focus Visible 2.4.7. https://www.w3.org/WAI/WCAG22/Understanding/ [A] → [[wcag-aa-checklist]], [[touch-target-size]]
- WebAIM. Contrast and Color Accessibility. https://webaim.org/articles/contrast/ [A-] → [[wcag-aa-checklist]]
- WebAIM. Usable and Accessible Form Validation. https://webaim.org/techniques/formvalidation/ [A-] → [[form-ux-best-practices]]

### A(원리)/B(편집) — 심리 법칙 편집물
- Yablonski, J. Laws of UX. https://lawsofux.com/ [A(원리)/B(편집)] → [[laws-of-ux-overview]], [[fitts-law]], [[hicks-law]], [[jakobs-law]], [[peak-end-rule]], [[doherty-threshold]], [[aesthetic-usability-effect]]
  - 하위 법칙(Fitts·Hick·Doherty 등)의 원 실험 근거는 A급이며, 사이트 자체는 2차 편집물 B급.

### A- — 공식 디자인 시스템 (1차 출처)
- Google. Material Design 3. / Apple. Human Interface Guidelines. / Shopify Polaris. / IBM Carbon. / Atlassian Design System. [A-] → [[design-systems-authority]]
- Meta Platforms. Astryx — 오픈소스 디자인 시스템(React + StyleX, 접근성 내장 컴포넌트 160+, 다크모드, 에이전트 친화). © Meta Platforms. https://astryx.atmeta.com/ (github: facebook/astryx) [A-] → [[design-systems-authority]] (2026-07-13 추가, 메인 세션 신뢰도 검증 완료)

### B — 실무 매체·공공 표준
- Smashing Magazine. The Thumb Zone: Designing for Mobile Users. https://www.smashingmagazine.com/2016/09/the-thumb-zone-designing-for-mobile-users/ [B] → [[thumb-zone-mobile]]
- Smashing Magazine. Improving IA With Card Sorting. https://www.smashingmagazine.com/2014/10/improving-information-architecture-card-sorting-beginners-guide/ [B] → [[information-architecture-basics]]
- KRDS (전자정부 UI/UX 가이드). https://uiux.egovframe.go.kr/guide/service/service_02_05.html [B, 한국·공공 한정] → [[korean-market-ux-patterns]]
- NN/g. Progress Indicators (로딩 피드백 일반). https://www.nngroup.com/articles/progress-indicators/ [B, 스켈레톤 특정 근거 아님] → [[loading-skeleton-states]]

### 라이선스 표기 (아이디어 각색 · 원문 복제 없음)
- MengTo/Skills — Copyright (c) Meng To, MIT License. https://github.com/MengTo/Skills
  - 파생 노드: [[glass-dark-ui-pattern]], [[visual-style-vocabulary]], [[landing-page-review-checklist]] (패러프레이즈·역변환).
  - 어댑트 스킬: `worker/skills/ui-review-intake.md`, `landing-page-review.md`, `evidence-based-audit.md`, `feedback-handoff-prompt.md`.
  - MIT 준수: 코드/원문 재배포 없음(아이디어만 재서술). 각 파일 하단·README·skills/README에 출처 표기.

## 검증 후보 (아직 실무 지침으로 확정하지 않음 · 교차 확인 필요)
- Toss(토스) 기술블로그의 UX 4원칙(3초 규칙·단순함·최소 기능·임팩트 집중). https://toss.tech/article/insurance-claim-process [C, 단일 출처·기업 방법론] → [[korean-market-ux-patterns]]에서 "공개 자료 기준 신중 인용"으로만 사용. **인용된 4원칙을 직접 뒷받침하는 정확한 출처 URL로 교체 대기**(현재 링크는 보험청구 아티클로 4원칙 근거와 불일치 소지).
- 엄지존 정확도 수치(이지존 하단 25~40%·96%, 하드존 61%): Smashing 아티클이 직접 뒷받침하지 않음. Hoober 계열 연구 출처 확인 전까지 "검증 필요"로 다룸 → [[thumb-zone-mobile]].
- "스켈레톤 스크린이 스피너보다 체감 대기를 줄인다": 연구 결과 혼재. 맥락 의존이며 정설로 단정하지 않음 → [[loading-skeleton-states]].
- 타이포 모듈러 스케일 1.125~1.5 비율대: 널리 쓰이는 관행이나 규범값 아님(무출처) → [[visual-hierarchy]]에서 "관행 기준"으로 표기.

## 폐기된 출처
- blurtest 블로그(F/Z 패턴): C급 단일 블로그. 노드 본문의 "NN/g 후속 재해석" 주장과 출처 불일치 → 1차 NN/g(Pernice 2017)로 교체함(2026-07-13).
