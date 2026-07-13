---
id: doherty-threshold
title: Doherty 임계 (400ms)
tags:
  - laws
  - performance
  - feedback
source: seed
confidence: high
created: 2026-07-13
---
시스템과 사용자의 응답이 **400ms 이내**로 주고받을 때 생산성과 몰입이 급증한다. 그 이상 지연되면 주의가 흩어진다. **[H10]**

리뷰 관점:

- 클릭·제출 후 반응이 즉시 없으면 사용자는 실패로 오해하고 재클릭한다 — 즉시 피드백(버튼 로딩 상태·낙관적 UI)이 있는가.
- 400ms를 넘길 수밖에 없는 작업은 로딩 인디케이터로 "진행 중"을 알린다. 무엇보다 스켈레톤이 체감 대기를 줄인다. [[loading-skeleton-states]]
- 정적 스크린샷·텍스트 묘사만으로는 실제 응답 시간을 알 수 없으니, 성능 관련 Finding은 "검증 필요"로 표기한다.
- 진행 상태 가시성은 Nielsen 1번(시스템 상태 가시성)과도 연결된다.

체감 속도는 실제 속도만큼 중요하다 — 기다림을 채우는 것도 설계다.

출처: Jon Yablonski, Laws of UX — https://lawsofux.com/laws/doherty-threshold/
