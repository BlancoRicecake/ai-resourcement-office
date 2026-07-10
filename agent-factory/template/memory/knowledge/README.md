# memory/knowledge/ — 지식 노드 작성 가이드

> 자세한 설계 배경은 `agent-factory/bundle-standard.md` §2.5, `agent-factory/knowledge-arch.md`를
> 먼저 읽는다. 이 폴더는 **엔진(코드) 없이** 마크다운만으로 동작하는 지식 그래프다.

## 노드 형식

```markdown
---
id: <node-id>              # kebab-case, 파일명(확장자 제외)과 동일, 유일
title: <채울 자리: 제목>
tags: [<채울 자리>, <채울 자리>]
source: learned             # seed | learned
confidence: <채울 자리>      # low | med | high
created: <채울 자리: YYYY-MM-DD>
---
<채울 자리: 본문. 관련 노드는 [[다른-node-id]] 형태로 연결한다 — 이게 엣지다.>
```

- 파일명 = frontmatter `id` + `.md`.
- 한 노드 = 일반화 가능한 지식 한 개념. 특정 세션·특정 발화 그대로가 아니라 재사용 가능한
  형태로 재서술한다.

## 승격 규칙

`<JOB>.md`(인박스)에 쌓인 업무 기록 중 **일반화 가능한 교훈**이 확인되면 노드로 승격한다.
원래 항목에는 `→ [[node-id]]`로 승격된 노드를 역참조한다.

## consolidation (정리)

같은 사실·패턴이 반복 확인되면 새 노드를 만들지 말고 기존 노드의 `confidence`를 올린다
(low→med→high). 서로 모순되면 사용자에게 확인을 구한다.

## INDEX.md 갱신

노드를 추가·삭제·수정하면 `INDEX.md`에 한 줄(`- [[id]] 제목 — 태그: …`)을 함께 갱신
후보로 제안한다. **자동확정 금지** — 사용자 승인 후에만 반영한다.
