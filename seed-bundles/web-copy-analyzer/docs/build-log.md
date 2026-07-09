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

## 지식 그래프 (두 뿌리)

- **seed 뿌리**: `worker/knowledge/` — H1~H12 휴리스틱을 12개 마크다운 노드로
  증류(`graph.json`은 `npm run gen:graph`로 노드 frontmatter에서 자동 생성).
  읽기 전용, 번들 업데이트 시 덮임.
- **learned 뿌리**: `~/.web-copy-analyzer/knowledge/` — 런타임에 `learn_knowledge`로
  기록되는 일반화 가능한 도메인 지식. 업데이트에 영향받지 않음.
- `search_knowledge`/`knowledge_neighbors`는 seed+learned 병합본을 조회한다.

## 검증

- `npm test` — 155개 테스트 그린 (core/growth/mcp 전 계층: 파서·채점·prep
  컨텍스트·persona·hygiene·knowledge-store·merge·MCP wire/validate/custom-tools).
- `npm run build` — typecheck → 지식 그래프 생성 → esbuild 번들(cli.js/mcp.js)
  → `plugin/agents/web-copy-analyzer.md` 생성(15개 MCP 툴 네임스페이스 확인).
- CLI 스모크: `node app/dist/cli.js parse-sections`/`readability-scorecard`/
  `diagnose-section`을 실제 샘플 HTML에 실행해 `examples/output/` 생성(아래
  참고) — 결정론 툴 출력이 진짜 CLI 실행 결과임을 확인.

## Next Improvements

- 로컬 Chromium 렌더 옵션(SPA 폴백) 구현.
- 웹 쇼룸(결정론 스코어카드 전용, LLM 기능 제외)은 별도 트랙.
- 다국어 리라이트 톤 가이드 확장.
