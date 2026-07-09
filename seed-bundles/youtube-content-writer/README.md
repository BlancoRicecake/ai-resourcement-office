# 유튜브 컨텐츠 작가

영상 아이디어를 입력하면 형식에 맞는 유튜브 영상 원고 또는 토킹포인트를
작성하는 컨텐츠 작가 번들입니다.

## Quick Start

Python 3.8+만 있으면 됩니다. pip 설치가 필요 없습니다.

```bash
python app/app.py
```

브라우저에서 `http://127.0.0.1:8791` 이 열립니다.
API 키가 없어도 무료 템플릿 모드로 바로 사용할 수 있습니다.

LLM 기반 완성형 스크립트를 쓰려면:

1. `.env.example`을 `.env`로 복사
2. `OPENAI_API_KEY=` 뒤에 본인 키 입력
3. 앱 재시작

CLI 실행:

```bash
python app/app.py --cli examples/input/video-brief.md -o content-draft.md
```

## AI Worker

유튜브 컨텐츠 작가 - `worker/agent.md` (지시문), `worker/skills/`
(작업 절차), `worker/harness/` (Claude, Codex 등에서 구동하는 방법)

## 구성

```txt
AGENTS.md   폴더 연결 진입점 (지시문 로드 순서 안내)
app/        미니 SaaS (단일 파일 웹앱 + CLI)
worker/     에이전트 지시문, 스킬, 하네스, MCP 가이드
memory/     학습 루프용 누적 메모리 (운영 원칙, 사용자 선호, 채널 맥락, 원고 이력)
examples/   샘플 입력 + 출력 예시
docs/       빌드 로그, 비용/보안/한계 가이드
```

## User Responsibility

이 패키지는 호스팅 서비스가 아닙니다. 사용자는 자신의 환경과 API 키로 직접
실행하며, 모델 호출 비용과 데이터 보안은 사용자 책임입니다. 실행 전
`docs/security-notes.md`와 `docs/cost-guide.md`를 확인하세요.
