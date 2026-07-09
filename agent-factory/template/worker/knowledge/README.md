# worker/knowledge/ — seed 지식 그래프 작성 가이드

여기에 이 워커의 **검증된, 읽기 전용 큐레이션 지식**을 마크다운 노드로
채운다. 자세한 설계 배경은 `agent-factory/knowledge-arch.md`를 먼저 읽는다.

## 노드 형식

```markdown
---
id: hero-five-elements        # kebab-case, 파일명(확장자 제외)과 동일, 유일
title: 히어로 5요소
tags: [above-fold, structure]
source: seed                  # seed 노드는 항상 seed
confidence: high              # seed는 항상 high
---
본문. 다른 노드는 [[attention-ratio]] 처럼 연결한다 — 이게 엣지다.
```

- 파일명 = frontmatter `id` + `.md`. 하나라도 다르면 빌드가 실패한다.
- `agent.md` ②의 휴리스틱(H-라벨)을 노드로 증류하는 것이 자연스러운
  출발점이다 — 휴리스틱마다 노드 하나, 서로 연관된 원칙은 `[[wikilink]]`로
  엮는다.
- seed 노드는 **번들 업데이트 시 통째로 교체**된다. 런타임에 학습된 지식은
  여기 쓰지 않는다(성장 레이어 `~/.<slug>/knowledge/`로 간다 — `agent.md`
  §5 참고).

## 빌드 & 검증 게이트

`app/scripts/gen-graph.mjs`(레퍼런스: `seed-bundles/web-copy-analyzer/app/scripts/gen-graph.mjs`)가
이 폴더의 `*.md`를 읽어 `graph.json`을 생성한다. 다음을 위반하면 빌드가
**실패해야 한다**(사람이 눈으로 확인하고 넘어가지 않는다):

- 어떤 `[[wikilink]]`가 존재하지 않는 seed id를 가리킴 (dangling)
- self-loop (노드가 자기 자신을 링크)
- 중복 id
- frontmatter `id` ≠ 파일명
- 커밋된 `graph.json`이 재빌드 결과와 다름(비동기화)

자세한 통과 기준은 `agent-factory/verification.md` §5를 본다.

## 이 폴더에 있어야 할 것

- 각 개념당 `.md` 노드 파일 여러 개
- 빌드 산출물 `graph.json` (커밋한다 — 프리빌드 dist가 참조)

`.gitkeep`은 이 폴더가 빈 상태로도 git에 잡히게 하는 자리 표시자이며, 실제
노드를 채우면 지워도 된다.
