# worker/skills/ — 절차 시드 작성 가이드

여기에 이 워커가 반복 수행하는 **작업 절차(procedure)**를 마크다운으로
정의한다. 지식 그래프(`worker/knowledge/`)가 "무엇을 판단 기준으로 삼는가"
라면, skills는 "어떤 순서로 작업하는가"다(`knowledge-arch.md`의 L4 절차
계층).

## 무엇을 여기 쓰나

- `agent.md` ③ 워크플로에서 별도 절차로 뽑아낼 만큼 구체적인 흐름(예:
  "타깃 페르소나 인터뷰", "전체 진단 루프") — 레퍼런스:
  `seed-bundles/web-copy-analyzer/worker/skills/persona-interview.md`,
  `full-page-diagnosis.md`.
- 각 스킬 파일은 절차의 단계, 각 단계에서의 실패/이상 케이스 대응, 지켜야
  할 주의사항(예: PII 감지 시 중단)을 담는다.

## 무엇은 여기 쓰지 않나

- **런타임에 학습된 절차**는 여기 쓰지 않는다. 사용자가 반복 요청하는
  워크플로를 채택하면 `save_workflow` 툴로 성장 레이어(`~/.<slug>/`)에
  기록한다 — 이 폴더(seed)는 번들 업데이트 시 통째로 교체되므로 학습분을
  여기 쓰면 소실된다.

`.gitkeep`은 이 폴더가 빈 상태로도 git에 잡히게 하는 자리 표시자이며, 실제
스킬을 채우면 지워도 된다.
