# Build Log

## Source Problem

Content teams need a fast way to create structured briefs for search and AI
answer visibility.

## MVP Scope

Generate a practical content brief from a keyword, product description, and
target audience.

## 2026-07-06: v0.1 구현 완료

- `app/app.py`: Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.
  - 웹 UI (`http://127.0.0.1:8788`) + CLI 모드 (`--cli 입력.md -o 브리프.md`)
  - 입력 파일의 `Keyword:` / `키워드:` 등 한/영 라벨 자동 인식.
  - `OPENAI_API_KEY` 있으면 LLM 모드, 없으면 템플릿 기반 모의(mock) 모드.
  - LLM 프롬프트에 "검색량/순위 단정 금지, 근거 필요 주장은 [확인 필요] 표시"
    규칙 내장.
- `worker/`: skills(브리프 생성 절차), harness(3가지 구동 방법), mcp(미사용 + 확장 예시).
- `examples/`: 실제 CLI 실행으로 생성한 브리프로 교체.
- csv-review-insight-generator와 동일한 아키텍처를 재사용 (번들 표준 검증).

## Next Improvements

- Add competitor URL input.
- Add source/citation fields.
- 키워드 목록 일괄 처리 모드.
