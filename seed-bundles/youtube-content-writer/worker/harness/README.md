# Harness: 유튜브 컨텐츠 작가 구동 방법

이 워커는 특정 하네스에 종속되지 않습니다. 아래 중 편한 방법을 선택하세요.

## 방법 1: 미니 SaaS 단독 실행

```bash
python app/app.py
```

## 방법 2: Claude Code / Codex에서 직원으로 구동

1. 이 번들 폴더를 에이전트 작업 디렉토리로 연다.
2. `worker/agent.md`를 시스템 지시문 또는 프로젝트 지시문으로 등록한다.
3. 예시 프롬프트:

   > Notion 템플릿을 소개하는 6분짜리 Product Demo 유튜브 대본 만들어줘.
   > 말투는 차분하고 실무자 친화적으로 해줘.

4. 에이전트는 `worker/skills/write-youtube-content.md` 절차에 따라 CLI를 실행하고
   결과를 검토해 전달합니다.

## 방법 3: 콘텐츠 파이프라인에 편입

영상 기획 시트를 `examples/input/video-brief.md` 같은 입력 파일 형식으로 저장하면
CLI로 스크립트를 자동 생성할 수 있습니다. 생성된 대본은 촬영 전에 사람이 검수하세요.

## 권한 원칙

- 워커에게 필요한 것은 이 번들 폴더의 읽기/쓰기와 `python` 실행 권한뿐입니다.
- 네트워크 접근은 LLM 모드에서 OpenAI API 호출 시에만 발생합니다.
