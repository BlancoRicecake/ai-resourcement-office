---
id: form-ux-best-practices
title: 폼 UX 모범 사례
tags:
  - form
  - validation
  - interaction
source: seed
confidence: high
created: 2026-07-13
---
폼은 전환의 최종 관문이다. 마찰 하나가 이탈로 직결된다. **[H6]**

리뷰 관점:

- **레이블 위치** — 레이블은 필드 **위**에 둔다(플레이스홀더를 레이블로 쓰면 입력 시작 후 사라져 회상 부담이 생긴다).
- **인라인 검증 시점** — 검증은 **blur(필드 이탈) 시점**이 최선이다. 타이핑 중 실시간 에러는 방해가 되고, 제출 후에만 검증하면 뒤늦다. 도입 시 오류 감소·완료 속도 향상 효과가 보고된다.
- **에러 메시지** — 원인+해결책을 필드 **바로 아래**에 평문으로. "잘못된 입력"이 아니라 "비밀번호는 8자 이상이어야 합니다". [[microcopy-guidelines]]
- **관대한 입력(Postel)** — 전화번호 하이픈·공백·대소문자를 시스템이 흡수한다. 사용자에게 포맷을 강요하지 않는다.
- **필드 최소화** — 지금 꼭 필요한 것만 받는다. 선택 필드는 나중에.
- **접근성** — 레이블-필드 연결, 포커스 표시, 대비 하한을 지킨다. [[wcag-aa-checklist]]

정적 화면에서는 인라인 검증 동작을 알 수 없으니 "검증 시점 실측 필요"로 표기한다.

출처: WebAIM Form Validation — https://webaim.org/techniques/formvalidation/ , UXPin, Error Feedback — https://www.uxpin.com/studio/blog/error-feedback-best-practices-mobile-forms/
