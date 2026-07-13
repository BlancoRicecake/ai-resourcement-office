---
id: heuristic-evaluation-process
title: 휴리스틱 평가 절차
tags:
  - evaluation
  - process
  - report
source: seed
confidence: high
created: 2026-07-13
---
리뷰는 감이 아니라 절차다. 같은 화면을 두 번 순회하고, 발견을 정해진 형식으로 기록한다. **[H1]**

절차:

1. **1차 순회 (전체 흐름)** — 사용자 관점으로 처음부터 끝까지 훑어 첫인상·주요 이탈 지점·전반적 위계를 잡는다.
2. **2차 순회 (휴리스틱별)** — [H1~H12] 휴리스틱을 하나씩 대며 세부를 점검한다([[nielsen-10-heuristics]] 포함).
3. **Finding 기록** — 미스마다 `위치 + 관찰 + 근거(위반 휴리스틱/법칙/기준) + 심각도(0~4) + 개선안`으로 적는다.
4. **심각도 산정** — 빈도·영향·지속성 3요소로 매긴다. [[severity-rating-scale]]
5. **우선순위화** — `심각도 × 수정난이도`로 정렬해 quick win을 앞세운다.

리포트 구조: Executive Summary(상위 3~5) → Findings → 우선순위 → 개선안(Before/After) → 레퍼런스 근거.

원칙: 근거 없는 지적은 Finding이 아니다. 확인 못 한 항목은 "검증 필요"로 표기한다.

출처: NN/g, "How to Conduct a Heuristic Evaluation" — https://www.nngroup.com/articles/how-to-conduct-a-heuristic-evaluation/
