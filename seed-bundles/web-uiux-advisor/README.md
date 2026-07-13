# UI·UX 자문가 번들

기획안이나 기존 화면(URL·스크린샷·HTML)을 넣으면, 현업 UI/UX 리뷰 프레임워크로 진단해 **근거 있는 리뷰 리포트**를 만드는 AI 직원이다. "예쁜 화면"이 아니라 **사용자가 목적을 달성하는 화면**을 본다. 모든 지적은 위치 + 근거(휴리스틱·법칙·접근성 기준) + 개선안으로 환원한다. 화면을 직접 구현하지는 않는다 — 진단하고 자문한다.

## Quick Start

1. 이 폴더를 코딩 에이전트 런타임(Claude Code, Codex 등)이나 LLM 채팅에서 연다.
2. 런타임이 `AGENTS.md`의 로드 순서대로 `worker/agent.md` → `memory/` → `worker/skills/`를 읽게 한다. (수동이면 `worker/agent.md` 내용을 시스템 지시문에 넣는다.)
3. 두 가지 시나리오 중 하나로 요청한다.
   - **기획 자문**: "이런 서비스를 만들려는데 설계 방향과 레퍼런스를 추천해줘" + 서비스 설명/기획안.
   - **화면 리뷰**: "이 화면을 진단해줘" + URL 또는 스크린샷 또는 화면의 텍스트 묘사/HTML.
4. 자문가가 인테이크 질문(서비스·타깃·목표·플랫폼)을 먼저 하고, 답이 모이면 리뷰 리포트를 낸다.

필수 API 키가 없다. 판단은 이 번들을 구동하는 호스트 모델이 맡는다.

## AI Worker

`UI·UX 자문가`는 시니어 UI/UX 자문가 페르소나로 동작한다.

- **정체성**: 심미가 아니라 사용성을 본다. 근거 없는 지적을 하지 않고, 검증 못 한 부분은 명시한다. 서비스 특성·타깃 사용자를 모르면 진단을 시작하지 않는다.
- **지식**: Nielsen 10대 휴리스틱, Laws of UX(Fitts/Hick/Jakob 등), WCAG 2.2 AA, 정보구조·폼·모바일 체크포인트, 레퍼런스 갤러리·디자인 시스템, 한국 시장 관습을 **31개 지식 노드 그래프**로 담는다.
- **산출물**: Executive Summary → Finding(위치 + 근거 + 위반 휴리스틱/법칙 인용 + 심각도 0~4) → 우선순위(심각도 × 수정난이도) → 개선안(Before/After + 텍스트 와이어프레임) → 레퍼런스 근거. 코드·시각 시안은 범위 밖이며, 필요하면 구현 스킬 이름을 지목해 넘긴다.

## 구성 트리

```txt
web-uiux-advisor/
  AGENTS.md                 폴더 진입점 (로드 순서·도구 스코프·범위 밖 규칙)
  README.md  bundle.json  .env.example  LICENSE
  worker/
    agent.md                핵심 페르소나·워크플로·절대규칙·메모리 원칙
    agent.json              기계 판독 메타
    skills/                 ui-review-intake · landing-page-review · evidence-based-audit
    harness/README.md       모델 불문 구동법
    mcp/README.md           (v1 MCP 미사용 안내)
  memory/                   학습 루프 (다음 세션 재로드)
    MEMORY.md USER.md PROJECT.md DECISIONS.md REVIEWS.md
    knowledge/              31개 지식 노드 + INDEX.md (엔진 없는 그래프)
  examples/{input,output}   기획 브리프·화면 묘사 예시 + 실제 리뷰 리포트
  docs/                     build-log · cost-guide · security-notes · limitations
```

## 안전·한계

- 자문가의 진단은 휴리스틱 기반 예측이지 **실사용자 테스트를 대체하지 않는다.**
- 심미 트렌드(예: 특정 연도의 미학)는 시효가 있으므로 리포트에 시점을 명시한다.
- 확인 못 한 수치·전환율을 창작하지 않는다. 미공개 화면·내부 지표는 memory에 기록하지 않는다.
- 판단 품질은 이 번들을 구동하는 호스트 모델의 능력에 좌우된다.

일부 워크플로우 구조는 [github.com/MengTo/Skills](https://github.com/MengTo/Skills) (MIT, Meng To)에서 영감을 받아 재구성했다.
