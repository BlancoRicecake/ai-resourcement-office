# BUILD.md — 엔진 코드는 여기 없다, 복사해서 시작한다

이 `template/`은 **린 스켈레톤**이다. 지식 그래프 엔진, 성장 레이어, 빌드
도구는 여기에 중복 구현하지 않는다 — `seed-bundles/web-copy-analyzer/`가
정본 구현(reference implementation)이므로, 새 번들을 만들 때는 그 폴더의
실코드를 **복사해서 리네이밍**한다. (지도는 `agent-factory/reference/README.md`
참고.)

## 복사할 파일과 리네이밍 규칙

### 1. `app/core/` — 결정론 코어

```
seed-bundles/web-copy-analyzer/app/core/knowledge.ts   →  app/core/knowledge.ts   (그대로 복사, 로직 불변)
seed-bundles/web-copy-analyzer/app/core/types.ts        →  app/core/types.ts       (도메인 타입은 새로 정의)
seed-bundles/web-copy-analyzer/app/core/index.ts        →  app/core/index.ts       (export barrel, 새 모듈에 맞게 조정)
```

`knowledge.ts`(노드 파싱, 그래프 빌드, dangling/self-loop 검출,
`graph.json` 직렬화)는 도메인에 무관한 순수 엔진이다 — **그대로 복사**하고
수정하지 않는다. 이 워커 고유의 결정론 로직(파싱·채점·prep 등)만 새 파일로
추가한다.

### 2. `app/growth/` — 성장 레이어 (자기학습)

```
seed-bundles/web-copy-analyzer/app/growth/{frontmatter,fs-utils,hygiene,
  index,knowledge-store,memory-log,merge,paths,store,types}.ts
  → app/growth/ 아래 그대로 복사
```

이 폴더 전체가 도메인 무관 엔진이다(사용자 우선 병합, 위생 필터, 홈 디렉터리
경로 관리, persona/memory/knowledge 저장소). **그대로 복사**한다. 유일하게
고칠 곳은 `paths.ts` 안의 홈 디렉터리 이름이다:

```diff
- const HOME_DIR = ".web-copy-analyzer";
+ const HOME_DIR = ".<slug>";
```

### 3. `app/scripts/` — 빌드/검증 스크립트

```
seed-bundles/web-copy-analyzer/app/scripts/{build,gen-agent,gen-graph}.mjs
  → app/scripts/ 아래 그대로 복사
```

- `gen-graph.mjs` — seed 노드 → `graph.json` 빌드 + 검증 게이트(dangling/
  self-loop/중복 id 실패 시 throw). 경로 상수(`SEED_DIR`)만 확인, 로직은
  불변.
- `gen-agent.mjs` — `worker/agent.md` → `plugin/agents/<slug>.md` 생성.
  슬러그 참조를 바꾼다.
- `build.mjs` — `tsc --noEmit` + esbuild 번들 + plugin agents 생성 오케스트레이션.

### 4. `app/mcp/` — MCP 어댑터

```
seed-bundles/web-copy-analyzer/app/mcp/{index,server,tools,custom-tools,
  instructions,validate,wire,bin}.ts → app/mcp/ 아래 복사
```

`instructions.ts`(agent.md + 성장 레이어 병합 → MCP `instructions`/
`persona://merged` 리소스), `wire.ts`(도구 이름 wiring), `server.ts`(stdio
서버 부트스트랩)는 구조를 그대로 가져오고, `tools.ts`/`custom-tools.ts`만 이
워커의 실제 툴 정의(zod 스키마)로 교체한다. 도구 이름 문자열에서
`web-copy-analyzer` / `web_copy_analyzer`를 `<slug>` / `<slug 언더스코어형>`로
바꾼다.

### 5. `app/cli.ts`

CLI 어댑터 구조(서브커맨드 파싱, `app/core` 핸들러 호출, JSON 입출력)를
그대로 가져오고, 서브커맨드 목록만 이 워커의 것으로 교체한다. CLI 서브커맨드
↔ MCP 툴 이름은 반드시 1:1 대응해야 한다(`bundle-standard.md` §1).

### 6. `worker/harness/README.md`, `worker/mcp/README.md`

`seed-bundles/web-copy-analyzer/worker/harness/README.md`와
`worker/mcp/README.md`의 4가지 실행 모드 구조를 그대로 가져오고, 커맨드
예시와 CLI↔MCP 매핑 표만 이 워커의 것으로 바꾼다.

## 무엇을 새로 쓰나 (엔진이 아닌 것)

- `app/core/`의 도메인 로직(이 워커 고유의 파싱·채점·prep 함수)
- `app/mcp/tools.ts`의 툴 스키마와 핸들러 바인딩
- `worker/agent.md`, `worker/agent.json`, `worker/knowledge/*.md`,
  `worker/skills/*.md` — 전부 이 워커의 도메인 내용
- `plugin/.claude-plugin/plugin.json` — 슬러그·설명만 교체

## 체크리스트

- [ ] `HOME_DIR`(growth/paths.ts)을 `.<slug>`로 바꿨다
- [ ] MCP 툴 이름·CLI 서브커맨드에서 `web-copy-analyzer` 잔재가 없다
- [ ] `app/core`에 도메인 로직 외의 fs/network 코드가 섞이지 않았다
      (core는 순수해야 함 — `bundle-standard.md` §1)
- [ ] `npm run build` 후 `gen-graph.mjs`가 이 워커의 seed 노드로 통과한다
- [ ] `npm test`가 그린이다
