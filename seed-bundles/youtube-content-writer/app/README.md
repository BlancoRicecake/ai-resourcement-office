# 미니 SaaS: 유튜브 컨텐츠 원고 작성기

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱입니다.
pip 설치가 필요 없으며 Python 3.8 이상이면 바로 실행됩니다.

## 실행 (웹 UI)

```bash
python app.py
```

브라우저에서 `http://127.0.0.1:8791` 이 자동으로 열립니다.
영상 주제, 타깃 시청자, 영상 형식, 출력 모드, 톤, CTA 목적을 입력하고
"원고 생성"을 누릅니다.

## 실행 (CLI)

```bash
python app.py --cli ../examples/input/video-brief.md -o content-draft.md
```

입력 파일 형식:

```txt
Topic: Notion으로 콘텐츠 캘린더를 관리하는 법
Audience: 1인 창업자와 마케팅 담당자
Format: Product Demo
Output mode: Full Script
Runtime: 6 minutes
Tone: 차분하고 실무적인 말투
CTA: 템플릿 다운로드
Business context: Notion 업무 템플릿을 판매하는 작은 스튜디오
Notes: 화면 녹화와 B-roll 큐를 포함
```

## 실행 모드

| 모드 | 조건 | 동작 |
| --- | --- | --- |
| LLM 모드 | `OPENAI_API_KEY` 설정됨 | OpenAI API로 완성형 영상 원고 생성 |
| 무료 템플릿 모드 | API 키 없음 | 형식별 구조를 가진 영상 원고 골격 생성 |

## 환경변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | (없음) | 없으면 무료 템플릿 모드로 동작 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 사용할 모델 |
| `PORT` | `8791` | 웹 UI 포트 |
