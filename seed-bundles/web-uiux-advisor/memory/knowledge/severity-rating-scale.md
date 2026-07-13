---
id: severity-rating-scale
title: 심각도 척도 (0~4)
tags:
  - severity
  - prioritization
  - report
source: seed
confidence: high
created: 2026-07-13
---
심각도는 감이 아니라 3요소로 계산한다: **빈도**(얼마나 많은 사용자·화면에서 발생하나), **영향**(발생 시 목표 달성을 얼마나 막나), **지속성**(한 번 학습되나 매번 반복되나).

| 척도 | 의미 | 예 |
| --- | --- | --- |
| 0 | 문제 아님(참고) | 취향 수준의 관찰 |
| 1 | 코스메틱 | 정렬이 1px 어긋남 |
| 2 | 경미(우회 가능) | 레이블 위치가 애매하나 채울 수 있음 |
| 3 | 심각(목표 방해, 우선 수정) | 폴드 아래 밀린 1차 CTA |
| 4 | 재앙적(진행 불가·접근성 차단) | 대비 미달로 일부 사용자가 읽지 못함 |

리뷰 관점:

- 우선순위는 심각도 단독이 아니라 **`심각도 × 수정난이도`**로 정한다 — 심각도 높고 수정 쉬운 것이 quick win.
- 접근성 차단은 일부 사용자에게 4가 될 수 있음을 기억한다.
- 심각도에 이견이 있으면 3요소로 근거를 대고 사용자와 합의한다(합의값은 `DECISIONS.md`에).
- 절차 전체는 [[heuristic-evaluation-process]]를 따른다.

출처: NN/g, "Severity Ratings for Usability Problems" — https://www.nngroup.com/articles/how-to-rate-the-severity-of-usability-problems/
