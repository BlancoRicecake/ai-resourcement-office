# Cost and API Disclosure

외부 영상, 음성, 이미지 API가 필요한 경우 제작 전에 반드시 사용자에게 고지한다.

## Disclosure Template

```md
## 필요한 외부 서비스

- Service:
- Purpose:
- Why it is needed:

## 비용 발생 지점

- Billing unit:
- Estimated usage:
- Where user must verify current price:
- Free/local alternative:

## API 연결 방법

1. 공식 사이트에서 계정을 만든다.
2. 결제 또는 사용량 제한을 설정한다.
3. API 키를 발급한다.
4. `.env` 또는 사용자의 시크릿 저장소에 저장한다.
5. 테스트 요청을 실행한다.
6. 사용량 대시보드에서 과금 여부를 확인한다.

## 필요한 환경변수

- SERVICE_API_KEY=
- SERVICE_MODEL=
- SERVICE_REGION=

## 사용자 확인

- 비용 구조를 이해했나요?
- API 키를 사용자 환경에만 저장할까요?
- 이 방식으로 제작을 진행할까요?
```

## 원칙

- 가격은 서비스마다 자주 바뀌므로 문서 안에서 단정하지 않는다.
- 반드시 공식 가격 페이지나 대시보드에서 사용자가 직접 확인하게 한다.
- 비용이 발생할 수 있으면 무료/로컬 대안을 함께 제시한다.
- API 키를 채팅이나 웹사이트로 전달하라고 하지 않는다.
