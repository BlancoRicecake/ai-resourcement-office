# Skill: 전체 페이지 진단·리라이트 루프

카피라이팅 분석가가 URL/HTML 하나를 받아 진단부터 리라이트까지 끝내는 절차.
`worker/agent.md` ③ 작업 흐름의 실행 체크리스트 버전이다 — 판단 근거·휴리스틱
라벨은 agent.md를 따르고, 이 파일은 툴 호출 순서만 다룬다.

> 진단·리라이트에서 배운 일반화 가능한 절차·패턴은 `memory/COPY-PATTERNS.md`
> (인박스)에 후보로 제안하고, 반복 확인되면 `memory/knowledge/` 노드로 승격한다
> (agent.md ⑤). 이 seed 절차 파일 자체는 손대지 않는다.

## 절차

1. **페르소나 확보** — `memory/PERSONAS.md`에서 대상 페르소나를 고른다. 맞는
   페르소나가 없으면 `persona-interview.md` 절차로 먼저 정의해 `PERSONAS.md 추가
   후보`로 제안한다. 이후 도구 호출 시 이 페르소나를 `persona` 인자로 명시
   전달한다. 페르소나 없이 다음 단계로 진행하지 않는다.
2. **페이지 수집** — `fetch_page`로 URL을 가져온다. `error_kind`가 `ok`가
   아니면(404/timeout/blocked/non_html/too_large 등) 사유를 사용자에게
   설명하고 HTML 붙여넣기 폴백을 안내한다.
3. **파싱** — `parse_sections`. `parse_quality`가 `sparse`/`empty`면 SPA
   렌더링 부족 가능성을 알리고 렌더된 HTML 붙여넣기를 권한다.
4. **결정론 스코어카드** — `readability_scorecard`. 언어가 `ko`처럼 비영어면
   `english_dependent_metrics_applicable`을 확인해 가독성·we/you·전문용어
   지표를 참고용으로만 취급한다.
5. **첫 5초 진단** — `diagnose_section(scope="above_fold")`. 반환 payload로
   "무엇을/누구를/다음 행동" 회상 여부를 above-the-fold 요소만으로 판정한다.
6. **섹션별 진단** — 나머지 섹션마다 `diagnose_section(scope="section")`.
   각 미스를 명확성/신뢰/관련성/CTA 중 하나로 귀속하고 휴리스틱 라벨([H1]~
   [H12])을 붙인다. above-the-fold 우선순위를 유지한다.
7. **리라이트** — 미스로 표시된 섹션만 `rewrite_section`. 반환된
   `preservation_constraints`(후기·증거·수치)를 지키고, 변경마다 근거 원칙을
   명시한다. 후기·증언 섹션 자체는 리라이트 대상에서 제외한다.
8. **비교·검증** — `compare_report`로 before/after 조립. `preservation.ok`가
   `false`면 무엇이 빠졌는지 사용자에게 보여주고 6~7단계로 1회 자동 복귀한다.
9. **자가 점검** — agent.md ③-8의 루브릭 R1~R7을 점검한다. 하나라도
   "아니오"면 5~6단계로 복귀한다.
10. **성장 트리거(메모리 업데이트 후보)** — 사용자의 선호/교정 표현이나
    리라이트 채택/거부가 있으면 `메모리 업데이트 후보`로 제안한다(USER/DECISIONS/
    COPY-PATTERNS 중 해당 파일). 무엇을 후보로 제안하는지 항상 표시한다(자동 확정 금지).
11. **재검사** — 수정된 페이지가 재제출되면 2~9단계를 반복한다.
