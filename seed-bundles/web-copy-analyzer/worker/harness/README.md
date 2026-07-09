# Harness: 카피라이팅 분석가 구동 방법

이 워커는 특정 하네스에 종속되지 않는다. Node.js 18.17+ 만 있으면 아래 중 편한
방법을 선택할 수 있다.

## 방법 1: 미리 빌드된 단일 파일 실행 (npm install 불필요)

번들에 이미 `app/dist/cli.js`와 `app/dist/mcp.js`가 포함되어 있다면(다운로드
릴리스), 그대로 실행한다:

```bash
node app/dist/cli.js parse-sections '{"html":"<html>...</html>"}'
node app/dist/mcp.js   # MCP 클라이언트가 stdio로 이 프로세스를 띄우도록 등록
```

## 방법 2: 소스에서 빌드

```bash
cd app
npm install
npm run build     # tsc --noEmit + esbuild 번들 + plugin/agents 생성
node dist/cli.js parse-sections '{"html":"<html>...</html>"}'
```

## 방법 3: MCP를 쓰지 않는 코딩 에이전트(Codex/Manus 등)에서 직원으로 구동

1. 이 번들 폴더를 에이전트 작업 디렉토리로 연다.
2. `worker/agent.md`를 시스템 지시문(또는 AGENTS.md/CLAUDE.md)으로 등록한다.
3. 에이전트가 `node app/dist/cli.js <command> '<json>'` 형태로 아래 서브커맨드를
   호출하게 한다 — 각각 MCP 툴 1개와 1:1 대응하며 동일한 JSON 입출력 규격을 쓴다.

   | CLI 서브커맨드 | MCP 툴 |
   | --- | --- |
   | `fetch-page` | `fetch_page` |
   | `parse-sections` | `parse_sections` |
   | `readability-scorecard` | `readability_scorecard` |
   | `diagnose-section` | `diagnose_section` |
   | `rewrite-section` | `rewrite_section` |
   | `compare-report` | `compare_report` |
   | `persona save\|list\|get\|delete` | `save_persona`/`list_personas`/`get_persona`/`delete_persona` |
   | `remember` | `remember` |
   | `save-workflow` | `save_workflow` |

4. 예시 프롬프트:

   > 이 URL(https://example.com)의 랜딩페이지 카피를, 저장된 "부트스트랩 창업자"
   > 페르소나 기준으로 진단해줘.

   에이전트는 `worker/agent.md`의 ③ 작업 흐름을 따라 `fetch-page` →
   `parse-sections` → `readability-scorecard` → `diagnose-section` → …
   순서로 CLI를 호출하고 결과를 판단해 전달한다.

## 방법 4: Claude Code에서 named agent + MCP로 구동

`../../plugin/`을 Claude Code 플러그인으로 설치하면 MCP 서버와
`plugin/agents/web-copy-analyzer.md`(named agent, `worker/agent.md`로부터
생성됨)가 함께 등록된다. 이는 여러 설치 경로 중 하나(Claude 전용)이며 기본
형태는 아니다.

## 권한 원칙

- 워커에게 필요한 것은 `node` 실행 권한과, 페르소나/기억을 저장할
  `~/.web-copy-analyzer/` 읽기/쓰기 권한뿐이다.
- `fetch-page`가 외부 URL에 접근한다(SSRF 가드로 사설/로컬 주소는 기본 차단).
  그 외 네트워크 접근은 없다 — 진단·리라이트·비교는 전부 로컬 결정론 연산이다.
