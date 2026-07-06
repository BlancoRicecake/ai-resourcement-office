# 미니 SaaS: SEO/GEO 콘텐츠 브리프 생성기

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱입니다.
pip 설치가 필요 없으며 Python 3.8 이상이면 바로 실행됩니다.

## 실행 (웹 UI)

```bash
python app.py
```

브라우저에서 `http://127.0.0.1:8788` 이 자동으로 열립니다.
키워드(필수)와 제품 설명, 타깃 고객, 톤(선택)을 입력하고 "브리프 생성"을 누릅니다.

## 실행 (CLI)

```bash
python app.py --cli ../examples/input/brief.md -o brief.md
```

입력 파일 형식 (`Keyword:` / `키워드:` 등 한/영 라벨 모두 인식):

```txt
Keyword: AI 직원 패키지
Product: 다운로드해서 직접 실행하는 AI 에이전트 세팅 패키지
Audience: 개발자, 마케터, 소규모 사업자
```

## 실행 모드

| 모드 | 조건 | 동작 |
| --- | --- | --- |
| LLM 모드 | `OPENAI_API_KEY` 설정됨 | OpenAI API로 완성형 브리프 생성 |
| 모의(mock) 모드 | API 키 없음 | 템플릿 기반 브리프 골격 생성 (무료, 오프라인) |

## 환경변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | (없음) | 없으면 모의 모드로 동작 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 사용할 모델 |
| `PORT` | `8788` | 웹 UI 포트 |

## 보안 메모

- 서버는 `127.0.0.1`(localhost)에만 바인딩되며 외부에서 접근할 수 없습니다.
- 모의 모드에서는 데이터가 PC 밖으로 나가지 않습니다.
- LLM 모드에서는 입력한 키워드/제품 정보가 OpenAI API로 전송됩니다.
