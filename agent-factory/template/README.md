# <번들 이름> (<slug>)

<채울 자리: 한 문단 — 이 번들이 무엇을 입력받아 어떤 판단/산출물을
만드는지, 어떤 전문가 역할을 흉내내는지>

- <핵심 기능 1>
- <핵심 기능 2>
- <핵심 기능 3>

## 모델 불문 설치형

이 번들은 특정 LLM 제공자에 종속되지 않습니다. 결정론 로직(<채울 자리:
fetch·파싱·채점 등>)은 전부 로컬 연산이고, **판단(<채울 자리: 진단·리라이트
등>)은 당신이 쓰는 코딩 에이전트/MCP 클라이언트의 호스트 모델**이 맡습니다.
API 키가 필요 없습니다 — 이미 쓰고 있는 Claude/GPT/Gemini 등 코딩
에이전트가 그대로 전문가 역할을 합니다.

## Quick Start

Node.js 18.17+ 만 있으면 됩니다. 4가지 구동 방법 중 편한 것을 고르세요
(자세한 내용은 `worker/harness/README.md`).

### 1. 미리 빌드된 CLI 직접 실행 (설치 불필요)

```bash
node app/dist/cli.js <서브커맨드> '<json>'
```

### 2. 코딩 에이전트가 worker/agent.md를 읽고 CLI를 도구로 구동

`worker/agent.md`를 시스템 지시문(AGENTS.md/CLAUDE.md)으로 등록하면,
에이전트가 `node app/dist/cli.js <command> '<json>'` 형태로 서브커맨드를
호출합니다.

### 3. MCP 서버로 등록 (Claude Desktop 등)

```json
{
  "mcpServers": {
    "<slug>": {
      "command": "node",
      "args": ["/absolute/path/to/<slug>/app/dist/mcp.js"]
    }
  }
}
```

자세한 내용은 `worker/mcp/README.md` 참고.

### 4. Claude Code 플러그인

`plugin/`을 Claude Code 플러그인으로 설치하면 named agent
(`plugin/agents/<slug>.md`, `worker/agent.md`로부터 생성됨)와 MCP 서버가
함께 등록됩니다.

## AI Worker

- `worker/agent.md` — 이 워커의 정체성·휴리스틱·작업 흐름·주의 케이스를
  담은 단일 소스 지시문.
- `worker/knowledge/` — 자기학습 지식 그래프. 시드 노드(`graph.json`)는
  읽기 전용 검증 지식이고, 런타임에 확인한 일반화 가능한 지식은
  `~/.<slug>/knowledge/`(성장 레이어)에 누적되어 재시작 후에도 살아남습니다.
- `worker/skills/` — 반복 절차 정의.
- `worker/harness/` — 하네스별(플레인 CLI/MCP/플러그인) 구동 가이드.

## 구성

```txt
app/            결정론 코어 + MCP 서버 + CLI (dist/ 프리빌드)
worker/         agent.md, knowledge/, skills/, harness/, mcp/
plugin/         Claude Code 플러그인 (named agent + MCP 번들)
examples/       샘플 입력 + 실제 실행 결과
docs/           빌드 로그, 비용/보안/한계 가이드
```

## 안전·한계

<채울 자리: SSRF 가드, 로컬 처리 원칙, PII/미공개 매출 거부, 절대 규칙
요약 등 — `docs/limitations.md` 참고>

## User Responsibility

이 패키지는 호스팅 서비스가 아닙니다. 사용자는 자신의 환경과 코딩 에이전트/
모델로 직접 실행하며, 그 모델의 토큰 비용과 데이터 보안은 사용자 책임입니다.
실행 전 `docs/security-notes.md`와 `docs/cost-guide.md`를 확인하세요.
