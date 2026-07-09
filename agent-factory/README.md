# 에이전트 공장 (Agent Factory)

내부 팀 도구다. AI력 사무소가 찍어내는 모든 AI 워커 번들이 **하나의 통일된
형식**으로 나오도록 하는 하네스이며, 팀원이 새 에이전트를 만들 때 매번
처음부터 구조를 고민하지 않도록 뼈대·표준·검증 게이트를 미리 준비해 둔다.

- **내부 전용**이다 — 웹사이트 워커 목록(`site/data.js`, `site/index.html`)에
  올라가지 않고, `seed-bundles/`처럼 zip으로 릴리스되지도 않는다. 팀원이
  로컬에서 새 번들을 만들 때 참고·복제하는 작업대일 뿐이다.
- 실제 공개 산출물은 이 공장을 거쳐 `seed-bundles/<slug>/`에 착지한 폴더
  번들이다.

## 왜 이게 산출물 형식을 통일하나

팀원마다 다른 언어·구조·문서 관습으로 번들을 만들면, 사용자는 매번 새로
읽는 법을 배워야 하고 우리는 매번 새로 검증 기준을 세워야 한다. 이 공장은
"정본 표준 문서(`bundle-standard.md`, `knowledge-arch.md`) + 레퍼런스
구현(`seed-bundles/web-copy-analyzer/`) + 채울 자리만 남긴 스켈레톤
(`template/`) + 통과선(`verification.md`)"을 한 세트로 묶어, 누가 만들든
같은 모양(폴더 구조, 지식 그래프 2-뿌리, 자기학습 강령, CLI/MCP 이중 표면,
배포 게이트)이 나오게 강제한다. 형식이 통일되면 사용자 경험도, 우리의
리뷰 비용도 매번 재설계할 필요가 없어진다.

## 새 에이전트 만들기 (퀵스타트)

1. **정본 문서를 먼저 읽는다** — [`bundle-standard.md`](./bundle-standard.md)
   (출력 형식의 단일 출처)와 [`knowledge-arch.md`](./knowledge-arch.md)
   (지식 계층·자기학습 설계)를 숙지한다. 이 두 문서와 어긋나는 결정은 하지
   않는다.
2. **파이프라인을 따라간다** — [`PIPELINE.md`](./PIPELINE.md)의 5단계
   (research → design → implement → verify → publish)를 순서대로 밟는다.
   각 단계에는 통과해야 할 게이트와 담당 에이전트/모델이 명시돼 있다.
3. **스켈레톤을 복제한다** — `template/`을 `seed-bundles/<slug>/`로 복사해
   시작한다. `template/BUILD.md`가 지식 그래프 엔진·성장 레이어·빌드
   스크립트를 어디서 가져와 어떻게 리네이밍할지 안내한다(엔진 코드는 이
   폴더에 중복 보관하지 않는다 — `reference/`를 본다).
4. **원칙을 지킨다** — [`PRINCIPLES.md`](./PRINCIPLES.md)(운영비 0원, 코어
   공유, 폴더-번들 모델 불문, 게이트 자기승인 금지 등)를 구현 내내 기준으로
   삼는다.
5. **검증 게이트를 통과한다** — [`verification.md`](./verification.md)의
   체크리스트를 작성자 본인이 아닌 별도 리뷰 컨텍스트에서 통과시킨다.
6. **레퍼런스로 확인한다** — 막히면 [`reference/README.md`](./reference/README.md)
   가 가리키는 `seed-bundles/web-copy-analyzer/`의 실제 코드를 본다.
7. 완성된 번들은 `seed-bundles/<slug>/`에 착지시키고, 배포는 기존
   `scripts/build-release.py` + GitHub Release 경로를 그대로 쓴다.

## 문서 지도

| 문서 | 역할 |
| --- | --- |
| [`bundle-standard.md`](./bundle-standard.md) | v0.2 폴더-번들 출력 형식의 단일 출처 |
| [`knowledge-arch.md`](./knowledge-arch.md) | 4층 컷 · 2-뿌리 지식 그래프 · 자기학습 설계 |
| [`PIPELINE.md`](./PIPELINE.md) | research→design→implement→verify→publish 5단계, 단계별 게이트/담당 |
| [`PRINCIPLES.md`](./PRINCIPLES.md) | 사무소 포지셔닝·타깃·비협상 규칙 + 공장이 강제하는 원칙 |
| [`verification.md`](./verification.md) | 배포 전 통과해야 하는 검증 게이트 (안전·품질 결합) |
| [`template/`](./template/) | 새 번들을 시작할 린 스켈레톤 (엔진 코드 미포함) |
| [`reference/README.md`](./reference/README.md) | 레퍼런스 구현(web-copy-analyzer) 코드 지도 |

## 이 공장이 아닌 것

- 웹사이트에 노출되는 워커가 아니다 — `site/`는 건드리지 않는다.
- 다운로드 가능한 번들이 아니다 — zip으로 릴리스되지 않는다.
- 새 표준이 아니다 — `agent-factory/bundle-standard.md`가 유일한 정본이며,
  `docs/bundle-standard.md`(v0.1)는 이미 여기로 흡수됐다.
