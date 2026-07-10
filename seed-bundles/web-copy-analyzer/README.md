# 웹 카피 분석기 (web-copy-analyzer)

사이트 URL(또는 HTML)과 타깃 구매자 페르소나를 넣으면, 그 페르소나의 눈으로
랜딩페이지 반응을 진단하고 전환 카피 리라이트 리포트를 만드는 **전환 카피
컨설턴트** 번들입니다.

- above-the-fold부터 섹션별로 "무엇을/누구를/다음 행동"이 5초 안에 전달되는지
  시뮬레이션
- 이탈 요인을 명확성/신뢰/관련성/CTA 네 축으로 귀속
- 미스 섹션만 페르소나 어휘·톤으로 리라이트 (후기·증언 원문은 절대 보존)
- before/after 비교 리포트 + 보존 검증

## 모델 불문 설치형

이 번들은 특정 LLM 제공자에 종속되지 않습니다. 결정론 로직(fetch·파싱·채점·
저장·비교)은 전부 로컬 Node.js 연산이고, **판단(진단·리라이트·페르소나 합성)은
당신이 쓰는 코딩 에이전트/MCP 클라이언트의 호스트 모델**이 맡습니다. API 키가
필요 없습니다 — 이미 쓰고 있는 Claude/GPT/Gemini 등 코딩 에이전트가 그대로
분석가 역할을 합니다.

## Quick Start

Node.js 18.17+ 만 있으면 됩니다. 4가지 구동 방법 중 편한 것을 고르세요
(자세한 내용은 `worker/harness/README.md`).

### 1. 미리 빌드된 CLI 직접 실행 (설치 불필요)

```bash
node app/dist/cli.js parse-sections '{"html":"<html>...</html>"}'
```

### 2. 코딩 에이전트가 worker/agent.md를 읽고 CLI를 도구로 구동 (Codex/Manus 등)

`worker/agent.md`를 시스템 지시문(AGENTS.md/CLAUDE.md)으로 등록하면, 에이전트가
`node app/dist/cli.js <command> '<json>'` 형태로 서브커맨드를 호출합니다 —
`fetch-page`, `parse-sections`, `readability-scorecard`, `diagnose-section`,
`rewrite-section`, `compare-report`, `persona save|list|get|delete`,
`remember`, `save-workflow`, `search-knowledge`, `knowledge-neighbors`,
`learn-knowledge`.

### 3. MCP 서버로 등록 (Claude Desktop 등)

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

자세한 내용은 `worker/mcp/README.md` 참고.

### 4. Claude Code 플러그인

`plugin/`을 Claude Code 플러그인으로 설치하면 named agent
(`plugin/agents/web-copy-analyzer.md`, `worker/agent.md`로부터 생성됨)와 MCP
서버가 함께 등록됩니다.

## AI Worker

- `worker/agent.md` — 카피라이팅 분석가의 정체성·휴리스틱(H1~H12)·작업 흐름·
  주의 케이스를 담은 단일 소스 지시문. MCP `instructions`/named agent 모두 이
  문서로부터 나옵니다.
- `worker/knowledge/` — 자기학습 지식 그래프. 시드 12개 노드(`graph.json`)는
  읽기 전용 검증 지식이고, 런타임에 확인한 일반화 가능한 지식은
  `~/.web-copy-analyzer/knowledge/`(성장 레이어)에 누적되어 재시작 후에도
  살아남습니다. `search_knowledge`/`knowledge_neighbors`는 이 병합본을
  조회합니다.
- `worker/skills/` — 페르소나 인터뷰, 전체 진단 루프 같은 절차 정의.
- `worker/harness/` — 하네스별(플레인 CLI/MCP/플러그인) 구동 가이드.

## 구성

```txt
AGENTS.md       폴더 진입점 — 로드 순서·도구 스코프·범위 밖 규칙
memory/         학습 루프 (MEMORY/USER/PROJECT/DECISIONS/COPY-PATTERNS, 순수 마크다운 기반)
app/            결정론 코어(파싱/채점/prep) + MCP 서버 + CLI (dist/ 프리빌드)
worker/         agent.md, knowledge/(그래프 강화), skills/, harness/, mcp/
plugin/         Claude Code 플러그인 (named agent + MCP 번들)
examples/       샘플 페르소나·랜딩페이지 HTML + 실제 실행 결과
docs/           빌드 로그, 비용/보안/한계 가이드
```

학습 루프는 두 표현으로 하나다: `memory/`는 어떤 코딩 에이전트든 런타임 0으로 읽는
**기반**(완료 후 `메모리 업데이트 후보` 제안, 자동 확정 금지)이고, `worker/knowledge/`
지식 그래프 + 성장 레이어(`~/.web-copy-analyzer/`)는 CLI/MCP로 자동화하는 **런타임 강화**다.
자세한 로드 순서는 `AGENTS.md` 참고.

## 안전·한계

- `fetch_page`는 SSRF 가드로 사설망·루프백·메타데이터 주소를 기본 차단합니다.
- 진단·리라이트는 로컬에서만 처리되며, 미공개 페이지·매출 수치를 외부로
  보내지 않습니다.
- `remember`/`learn_knowledge`는 PII·미공개 매출 등 민감 정보를 자동 거부합니다.
- 저장된 타깃 페르소나 없이는 진단을 시작하지 않습니다. 후기·증언 원문은
  절대 다시 쓰지 않습니다.
- 프렙 툴(`diagnose_section`/`rewrite_section`)은 LLM을 호출하지 않고 판단
  재료(payload)만 반환합니다 — 실제 판단 품질은 호스트 모델에 달려 있습니다.
  자세한 한계는 `docs/limitations.md` 참고.

## User Responsibility

이 패키지는 호스팅 서비스가 아닙니다. 사용자는 자신의 환경과 코딩 에이전트/
모델로 직접 실행하며, 그 모델의 토큰 비용과 데이터 보안은 사용자 책임입니다.
실행 전 `docs/security-notes.md`와 `docs/cost-guide.md`를 확인하세요.
