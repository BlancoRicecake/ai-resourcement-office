# AI력 Bundle v0.3 Standard (폴더-번들 · 학습 루프 메모리)

> v0.3은 팀이 롤아웃한 **learning-loop 메모리 표준**(`memory/` + `AGENTS.md` 진입점 +
> `version`)을 정본으로 명문화한다. v0.2가 밀던 "2-뿌리 지식 그래프 우선"은 **정본에서
> 내려가 선택적 강화(부록)**가 됐다 — 이유: 순수 마크다운 `memory/`는 어떤 코딩
> 에이전트든 **런타임 0으로 읽는다**. 이게 "모델 불문 어디서나 붙여넣기" 목표에 가장
> 부합한다. 그래프/성장레이어는 런타임을 동봉하는 코드형 번들에서만 얹는다.

## 0. 정본과 레퍼런스

- 이 문서 = 형식의 단일 출처.
- 순수-마크다운 정본 예시 = 팀 번들(`seed-bundles/youtube-content-writer/` 등).
- 코드형(그래프 강화) 예시 = `seed-bundles/web-copy-analyzer/`.

## 1. 필수 구조

```txt
<slug>/
  AGENTS.md                 폴더 진입점 (§3). 런타임이 폴더를 열면 이 순서로 로드:
                            worker/agent.md → memory/ → worker/skills/
  README.md
  bundle.json               카탈로그 메타 + version (§5)
  .env.example
  LICENSE

  worker/                   에이전트의 "사람" 부분
    agent.md                직무 지침 + 메모리 사용 원칙 + "완료 후 업데이트 후보 제안"
    agent.json              기계 판독 메타
    skills/                 업무 단계별 규칙 문서
    harness/README.md       모델 불문 구동법
    mcp/README.md           (MCP 쓸 때) 등록 가이드

  memory/                   학습 루프 (평문, 다음 세션에 재로드) — §2
    MEMORY.md               고정 운영 원칙 (에이전트가 항상 지킴)
    USER.md                 사용자 선호·톤·산출물 취향·금지사항
    PROJECT.md              현재 맥락 (대상·목표·주력 형식 등)
    DECISIONS.md            승인/보류/반복 적용 기준
    <JOB>.md                직무별 누적 (예: SCRIPTS, BRIEFS, COPY-PATTERNS, CHANNEL)

  examples/{input,output}
  docs/{build-log,cost-guide,security-notes,limitations}.md

  app/                      (선택) 결정론 도구 소스 — 코드형 번들만. core/ 공유, CLI·MCP 어댑터
  plugin/                   (선택) Claude Code 어댑터 — agent.md에서 생성
  worker/knowledge/         (선택·강화) 2-뿌리 지식 그래프 — 부록 A, `knowledge-arch.md`
```

**팀(멀티-멤버) 번들**은 멤버별 `memory/` 대신 **팀 공유 `memory/` 하나**를 두고 멤버들이
공통 참조한다(예: pd-team의 CHANNEL·PRODUCTION-LOG 공유).

언어·런타임 자유. 순수-마크다운 번들이 기본이며 `app/`은 결정론 도구가 필요할 때만 얹는다.
코드형이어도 **두 표면(CLI·MCP)은 하나의 core를 공유**한다(어댑터에 신규 로직 금지).

## 2. 학습 루프 메모리 (`memory/`)

메모리는 **모델 학습(가중치)이 아니라, 다음 세션에서 다시 읽어 적용하는 운영 기록**이다.

- **로드**: 세션 시작 시 `memory/` 전체를 읽어 반영한다. 비어 있으면 신입 상태로 시작한다.
- **기록(학습 루프)**: 업무를 마치면 배운 점·사용자 피드백·유효했던 패턴을
  **`메모리 업데이트 후보`로 제안**한다. **자동 확정 금지** — 사용자가 승인한 것만
  실제 파일에 반영한다(= write_approval). 기존 메모리는 덮어쓰지 않고 병합/교체 후보로
  나란히 제시한다.
- **파일 역할**: MEMORY(불변 운영원칙) / USER(사용자 모델) / PROJECT(맥락) /
  DECISIONS(승인·보류·반복 기준) / `<JOB>`(직무 누적: 이력·잘 통한 패턴·피드백 학습).
- **금지**: API 키·비밀번호·개인정보·원문 발췌를 메모리에 넣지 않는다. 미공개 매출/전환
  실측치 저장 금지. 저작권 있는 원문을 그대로 저장하지 않는다(아이디어만 재서술).
