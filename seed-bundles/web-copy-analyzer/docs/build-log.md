# Build Log

## Source Problem

랜딩페이지 카피를 사람에게 리뷰받으면 건당 $30~349, 패널 서비스는 연 $20K.
1인 창업자·인디해커·소규모 팀은 이 비용을 감당하기 어렵고, 타깃 구매자를
모르는 채 조언하는 기존 AI 툴은 "발 크기를 모르고 신발을 파는" 격이었다.

## MVP Scope

타깃 페르소나 기준으로 랜딩페이지를 진단하고(above-the-fold부터 명확성/신뢰/
관련성/CTA 귀속), 미스 섹션만 페르소나 어휘로 리라이트하되 후기·증언 원문은
보존하는 전환 카피 컨설턴트.

## 소스 → 폴더 번들 마이그레이션

- 원 서비스는 `ai-factory-harness/services/web-copy-analyzer/`에서
  design.md(architect+analyst 설계, critic 게이트 심사)를 거쳐 구현되었다.
- 이 번들은 그 구현을 `seed-bundles/web-copy-analyzer/`로 폴더 이전한 것이다:
  `app/`(코어+MCP+CLI+빌드 스크립트), `worker/`(agent.md·knowledge·harness·
  mcp 가이드), `plugin/`(Claude Code 플러그인).
- design.md 자체는 소스 저장소에만 있고 번들에는 포함되지 않으므로,
  `worker/agent.md`가 design.md의 문제 상황 표(§3)와 자가 점검 루브릭(§9)을
  인용하던 부분은 자기완결적으로 재작성했다 — 다운로드한 사용자가 참조할 수
  없는 외부 문서를 가리키지 않도록, 실패 케이스(404/타임아웃/SPA 빈약/
  페르소나 없음·손상/보존 실패/이름 충돌 등)는 문장 안에 조건을 직접 서술하고,
  루브릭 R1~R7은 agent.md ③ 8단계에 그대로 인라인했다.

## 지식 노드 (엔진 없는 그래프)

- `memory/knowledge/` — H1~H12 휴리스틱을 12개 마크다운 노드로 증류. 노드는
  frontmatter(`id`·`title`·`tags`·`source`·`confidence`) + 본문 + `[[위키링크]]`
  엣지로 구성되고, `INDEX.md`가 노드당 한 줄 색인을 담는다.
- 검색 엔진·자동 조회 코드는 없다(데이터만이 표준, `knowledge-arch.md` 결정).
  에이전트가 `INDEX.md`만 읽고 필요한 노드를 열어 `[[링크]]`를 따라간다 — 전부-로드
  비용을 런타임 0으로 "지금 필요한 양"에 비례하게 만든다.
- 런타임 학습분은 `memory/COPY-PATTERNS.md`(인박스)에 쌓였다가 일반화 가능한 교훈이
  확인되면 `source: learned` 노드로 승격된다(agent.md ⑤).

## 검증 (v2.0.0)

- `npm test` — 96개 테스트 그린 (core/mcp 계층: 파서·채점·prep 컨텍스트·persona·
  compare·fetch + MCP wire/validate/custom-tools/server). growth·knowledge-engine
  테스트는 해당 레이어 제거와 함께 삭제됨(v1의 155개에서 감소는 의도된 결과).
- `npm run build` — typecheck → esbuild 번들(cli.js/mcp.js) →
  `plugin/agents/web-copy-analyzer.md` 생성(6개 MCP 툴 네임스페이스 확인).
- CLI 스모크: `node app/dist/cli.js parse-sections`/`readability-scorecard`/
  `diagnose-section`(명시적 persona 입력)을 실제 샘플 HTML에 실행해
  `examples/output/` 생성 — 결정론 툴 출력이 진짜 CLI 실행 결과임을 확인.

## v2.0.0 재구성 (표준 이전 작업물 → 표준 준수)

이 번들은 팀의 번들 표준(`agent-factory/bundle-standard.md` §2.5 지식 노드 컨벤션,
`knowledge-arch.md`의 "그래프는 데이터만, 엔진 코드 없음" 결정)이 확정되기 **전에**
만들어졌다. v2.0.0에서 표준에 완전히 맞췄다(breaking restructure — slug 고정, 런타임
데이터 스키마 변경):

- **지식 이동**: `worker/knowledge/*.md` 12개 노드를 `memory/knowledge/`로 이동하고
  `INDEX.md`를 추가. `graph.json`과 `gen:graph` 스크립트 제거.
- **엔진/성장 레이어 제거**: `app/core/knowledge.ts`, `app/growth/` 전체,
  비결정론 도구 9종(`search_knowledge`·`knowledge_neighbors`·`learn_knowledge`·
  `save_persona`·`list_personas`·`get_persona`·`delete_persona`·`remember`·
  `save_workflow`) 삭제. 결정론 도구 6종만 유지(CLI/MCP).
- **페르소나 명시적 입력**: `diagnose_section`/`rewrite_section`이 persona 저장소를
  조회하지 않고 `persona` 객체를 인자로 받는다(`examples/input/persona.json` wire
  형식). MCP `persona://merged` 리소스 제거, `instructions`는 `worker/agent.md`
  원문만.
- **학습 루프 표준화**: 성장 레이어의 역할을 표준 `memory/` 파일로 흡수 —
  `memory/PERSONAS.md`(신규) 추가, 위생·업데이트 후보 규칙을 행동 규칙으로 존치.

### v1 → v2 마이그레이션 노트

v1을 실행하며 홈 디렉터리 성장 레이어(기본값 `~/.web-copy-analyzer/`)에 쌓인 런타임
데이터가 있다면, 다음과 같이 이 번들의 `memory/` 파일로 옮긴다(v2는 그 경로를 더 이상
읽지 않는다):

- `~/.web-copy-analyzer/personas/` → `memory/PERSONAS.md`
- `~/.web-copy-analyzer/voice.md`(브랜드 보이스·금지 표현) → `memory/USER.md`
- `~/.web-copy-analyzer/decisions.log` → `memory/DECISIONS.md`
- `~/.web-copy-analyzer/workflows/` → `worker/skills/` 또는 `memory/COPY-PATTERNS.md`
- `~/.web-copy-analyzer/knowledge/`(learned 노드) → `memory/knowledge/`의 노드
  (`source: learned` 유지)와 `INDEX.md` 한 줄 추가

## Next Improvements

- 로컬 Chromium 렌더 옵션(SPA 폴백) 구현.
- 다국어 리라이트 톤 가이드 확장.
