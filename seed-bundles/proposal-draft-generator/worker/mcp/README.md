# MCP 설정

v0.1에서 이 번들은 MCP 서버를 사용하지 않습니다.
미니 SaaS와 CLI만으로 전체 워크플로가 동작합니다.

## 확장 예시 (선택)

과거 제안서 폴더를 에이전트가 참조하게 하려면 filesystem MCP 서버를
연결할 수 있습니다. Claude Code 기준 예시:

```bash
claude mcp add proposals-fs -- npx -y @modelcontextprotocol/server-filesystem ./past-proposals
```

## 권한 주의

- 과거 제안서에는 고객사 기밀이 포함될 수 있습니다. 연결 전에 폴더 내용을
  확인하고, 필요한 최소 폴더만 노출하세요.
