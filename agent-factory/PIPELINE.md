# 제작 파이프라인 (5단계)

`docs/strategy.md`의 **Operating Loop**와 **Operating Pipeline v0.2**를
그대로 흡수해 다섯 개의 실행 단계로 정식화한 것이다. 각 사이클의 산출물은
"서비스 하나 + 그 서비스를 만들며 탄생한 에이전트 번들"이며, 번들은
`seed-bundles/<slug>/`에 착지해 AI력 사무소 웹 디렉토리와 GitHub 릴리스에
오른다.

```
research → design → implement → verify → publish → (1로 돌아가 반복)
```

각 단계는 **목적 · 입력 · 게이트(무엇이 참이어야 다음으로 가는가) · 담당(에이전트/모델)**
으로 정의한다.

## 조직 역할 그림 (v0.3)

이 5단계 뒤에는 실제로 번들을 만들고 유지하는 팀 내부의 역할 분담이 있다.
직무 분석가와 에이전트 메이커가 새 직원을 설계·제작하면, 에이전트 훈련소가
`memory/`를 지식으로 채워 콜드스타트를 없애고, 에이전트 기술 전문가가
파이프라인 전체에 최신 제작 기술을 공급한다.

```
직무 분석가 → 에이전트 메이커 → 에이전트 훈련소(memory 적재·졸업시험) → 실전 투입
  (design)      (implement)              ↑ (design~verify 사이)
                                          |
                              에이전트 기술 전문가 (전 단계 지원: 기술 자문 + 보수 교육 제안서)
```

- **직무 분석가**: research/design 단계에서 도메인 휴리스틱과 문제 상황을
  분석한다(§1의 `architect`/`analyst` 역할과 겹친다).
- **에이전트 메이커**: implement 단계에서 `template/`을 채워 "빈 직원"을
  만든다(§2의 `executor` 역할).
- **에이전트 훈련소**(`seed-bundles/agent-training-camp/`): 새로 만들어진
  에이전트가 실전 투입되기 전, 3단계 합법 지식 파이프라인(흡수→실무적
  합성→적재)으로 `memory/`(특히 `<JOB>.md`, `DECISIONS.md`)를 미리 채우고,
  마지막에 직무 맞춤 졸업 시험으로 실전 투입 가능 여부를 판정한다. 그래프가
  아니라 **`memory/`를 채운다** — 코드형(그래프 강화) 번들이면 이 지식을
  seed 그래프 노드로도 승격할 수 있다(부록 A).
- **에이전트 기술 전문가**(`seed-bundles/agent-tech-specialist/`): 특정
  단계를 맡지 않고 파이프라인 전체를 지원한다 — 기술 동향을 추적해 팀
  번들이 전제하는 기술이 낡으면 `보수 교육 제안서`(diff 형태의 규칙 업데이트
  후보)를 만든다. 다른 번들 파일을 직접 고치지 않고 제안서로만 만든다.

## 0. 리서치 (매일, 상시)

- **목적**: 지금 인기를 얻는 SaaS/워크플로 하나를 골라 기능을 분해·분석한다.
- **입력**: SaaS Research Agent(바탕화면 `SaaS_Research_Agent` 폴더)의 매일
  아침 한국·미국 시장 SaaS 순위, 검색 키워드, SNS 바이럴 조사.
- **게이트**: 보고서가 "무엇을 배울 도메인인가"와 "왜 지금 인기 있는가"에
  근거(출처)와 함께 답한다. 근거 없는 수치는 "미확인"으로 표기한다.
- **담당**: document-specialist / research 성격 에이전트. 사람이 누적된
  보고서를 읽고 만들 서비스 하나를 선정한다(**사람 개입 지점 1**).

## 1. Design (설계)

- **목적**: 코드를 한 줄도 쓰기 전에 기능을 단위 동작까지 쪼개고, 정상
  플로우뿐 아니라 문제 상황(네트워크 실패, 키 없음, 입력 손상 등)까지
  UI/판단 대응을 표로 정리한다. 이 도메인에서 실제로 통용되는 전문가 판단
  기준(휴리스틱)을 리서치해 `worker/agent.md` 초안에 담는다.
- **입력**: 선정된 서비스 주제, `bundle-standard.md`, `knowledge-arch.md`.
- **게이트**: (a) 기능이 단위 동작 단위로 쪼개졌는가, (b) 문제 상황별
  대응이 빠짐없이 정의됐는가, (c) `agent.md` 초안에 도메인 휴리스틱과
  워크플로가 근거와 함께 있는가, (d) 지식 그래프에 넣을 seed 노드 후보와
  성장 레이어에 쌓을 기억 스키마가 정의됐는가. **작성자 본인이 이 게이트를
  자기승인하지 않는다** — 별도 리뷰 컨텍스트(architect/critic)가 통과·미달을
  판정한다.
- **담당**: `architect`(Opus) 주도, 필요 시 `oh-my-claudecode:analyst`로
  도메인 판단 기준을 보강. 검토는 `oh-my-claudecode:critic`(별도 컨텍스트).

## 2. Implement (구현)

