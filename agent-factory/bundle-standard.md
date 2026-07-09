# AI력 Bundle v0.2 Standard (폴더-번들)

> v0.1(`docs/bundle-standard.md`)을 흡수·승격한 문서다. v0.1은 "미니 SaaS + 워커"를
> 전제한 Python 앱 중심이었다. v0.2는 **폴더-번들이 정본**이며 특정 언어·모델에
> 종속되지 않는다. 목표는 하나다 — **어떤 코딩 에이전트(Claude/Codex/Manus…)가
> 폴더를 읽어도 동일하게 실행되는, 판단하는 전문가 에이전트**를 통일된 형식으로
> 찍어내는 것.

## 0. 정본과 레퍼런스

- 이 문서 = 형식의 단일 출처(single source of truth).
- 정본 구현 예시(reference implementation) = `seed-bundles/web-copy-analyzer/`.
  새 번들을 만들 때 구조·코드 패턴은 이 번들을 복제해서 시작한다
  (`agent-factory/template/`의 뼈대 + web-copy-analyzer의 실코드).

## 1. 필수 구조

```txt
<slug>/
  README.md                 한 줄 소개 + Quick Start(4가지 실행 모드) + 구성
  bundle.json               카탈로그 메타데이터 (§4)
  .env.example              코드가 실제로 읽는 env만 (없으면 "키 불필요" 명시)
  LICENSE

  app/                      결정론 도구의 소스 (언어 자유; TS 권장)
    core/                   순수·isomorphic 로직 (fs·network 없음) — 웹/CLI/MCP가 공유
    growth/                 성장 레이어 (자가학습 저장/병합/위생) — §3
    mcp/                    MCP 어댑터 (core를 감싸는 얇은 레이어)
    cli.ts                  CLI 어댑터 (동일 core 핸들러를 서브커맨드로 노출)
    scripts/                build(=dist 프리번들) / gen-agent / gen-graph
    dist/                   프리빌드 산출물 (gitignore, 릴리스 자산) — zero-install 실행용

  worker/                   에이전트의 "사람" 부분 (모델 불문 이식성)
    agent.md                단일 소스 페르소나 정의 (정체성·휴리스틱·워크플로·자가학습 강령)
    agent.json              기계 판독 메타 (역할·입출력·도구·한계)
    knowledge/              지식 그래프 seed 뿌리 (§2) — .md 노드 + graph.json
    skills/                 절차 시드 (재사용 작업 절차; 런타임 학습분은 성장 레이어로)
    harness/README.md       모델 불문 구동법 (4가지 실행 모드)
    mcp/README.md           MCP 클라이언트 등록 가이드

  plugin/                   Claude Code 어댑터 (선택) — agent.md로부터 생성
    .claude-plugin/plugin.json
    agents/<slug>.md        gen-agent가 agent.md에서 생성 (직접 수정 금지)

  examples/
    input/                  실제 샘플 입력
    output/                 실제 CLI 실행으로 얻은 산출물 (날조 금지) + 판단 리포트

  docs/
    build-log.md            어떻게 만들었나
    cost-guide.md           결정론 도구=$0, 판단 비용은 호스트 모델 토큰
    security-notes.md       SSRF/로컬처리/위생/스키마 등
    limitations.md          알려진 한계
```

언어 자유. 단, **두 표면(CLI·MCP)은 반드시 하나의 core를 공유**한다. core에 없는
로직이 어댑터에 새로 생기면 설계 위반이다. 자연어 에이전트로 쓰는 것은 이 도구
표면 위에 `agent.md` 하나를 얹는 것으로 해결하며 세 번째 표면을 만들지 않는다.

## 2. 지식 계층 (4층 컷) — 자세히는 `knowledge-arch.md`

- **L1 정체성 + 상위 휴리스틱** → `worker/agent.md` (항상 로드)
- **L2 계산 규칙** → `app/core` 코드 (결정론)
- **L3 지식 그래프** → **2-뿌리 병합**
  - seed: `worker/knowledge/*.md` (검증·읽기전용, 업데이트 시 교체)
  - learned: `~/.<slug>/knowledge/*.md` (런타임 자가학습, 업데이트 불변)
  - `search_knowledge`/`knowledge_neighbors`는 **병합본**을 조회 → 재시작 후 연속성
- **L4 절차** → `worker/skills/` (seed) + `save_workflow`(learned)

