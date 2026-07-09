# MCP 서버: web-copy-analyzer

web-copy-analyzer의 MCP stdio 서버 소스는 `../../app/mcp/`에 있다(module
resolution이 `app/node_modules`를 찾아야 하므로 소스는 app/ 아래 있어야
한다). 12개 툴(persona 관리 4개 + 결정론 코어 6개 + 성장 레이어 2개)을
노출하고, `../agent.md`를 성장 레이어(`~/.web-copy-analyzer/`)와 병합한 뒤
`instructions`(MCP initialize 응답)와 `persona://merged` 리소스로 내보낸다.

실행 가능한 서버는 빌드 산출물 `app/dist/mcp.js`(단일 파일, 외부 의존성
없음)다 — 릴리스 에셋으로만 배포되며(`dist/`는 저장소에 커밋되지 않는다)
다운로드한 번들에는 이미 포함되어 있다.

## Claude Desktop / Claude Code에 등록

소스에서 빌드하는 경우: `cd app && npm install && npm run build`. 그 후:

```json
{
  "mcpServers": {
    "web-copy-analyzer": {
      "command": "node",
      "args": ["/absolute/path/to/web-copy-analyzer/app/dist/mcp.js"]
    }
  }
}
```

Claude Code plugin 경로로 설치하면(`../../plugin/`) 이 등록이 자동으로 이뤄진다.

## Cursor 등 다른 MCP 클라이언트

동일한 stdio 서버이므로, 클라이언트가 지원하는 형식으로 `node
app/dist/mcp.js`를 커맨드로 등록하면 된다.

## 소스에서 직접 실행 (개발용)

```bash
cd app && npm install
node --import tsx mcp/bin.ts
```
