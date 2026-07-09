# Security Notes

실행 전 코드와 권한을 검토하세요.

## Data Handling

- 접근하는 로컬 파일: <채울 자리>
- 호출하는 외부 API/네트워크: <채울 자리 — 없으면 "없음"을 명시>
- 로컬 밖으로 나가는 데이터: <채울 자리 — 없으면 "없음"을 명시>

## 지식/기억 위생 (agent-factory/knowledge-arch.md §3)

- `remember`/`learn_knowledge`는 고객 PII(이메일·전화·주민번호), 미공개
  매출·전환율·트래픽 실측치를 감지하면 자동 거부합니다. 이 거부를 우회하는
  경로는 만들지 않습니다.

## Secrets

`.env` 파일이나 실제 API 키를 커밋하지 마세요.