- **목적**: design.md를 실제 문서·(선택)코드로 옮긴다. 기본은
  순수-마크마운 번들: `AGENTS.md` 진입점, `worker/agent.md`(직무 지침 +
  메모리 사용 원칙), `memory/{MEMORY,USER,PROJECT,DECISIONS,<JOB>}.md`,
  `worker/skills/`, `bundle.json`(+`version`), `docs/*`를 채운다.
  결정론 도구가 꼭 필요한 과제만 `app/core`를 만들고 CLI(`app/cli.ts`)/
  MCP(`app/mcp/`) 두 어댑터가 그 core를 공유하게 한다(선택 강화).
- **입력**: 통과된 design.md, `agent-factory/template/`(스켈레톤),
  순수-마크다운 레퍼런스는 `seed-bundles/youtube-content-writer/`, 코드형
  레퍼런스는 `seed-bundles/web-copy-analyzer/`. 신임 에이전트의 지식
  선적재가 필요하면 `seed-bundles/agent-training-camp/`(3단계 합법
  지식 파이프라인)로 `memory/`를 채운다.
- **게이트**: (a) `AGENTS.md`가 로드 순서·도구 스코프·범위 밖 규칙을
  갖췄는가, (b) `memory/` 표준 파일이 존재하고 `agent.md`에 학습 루프
  규칙(업데이트 후보 제안·자동확정 금지)이 있는가, (c) (그래프 강화 시만)
  지식 그래프 seed가 검증 게이트(dangling 링크 0, self-loop/중복 없음,
  `graph.json` 동기화)를 통과하는가, (d) (코드형만) core에 없는 로직이
  어댑터에 새로 생기지 않았는가, (e) 샘플 input과 **실제 실행으로 얻은**
  output이 있는가(날조 금지).
- **담당**: `executor`(복잡한 작업은 Opus 라우팅), 지식 선적재는
  `agent-training-camp` 패턴, 기술 스택 선택은 `agent-tech-specialist`
  자문. **파일 쓰기는 메인 스레드가 아니라 executor에게 위임해 비용을
  메인 컨텍스트 밖에 둔다.** executor를 순차로 여러 번 spawn할 때는 이전
  세션이 남긴 tsserver 프로세스가 누적되지 않도록 정리한 뒤 다음 spawn을
  시작한다.

## 3. Verify (검증)

- **목적**: 구현이 design.md의 플로우·문제 상황 표와 실제로 일치하는지,
  안전·품질 기준을 만족하는지 **작성자와 분리된 컨텍스트**에서 확인한다.
- **입력**: 구현된 번들, `verification.md`의 게이트 체크리스트.
- **게이트**: `verification.md`의 전체 체크리스트 통과. 특히 —
  no-fake-completion(TODO/`test.skip`/`.only`/스텁 테스트/미구현 분기는
  블로커), 예시는 실제 실행 결과여야 함, 지식 그래프 검증 게이트 통과,
  core-공유 원칙 준수, 테스트 그린.
- **담당**: 구현자와 분리된 독립 게이트 — `security-reviewer`(보안),
  `qa-tester`(실행 시나리오), `code-reviewer`(코드 품질), `verifier`(완료
  근거 검증). **같은 세션·같은 컨텍스트에서 스스로 통과를 선언하지 않는다.**
  실패 시 2단계(구현)로 돌아가 수정 후 재검증한다.

## 4. Publish (공개)

- **목적**: 검증을 통과한 번들을 실제로 내놓는다.
- **입력**: verify를 통과한 번들.
- **게이트**: `bundle.json`의 `version`을 semver로 올렸는가(신규 번들은
  `1.0.0`, 기존 번들의 다음 버전은 slug를 고정한 채 patch/minor/major 규칙을
  따름 — `bundle-standard.md` §5), `scripts/build-release.py`로 zip 빌드
  성공, GitHub Release 생성, `site/data.js` 카탈로그 등록. **npm
  publish/사이트 배포처럼 되돌리기 어려운 행위는 자동 실행하지 않고 사람이
  최종 승인한다**(**사람 개입 지점 2**).
- **담당**: 빌드는 executor/스크립트가 수행, 최종 배포 승인은 사람.

## 1로 돌아가 반복

공개가 끝나면 이번 사이클에서 드러난 공장 자체의 빈틈(모호했던 게이트,
반복된 실수, 누락된 체크리스트 항목)을 `PIPELINE.md`/`verification.md`에
반영하고 리서치 단계로 돌아간다. 회고 없이 반복하면 두 번째 번들부터도 같은
실수가 반복된다.

## 모델 라우팅 요약

| 단계 | 주 담당 | 모델 |
| --- | --- | --- |
| research | document-specialist/research agent | 상황에 맞게 (sonnet 기본) |
| design | architect | Opus |
| implement | executor | Sonnet, 복잡한 작업은 Opus |
| verify | security-reviewer / qa-tester / code-reviewer / verifier (author와 분리) | Sonnet, 보안/대규모는 Opus |
| publish | executor(빌드) + 사람(최종 승인) | — |
