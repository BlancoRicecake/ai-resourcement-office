# MCP 설정

v0.1에서 이 번들은 MCP 서버를 사용하지 않습니다.
미니 SaaS와 CLI만으로 전체 워크플로가 동작합니다.

## 확장 예시 (선택)

에이전트가 로컬 CSV 폴더를 직접 탐색하게 하려면 filesystem MCP 서버를
연결할 수 있습니다. Claude Code 기준 예시:

```bash
claude mcp add reviews-fs -- npx -y @modelcontextprotocol/server-filesystem ./examples/input
```

## 권한 주의

- MCP 서버에는 필요한 최소 폴더만 노출하세요.
- 실제 고객 데이터 폴더를 통째로 연결하기 전에 개인정보 포함 여부를 확인하세요.
