# Build Log

## Source Problem

Small businesses need a quick way to understand repeated issues in customer
reviews without building a full analytics stack.

## MVP Scope

Analyze CSV reviews and generate a readable Markdown insight report.

## 2026-07-06: v0.1 구현 완료

- `app/app.py`: Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱.
  - 웹 UI (`http://127.0.0.1:8787`) + CLI 모드 (`--cli 입력.csv -o 리포트.md`)
  - `OPENAI_API_KEY` 있으면 LLM 모드(Chat Completions, JSON 응답 강제),
    없으면 키워드 규칙 기반 모의(mock) 모드로 동작.
  - 리뷰 컬럼 자동 인식, 행 수 제한(기본 200행)으로 비용 보호.
  - localhost 전용 바인딩.
- `worker/`: skills(분석 절차), harness(3가지 구동 방법), mcp(미사용 + 확장 예시) 문서화.
- `examples/`: 샘플 20행 CSV와 실제 CLI 실행으로 생성한 리포트.
- 기술 선택 이유: Beginner 난이도 기준 "API 키 + 명령어 하나"를 지키기 위해
  pip 의존성 없는 stdlib 구성을 선택. OpenAI 호출도 `urllib`로 직접 처리.

## Next Improvements

- Add CSV export for classified rows.
- Add issue trend charts.
- 대용량 CSV 배치 분할 처리 (현재는 단일 요청).
