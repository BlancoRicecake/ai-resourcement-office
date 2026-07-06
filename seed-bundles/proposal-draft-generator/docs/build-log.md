# Build Log

## Source Problem

Consultants and small teams need to turn rough client requests into structured
proposal drafts quickly.

## MVP Scope

Generate a proposal outline and first draft from client problem, service scope,
budget, and timeline.

## 2026-07-06: v0.1 구현 완료

- `app/app.py`: Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.
  - 웹 UI (`http://127.0.0.1:8789`) + CLI 모드 (`--cli 입력.md -o 제안서.md`)
  - 입력 파일의 `Client problem:` / `고객 문제:` 등 한/영 라벨 자동 인식.
  - `OPENAI_API_KEY` 있으면 LLM 모드, 없으면 8개 섹션 템플릿 기반 mock 모드.
  - "가격·일정·계약 조건은 초안이며 사람이 검토해야 한다" 경고를 문서와
    프롬프트 양쪽에 내장.
- `worker/`: skills(초안 작성 절차 + 기밀 확인 규칙), harness, mcp 문서화.
- `examples/`: 실제 CLI 실행으로 생성한 제안서 초안으로 교체.
- csv/seo 번들과 동일한 아키텍처를 재사용 (번들 표준 3회 검증 완료).

## Next Improvements

- Add export to DOCX.
- Add reusable service menu templates.
- Add risk and assumption sections.
