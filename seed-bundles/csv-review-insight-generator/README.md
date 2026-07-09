# CSV 리뷰 분석 리포트 생성기

고객 리뷰 CSV를 입력하면 감성 분류, 주요 불만, 개선 요청, 요약 리포트를
생성하는 미니 SaaS 번들입니다.

## Quick Start

Python 3.8+만 있으면 됩니다. pip 설치가 필요 없습니다.

```bash
python app/app.py
```

브라우저에서 `http://127.0.0.1:8787` 이 열립니다.
API 키가 없어도 무료 모의(mock) 모드로 바로 체험할 수 있습니다.

LLM 기반 심층 분석을 쓰려면:

1. `.env.example`을 `.env`로 복사
2. `OPENAI_API_KEY=` 뒤에 본인 키 입력
3. 앱 재시작

CLI 실행:

```bash
python app/app.py --cli examples/input/sample.csv -o report.md
```

## AI Worker

리뷰 분석 직원 — `worker/agent.md` (지시문), `worker/skills/` (작업 절차),
`worker/harness/` (Claude Code 등에서 구동하는 방법)

## 구성

```txt
AGENTS.md   폴더 연결 진입점 (지시문 로드 순서 안내)
app/        미니 SaaS (단일 파일 웹앱 + CLI)
worker/     에이전트 지시문, 스킬, 하네스, MCP 가이드
memory/     누적 학습 메모리 (운영 원칙, 사용자 선호, 프로젝트 맥락, 인사이트)
examples/   샘플 CSV 20행 + 실제 실행으로 생성한 리포트
docs/       빌드 로그, 비용/보안/한계 가이드
```

## User Responsibility

이 패키지는 호스팅 서비스가 아닙니다. 사용자는 자신의 환경과 API 키로 직접
실행하며, 모델 호출 비용과 데이터 보안은 사용자 책임입니다. 실행 전
`docs/security-notes.md`와 `docs/cost-guide.md`를 확인하세요.
