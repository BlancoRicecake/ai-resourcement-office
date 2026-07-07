# AI Resourcement Office Strategy v0.1

## Positioning

AI Resourcement Office is a free directory for downloadable AI worker packages.

It is different from hosted agent marketplaces. The service does not execute
agents, store user data, or pay model/API costs. Each package helps users set up
an AI worker on their own machine or cloud account.

## One-Line Description

Download AI worker setup packages that include a mini SaaS, agent instructions,
skills, harnesses, MCP examples, and sample outputs.

## Target User

- Solo builders
- Small business operators
- Marketers
- Consultants
- Developers learning AI agent workflows
- Teams that want reusable local AI workflows without vendor lock-in

## v0.1 Scope

Included:

- Static web directory
- Worker and bundle detail cards
- Download/GitHub links
- Standard bundle schema
- Safety and cost guidance
- First 3 seed bundle specs

Excluded:

- Login
- Payments
- Hosted agent execution
- User uploads
- Reviews
- Runtime monitoring
- Managed API keys

## Operating Loop

1. Find a popular SaaS/workflow category.
2. Extract the underlying user problem.
3. Avoid copying brand, UI, or protected assets.
4. Build a small independent mini SaaS around one core workflow.
5. Package the AI worker that can reproduce or maintain that SaaS.
6. Publish the bundle with setup, cost, security, and limitation notes.

## Operating Pipeline v0.2 (2026-07-07 확정)

위 루프를 실제로 굴리는 상시 파이프라인. 각 사이클의 산출물은 "서비스 + 그
서비스를 만들며 탄생한 에이전트 묶음"이며, 묶음은 AI력 사무소 웹 디렉토리에
번들로 올라간다.

1. **리서치 (매일)**: SaaS Research Agent(바탕화면 `SaaS_Research_Agent` 폴더)가
   매일 아침 정해진 시간에 한국·미국 시장의 SaaS 순위, 검색 키워드, SNS
   바이럴을 조사하고, 지금 인기를 얻는 SaaS 하나를 골라 기능을 분해·분석한
   보고서를 생성한다. 보고서 피드백을 반복하며 리서치 품질을 개선한다.
2. **선정**: 누적된 보고서를 보고 만들 서비스(SaaS) 하나를 선정한다.
3. **제작**: 선정한 서비스를 독립적인 미니 SaaS로 직접 만든다 (브랜드·UI·자산
   복제 금지 원칙 유지).
4. **패키징**: 제작 과정에서 탄생한 에이전트들을 번들 표준(bundle-standard.md)
   으로 묶는다.
5. **배포**: AI력 사무소 웹 디렉토리와 GitHub 릴리스에 올린다.
6. 1로 돌아가 반복한다.

## Non-Negotiable Rule

Every public page and README must make this clear:

AI Resourcement Office does not run the worker for the user. The user downloads
the package and runs it with their own environment and budget.

