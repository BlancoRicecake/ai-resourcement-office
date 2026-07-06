# Harness: SEO/GEO 브리프 직원 구동 방법

이 워커는 특정 하네스에 종속되지 않습니다. 아래 중 편한 방법을 선택하세요.

## 방법 1: 미니 SaaS 단독 실행 (하네스 불필요)

```bash
python app/app.py
```

## 방법 2: Claude Code / 코딩 에이전트에서 직원으로 구동

1. 이 번들 폴더를 에이전트 작업 디렉토리로 연다.
2. `worker/agent.md`를 시스템 지시문(또는 CLAUDE.md)으로 등록한다.
3. 예시 프롬프트:

   > "AI 직원 패키지" 키워드로 콘텐츠 브리프를 만들어줘. 타깃은 소규모 사업자야.

   에이전트는 `skills/generate-content-brief.md` 절차에 따라
   `python app/app.py --cli ...`를 실행하고 결과를 검토해 전달합니다.

## 방법 3: 콘텐츠 파이프라인에 편입

CLI 모드는 파일 입출력을 지원하므로 키워드 목록을 순회하며 브리프를
일괄 생성할 수 있습니다.

```bash
for kw in keywords/*.md; do python app/app.py --cli "$kw" -o "briefs/$(basename $kw)"; done
```

## 권한 원칙

- 워커에게 필요한 것은 이 번들 폴더의 읽기/쓰기와 `python` 실행 권한뿐입니다.
- 네트워크 접근은 LLM 모드에서 OpenAI API 호출 시에만 발생합니다.
