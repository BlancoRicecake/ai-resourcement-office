# MCP

v1의 기본 모드는 MCP 서버나 외부 도구 권한을 요구하지 않는다.

사용자가 자동 발행을 원할 때만 옵션으로, 사용자가 실제로 쓰는 발행 플랫폼을 MCP나 API로 연결한다. 대상 예: WordPress/Ghost(블로그·CMS), Stibee/Mailchimp/ConvertKit(뉴스레터), Buffer(SNS 예약). 인스타그램·스레드·링크드인 개인 계정 자동 게시는 플랫폼 API 제약이 크므로 정직하게 고지한다. 세팅 방법은 `worker/skills/publish-connectors.md`를 따르며, 커넥터가 연결돼도 실제 게시는 사용자 컨펌 후에만 실행한다.
