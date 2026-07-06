# 미니 SaaS: 온라인 서비스 법률 문서 초안 생성기

Python 표준 라이브러리만 사용하는 단일 파일 로컬 웹앱입니다.
pip 설치가 필요 없으며 Python 3.8 이상이면 바로 실행됩니다.

> ⚠️ 법률 자문이 아닙니다. 생성물은 변호사 검토가 필요한 초안입니다.

## 실행 (웹 UI)

```bash
python app.py
```

브라우저에서 `http://127.0.0.1:8790` 이 자동으로 열립니다.

## 실행 (CLI)

```bash
python app.py --cli ../examples/input/service.md -o legal-docs.md
```

입력 파일 형식 (한/영 라벨 모두 인식):

```txt
Service name: 서비스명
Description: 서비스 설명
Operator: 개인 | 개인사업자 | 법인
Payment: 무료 | 유료
Personal data: 없음 | 이메일, 이름 등
Contact: 이메일
Documents: 이용약관, 개인정보처리방침, 면책조항
```

## 실행 모드

| 모드 | 조건 | 동작 |
| --- | --- | --- |
| LLM 모드 | `OPENAI_API_KEY` 설정됨 | OpenAI API로 서비스 맞춤 초안 생성 |
| 모의(mock) 모드 | API 키 없음 | 대한민국 법령 구조 기반 템플릿 초안 (무료, 오프라인) |

## 환경변수

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `OPENAI_API_KEY` | (없음) | 없으면 모의 모드로 동작 |
| `OPENAI_MODEL` | `gpt-4o-mini` | 사용할 모델 |
| `PORT` | `8790` | 웹 UI 포트 |

## 보안 메모

- 서버는 `127.0.0.1`(localhost)에만 바인딩되며 외부에서 접근할 수 없습니다.
- 모의 모드에서는 데이터가 PC 밖으로 나가지 않습니다.
- LLM 모드에서는 입력한 서비스 정보가 OpenAI API로 전송됩니다.
