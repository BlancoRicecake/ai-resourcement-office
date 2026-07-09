# 레퍼런스 구현: `seed-bundles/web-copy-analyzer/`

이 번들이 `bundle-standard.md` v0.2와 `knowledge-arch.md`를 실제로 구현한
**정본 예시**다. 새 번들을 만들 때 "이 패턴을 보려면 이 파일" 지도로 쓴다.

| 보고 싶은 패턴 | 파일 |
| --- | --- |
| 2-뿌리 지식 그래프 엔진(노드 파싱, 빌드, dangling/self-loop 검출) | `app/core/knowledge.ts` |
| 성장/자기학습 레이어(병합, 위생 필터, 저장소) | `app/growth/` (`merge.ts`, `hygiene.ts`, `knowledge-store.ts`, `store.ts`, `paths.ts`) |
| seed 노드 실제 예시 (frontmatter + `[[wikilink]]`) | `worker/knowledge/*.md` (예: `hero-five-elements.md`) |
| 자기학습 행동 강령(agent.md에 주입하는 형태) | `worker/agent.md` §5 |
| agent.md 표준 섹션 구조(①~⑤) | `worker/agent.md` 전체 |
| CLI/MCP가 공유하는 core 어댑터 패턴 | `app/cli.ts` + `app/mcp/`(`tools.ts`, `wire.ts`, `instructions.ts`) |
| 빌드·검증 게이트(seed → graph.json, dangling/self-loop/중복 실패 처리) | `app/scripts/gen-graph.mjs` + `app/core/__tests__/knowledge-seed.test.ts` |
| named agent 생성(agent.md → plugin) | `app/scripts/gen-agent.mjs` |
| 하네스별 구동 가이드(4가지 실행 모드) | `worker/harness/README.md` |
| MCP 등록 가이드 | `worker/mcp/README.md` |
| 절차 시드(skills) 실제 예시 | `worker/skills/persona-interview.md`, `full-page-diagnosis.md` |
| 문서/예시 산출물 형태 | `docs/*.md`, `examples/` |
| bundle.json 실제 채움 예시 | `bundle.json` |

새 번들을 시작할 때는 `agent-factory/template/`(빈 스켈레톤)을 복사한 뒤,
`agent-factory/template/BUILD.md`가 안내하는 대로 위 표의 엔진/도구
코드를 이 번들에서 그대로 복사해 리네이밍한다. 도메인 로직(파싱·채점 등)과
`agent.md`/`worker/knowledge/`의 실제 내용만 새로 작성한다.
