# 지식 노드 INDEX

이 파일은 지식 노드의 목록(엔진 없는 그래프의 색인)이다. 사용 규칙:

- 세션 시작 시 이 **INDEX만** 읽는다. 노드 본문 전체를 미리 로드하지 않는다.
- 작업(진단·리라이트)과 관련된 노드만 골라 열고, 본문의 `[[위키링크]]`를 따라 이웃 노드로 확장한다.
- 노드를 추가·삭제하면 INDEX도 같이 갱신한다 — 단, `메모리 업데이트 후보`로 제안하고 자동 확정하지 않는다(노드와 INDEX 동반 갱신).
- 새 지식은 `memory/COPY-PATTERNS.md`(인박스)에 먼저 쌓고, 일반화 가능한 교훈이 확인되면 노드로 승격한 뒤 아래 "learned 노드"에 같은 형식으로 한 줄 추가한다.

## seed 노드 (번들 동봉 · 검증됨)

- [[attention-ratio]] 어텐션 비율 — 클릭 가능 링크 대 목표 — 태그: cta, above-fold, focus
- [[common-mistakes-checklist]] 흔한 실수 체크리스트 — 태그: checklist, diagnosis, clarity
- [[f-pattern]] F-패턴 — 스캔 동선에 정보어를 태운다 — 태그: layout, readability, clarity
- [[feature-to-benefit]] 기능→혜택 번역 — 태그: benefit, relevance, rewrite
- [[headline-clarity]] 헤드라인 명확성 — 이 문장만 읽어도 아는가 — 태그: headline, clarity, above-fold
- [[hero-five-elements]] 히어로 5요소 — 태그: above-fold, structure, clarity
- [[miss-attribution]] 미스 귀속 프레임 — clarity / trust / relevance / cta — 태그: attribution, framework, diagnosis
- [[objection-handling]] 오브젝션 핸들링 — 반론을 발생 지점에서 해소 — 태그: objection, trust, faq
- [[persona-first]] 페르소나 우선 — 페르소나 없이 진단 불가 — 태그: persona, foundation, relevance
- [[social-proof-placement]] 사회적 증거 배치 — fold 근처·반론 지점 — 태그: social-proof, trust, layout
- [[voc-preservation]] 고객 언어 원문 보존 (VoC) — 태그: voc, trust, preservation
- [[you-we-ratio]] you:we 비율 — 방문자를 주어로 — 태그: voice, relevance, rewrite

## learned 노드 (런타임 학습분)

아직 없음. 런타임에 승격된 노드는 위 seed 노드와 같은 `- [[id]] 제목 — 태그: …` 형식으로 여기에 추가한다.
