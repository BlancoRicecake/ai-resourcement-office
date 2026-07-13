# 지식 노드 INDEX

이 파일은 지식 노드의 목록(엔진 없는 그래프의 색인)이다. 사용 규칙:

- 세션 시작 시 이 **INDEX만** 읽는다. 노드 본문 전체를 미리 로드하지 않는다.
- 이번 리뷰·자문과 관련된 노드만 골라 열고, 본문의 `[[위키링크]]`를 따라 이웃 노드로 확장한다.
- 노드를 추가·삭제하면 INDEX도 같이 갱신한다 — 단, `메모리 업데이트 후보`로 제안하고 자동 확정하지 않는다(노드와 INDEX 동반 갱신).
- 새 지식은 `memory/REVIEWS.md`(인박스)에 먼저 쌓고, 일반화 가능한 교훈이 확인되면 노드로 승격한 뒤 아래 "learned 노드"에 같은 형식으로 한 줄 추가한다.

## seed 노드 (번들 동봉 · 검증됨)

> 2026-07-13 훈련소 초안 감사 반영: 노드 수 31 불변. 참고문헌·근거는 `memory/RESEARCH.md`에 일원화. frontmatter `created` 일괄 추가, `confidence`는 근거 강도별 차등(대부분 high, 아래 5개는 medium: [[f-pattern-z-pattern]]·[[thumb-zone-mobile]]·[[loading-skeleton-states]]·[[korean-market-ux-patterns]]·[[visual-style-vocabulary]]).

- [[nielsen-10-heuristics]] Nielsen 10대 사용성 휴리스틱 — 태그: heuristics, evaluation, foundation
- [[laws-of-ux-overview]] Laws of UX 개요 — 태그: laws, foundation, heuristics
- [[fitts-law]] Fitts의 법칙 (타깃 크기·거리) — 태그: laws, cta, interaction
- [[hicks-law]] Hick의 법칙 (선택지와 결정 시간) — 태그: laws, navigation, cta
- [[jakobs-law]] Jakob의 법칙 (익숙한 패턴) — 태그: laws, convention, learnability
- [[peak-end-rule]] Peak-End 규칙 (결정적 순간) — 태그: laws, onboarding, emotion
- [[doherty-threshold]] Doherty 임계 (400ms) — 태그: laws, performance, feedback
- [[visual-hierarchy]] 시각적 위계 — 태그: hierarchy, layout, clarity
- [[f-pattern-z-pattern]] F패턴·Z패턴 (스캔 동선) — 태그: scanning, layout, readability
- [[wcag-aa-checklist]] WCAG 2.2 AA 접근성 하한 — 태그: accessibility, contrast, wcag
- [[information-architecture-basics]] 정보구조(IA) 기초 — 태그: ia, navigation, structure
- [[navigation-depth-rules]] 내비게이션 깊이 규칙 — 태그: navigation, ia, mobile
- [[form-ux-best-practices]] 폼 UX 모범 사례 — 태그: form, validation, interaction
- [[empty-state-onboarding]] 빈 상태·온보딩 — 태그: empty-state, onboarding, first-run
- [[loading-skeleton-states]] 로딩·스켈레톤 상태 — 태그: loading, performance, feedback
- [[thumb-zone-mobile]] 엄지존 (모바일) — 태그: mobile, touch, reachability
- [[touch-target-size]] 터치 타깃 크기 — 태그: mobile, touch, accessibility
- [[heuristic-evaluation-process]] 휴리스틱 평가 절차 — 태그: evaluation, process, report
- [[severity-rating-scale]] 심각도 척도 (0~4) — 태그: severity, prioritization, report
- [[reference-galleries]] 레퍼런스 갤러리 — 태그: reference, inspiration, benchmark
- [[design-systems-authority]] 디자인 시스템 권위 — 태그: design-system, standards, reference
- [[korean-market-ux-patterns]] 한국 시장 UX 관습 — 태그: korea, convention, localization
- [[ux-role-boundaries]] UX 직무 경계와 자문가의 위치 — 태그: role, scope, positioning
- [[glass-dark-ui-pattern]] 다크 글래스모피즘 패턴 체크리스트 — 태그: visual-style, dark-mode, accessibility (출처: MengTo/Skills, MIT)
- [[visual-style-vocabulary]] 시각 스타일 어휘집 — 태그: visual-style, vocabulary, reference (출처: MengTo/Skills, MIT)
- [[landing-page-review-checklist]] 랜딩페이지 리뷰 체크리스트 — 태그: landing-page, conversion, structure (출처: MengTo/Skills, MIT)
- [[microcopy-guidelines]] 마이크로카피 지침 — 태그: microcopy, ux-writing, clarity
- [[above-the-fold-priority]] 폴드 우선 원칙 — 태그: above-fold, hierarchy, conversion
- [[breadcrumbs-pattern]] 브레드크럼 패턴 — 태그: navigation, ia, wayfinding
- [[search-vs-browse]] 검색 대 탐색 — 태그: search, navigation, ia
- [[aesthetic-usability-effect]] 심미-사용성 효과 — 태그: aesthetics, perception, trust

## learned 노드 (런타임 학습분)

아직 없음. 런타임에 승격된 노드는 위 seed 노드와 같은 `- [[id]] 제목 — 태그: …` 형식으로 여기에 추가한다.