- **출처(provenance)**: 외부 지식을 근거로 삼으면 원문이 아니라 **짧은 출처 표기**만
  남긴다(저자·연도·제목·URL). 고위험 직무(법률·의료·금융·투자·채용)는 전문가 검토·규제
  확인 문구를 함께 적재한다.
- **지식 선적재(seeding)**: 신임 에이전트의 `memory/`는 배포 전 `agent-training-camp`가
  3단계(합법 흡수→실무 합성→적재)로 채워 콜드스타트를 없앨 수 있다(`PIPELINE.md`).

## 3. `AGENTS.md` 진입점

폴더를 코딩 에이전트 런타임(Claude Code/Codex 등)에서 열면 읽히는 연결 문서. 반드시 포함:

1. 이 폴더가 어떤 직원 번들인지 + 로드 순서: `worker/agent.md` → `memory/` → `worker/skills/`
2. 도구 연결 스코프: 외부 도구는 사용자가 실제 쓰는 것만. `.mcp.json`/`.claude/settings.json`이
   있으면 그 범위 안에서만 도구·권한 사용.
3. 범위 밖 요청 처리: 직무 범위를 벗어나면 수행하지 않고 알리며, 적합한 다른 번들 제안.

## 4. `worker/agent.md`

직무 지침(정체성·판단성향·워크플로·절대규칙) + **메모리 사용 원칙 섹션**(어떤 memory 파일이
무엇을 담는지 + "완료 후 `메모리 업데이트 후보` 제안, 자동확정 금지"). 코드형 번들은 여기에
결정론 도구 사용 흐름과 (강화 시) `search_knowledge` 조회를 함께 기술한다.

## 5. bundle.json 필수 메타데이터

- slug, **version** (semver, 기준선 `1.0.0`, `slug` 바로 다음), title, worker, category,
  difficulty, runtime
- requiredKeys (없으면 "없음: 호스트 LLM이 판단"), estimatedCost (결정론 도구 $0 / 호스트
  모델 토큰 별도), includes, requirements
- downloadUrl (`.../releases/latest/download/<slug>.zip`), disclaimer

**version 규칙**: 같은 에이전트의 다음 버전은 **slug를 고정**한다(런타임 데이터 연속성).
메모리 파일 스키마를 크게 바꾸는 메이저 버전은 마이그레이션 안내를 docs에 남긴다.

## 6. 난이도

- Beginner: 폴더를 열고 지침대로 바로 사용.
- Intermediate: 소스 빌드/설정 또는 MCP 등록 필요.
- Advanced: DB·배포·클라우드 설정 필요.

## 7. 공개 체크리스트 (배포 게이트) — 자세히는 `verification.md`

- [ ] `AGENTS.md` 진입점 존재(로드 순서·도구 스코프·범위 밖 규칙)
- [ ] `memory/` 표준 파일(MEMORY/USER/PROJECT/DECISIONS + 직무별) 존재, 학습 루프 규칙이
      agent.md에 기술됨(업데이트 후보 제안·자동확정 금지)
- [ ] `bundle.json`에 `version`(semver) 존재
- [ ] README·`.env.example`·LICENSE 존재, 실제 키/시크릿·원문 발췌 미커밋
- [ ] 샘플 input **및 실제 실행으로 얻은** output 존재(날조 금지)
- [ ] cost-guide·security-notes·limitations 존재, 원본 브랜드·UI·카피 미복제
- [ ] 고위험 직무면 전문가 검토·규제 확인 문구 포함, 출처는 표기만(원문 없음)
- [ ] (코드형) 테스트 그린, core-공유 원칙 준수; (그래프 강화 시) 부록 A 검증 게이트 통과
- [ ] 작성/리뷰 분리 — 같은 컨텍스트 자기승인 금지

## 8. 비협상 규칙

AI력 사무소는 워커를 대신 실행하지 않는다. 사용자가 폴더를 내려받아 본인 환경·모델·예산으로
실행한다. 모든 API·모델·서버·서드파티 비용은 사용자 부담이다.

---

## 부록 A. (선택) 2-뿌리 지식 그래프 강화

런타임(app/)을 동봉하는 코드형 번들은 `memory/` 위에 **지식 그래프**를 얹어 연상 조회·검증
게이트·업데이트 불변 런타임 누적을 추가할 수 있다. seed=`worker/knowledge/`(번들),
learned=`~/.<slug>/knowledge/`(사용자 홈, 업데이트 불변), 병합 조회. 정본 예시는
web-copy-analyzer. 전체 설계는 `knowledge-arch.md`. **순수-마크다운 번들에는 요구되지 않는다.**
