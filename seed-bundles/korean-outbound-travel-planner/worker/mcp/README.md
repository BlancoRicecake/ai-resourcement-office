# MCP integration notes

이 MVP는 MCP 서버를 요구하지 않는다. 항공·숙소·장소·경로 공급자는 FastAPI 서버 측 HTTP 어댑터로 연결한다. 향후 공식 여행 공급자 MCP를 추가하더라도 `TravelInventoryProvider`와 `PlaceRouteProvider`의 정규화 모델을 유지한다.