노드 = frontmatter(`id,title,tags,source,confidence`) + 본문 + `[[wikilink]]`(엣지).
빌드 시 seed로 `graph.json`을 생성하고, **dangling 링크·self-loop·중복 id·id↔파일명
불일치는 빌드/테스트 실패**로 막는다(검증 게이트).

## 3. 성장·자가학습 레이어 (필수)

업데이트가 건드리지 않는 사용자 홈(`~/.<slug>/`)에 축적한다. 최소 구성:

- **USER 대응** — 페르소나/선호/브랜드 보이스/금지표현 (`remember`, `save_persona`)
- **SKILLS 대응** — 채택된 재사용 절차 (`save_workflow`)
- **MEMORY/지식 대응** — 일반화 도메인 지식 (`learn_knowledge` → learned 뿌리)

규칙:
- **사용자 우선 병합** — 성장 레이어 값이 번들 기본값을 이긴다.
- **위생(hygiene)** — 고객 PII·미공개 매출/전환/트래픽 실측치는 저장 거부(우회 금지).
  `remember`와 `learn_knowledge` 양쪽에 동일 적용.
- **`agent.md`에 자가학습 행동 강령을 반드시 주입** — 조회 우선 / 학습 기록 시점 /
  `remember`(사용자 종속) vs `learn_knowledge`(범용 도메인) 구분 / learned는 번들
  `worker/knowledge/`에 쓰지 않고 성장 레이어에만. (강령이 없으면 도구만 있고
  성장이 안 일어난다.) 자세히는 `knowledge-arch.md §3`.
- **자율 스킬 생성·개선(B)** — 복잡한 작업을 성공적으로 마치면 사용자 요청 없이도
  `save_workflow`로 절차를 증류하고, 기존 스킬과 겹치면 개선·갱신한다.
- **정리·승인(C)** — 반복 확인 시 새 노드 대신 `confidence` 상향·중복 병합·모순
  플래그(consolidation), 민감/광범위한 learned 쓰기는 선택적 승인 스테이징
  (`confidence: pending`)으로 다음 세션 반영 전에 사용자 확인.
- **에피소드 아카이브(A)는 현재 보류** — Hermes의 SQLite FTS5 전체 이력 리콜은 미채택,
  `decisions.log` + `search_knowledge`로 대체(향후 선택 스펙).

## 4. bundle.json 필수 메타데이터

- slug, title, worker(직원 이름), category, difficulty, runtime
- requiredKeys — 결정론 도구가 키 불필요면 그렇게 명시("없음: 호스트 LLM이 판단")
- estimatedCost — 결정론 도구 $0 / 호스트 모델 토큰은 별도
- includes, requirements
- downloadUrl — GitHub 릴리스 자산 (`.../releases/latest/download/<slug>.zip`)
- disclaimer — 사용자가 본인 환경·모델·예산으로 실행

## 5. 난이도

- Beginner: 프리빌드 dist + 한 명령이면 충분.
- Intermediate: 소스 빌드/설정 또는 MCP 등록이 필요.
- Advanced: DB·배포·클라우드 설정이 필요.

## 6. 공개 체크리스트 (배포 게이트) — 자세히는 `verification.md`

- [ ] README·`.env.example`·LICENSE 존재, 실제 키/시크릿 미커밋
- [ ] 샘플 input **및 실제 실행으로 얻은** output 존재(날조 금지)
- [ ] cost-guide·security-notes·limitations 존재
- [ ] 원본 SaaS 브랜드·UI·카피 미복제, 로컬 실행 경로 명확
- [ ] **지식 그래프 검증**: seed `[[링크]]` 전부 해소, self-loop/중복 없음, `graph.json` 동기화
- [ ] **자가학습 강령**이 `agent.md`에 존재, 위생 필터가 PII/미공개매출 거부 확인
- [ ] `agent.md`에 번들에 없는 문서(design.md, 문제표 등) **dangling 참조 0**
- [ ] core-공유 원칙 준수(어댑터에 신규 로직 없음), 테스트 그린
- [ ] 작성/리뷰 분리 — 같은 컨텍스트 자기승인 금지, 독립 검증 게이트 통과

## 7. 비협상 규칙 (모든 공개 페이지·README에 명시)

AI력 사무소는 워커를 대신 실행하지 않는다. 사용자가 패키지를 내려받아 본인 환경과
예산으로 실행한다. 모든 API·모델·서버·서드파티 비용은 사용자가 부담한다.
