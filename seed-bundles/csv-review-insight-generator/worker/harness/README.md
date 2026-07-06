# Harness: 리뷰 분석 직원 구동 방법

이 워커는 특정 하네스에 종속되지 않습니다. 아래 중 편한 방법을 선택하세요.

## 방법 1: 미니 SaaS 단독 실행 (하네스 불필요)

에이전트 없이 앱만 쓰는 가장 간단한 방법입니다.

```bash
python app/app.py
```

## 방법 2: Claude Code / 코딩 에이전트에서 직원으로 구동

1. 이 번들 폴더를 에이전트 작업 디렉토리로 연다.
2. `worker/agent.md`를 시스템 지시문(또는 CLAUDE.md)으로 등록한다.
3. `worker/skills/`의 스킬 파일을 에이전트가 읽을 수 있게 둔다.
4. 예시 프롬프트:

   > examples/input/sample.csv 리뷰를 분석해서 리포트를 만들어줘.

   에이전트는 `skills/analyze-review-csv.md` 절차에 따라
   `python app/app.py --cli ...`를 실행하고 결과를 검토해 전달합니다.

## 방법 3: 자체 스크립트/스케줄러에 편입

CLI 모드는 종료 코드와 파일 출력을 지원하므로 cron, 작업 스케줄러,
CI 파이프라인에서 바로 호출할 수 있습니다.

```bash
python app/app.py --cli daily-reviews.csv -o reports/$(date +%F).md
```

## 권한 원칙

- 워커에게 필요한 것은 이 번들 폴더의 읽기/쓰기와 `python` 실행 권한뿐입니다.
- 네트워크 접근은 LLM 모드에서 OpenAI API 호출 시에만 발생합니다.
