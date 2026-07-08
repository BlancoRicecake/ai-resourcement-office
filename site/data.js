window.AIRO_DATA = {
  workers: [
    {
      name: "컨텐츠 기획자",
      slug: "youtube-content-planner",
      category: "기획",
      summary:
        "채널 방향, 타깃 시청자, 주제 후보, 시리즈 구조, 영상 목적을 설계한다.",
      skills: ["채널 전략", "주제 발굴", "시리즈 기획"],
      tools: ["YouTube Studio 입력값"],
      output: "영상 기획 브리프",
      downloadUrl: "./downloads/youtube-content-planner.zip",
      details: {
        workflow: [
          "기존 채널인지 신규 채널인지 먼저 확인한다.",
          "기존 채널이면 URL·대표 영상·원고·썸네일·제목/설명란·성과 메모로 채널 정체성을 파악한다.",
          "최근 3-12개월 자료와 경쟁 채널 관찰로 기획 근거를 수집한다.",
          "기획 방향을 확정하기 위한 사용자 선택 질문 4개를 제시한다.",
          "답변을 반영해 주제·근거·시청자·약속·CTA를 담은 기획 브리프를 작성한다.",
          "확정된 브리프를 원고 작가에게 핸드오프한다."
        ],
        setup: [
          "OpenAI API 키는 선택 사항이다. 없으면 문서 기반으로만 동작한다.",
          "기존 채널이면 채널 URL과 대표 영상 3-5개를 준비한다.",
          "기존 원고·썸네일·업로드 제목·설명란·성과 메모가 있으면 함께 제공한다.",
          "신규 채널이면 분야·타깃·목표·출연 여부·제작 빈도를 미리 정리한다."
        ],
        advanced: [
          {
            title: "리서치 원칙 조정",
            body:
              "기본은 최근 3-12개월 데이터 우선이다. 채널 특성상 더 긴 기간이나 특정 출처(공식 문서·업계 리포트)를 우선하고 싶으면 그 기준을 알려 고정한다."
          },
          {
            title: "피드백 규칙화(feedback-rules)",
            body:
              "사용자 피드백은 자동으로 영구 규칙이 되지 않는다. '앞으로도 이 기준을 계속 적용할까요?'에 동의한 항목만 채널 규칙으로 저장된다."
          },
          {
            title: "채널 매니저 피드백 수용",
            body:
              "채널 매니저가 성과 분석으로 전달한 지시(근거·검증 지표 포함)를 다음 기획에 반영한다. 사용자 확정 규칙과 충돌하면 사용자에게 먼저 확인한다."
          }
        ]
      }
    },
    {
      name: "영상 원고 작가",
      slug: "youtube-script-writer",
      category: "원고",
      summary:
        "후킹, 구성, 멘트, 전환 문장, CTA를 담은 촬영 가능한 영상 원고를 작성한다.",
      skills: ["후킹 작성", "원고 구성", "CTA 설계"],
      tools: ["Markdown"],
      output: "유튜브 영상 원고",
      downloadUrl: "./downloads/youtube-script-writer.zip",
      details: {
        workflow: [
          "이번 영상이 숏폼인지 롱폼인지 먼저 확인한다.",
          "기획 브리프를 바탕으로 원고 분위기 선택지를 제안하고 사용자가 고르게 한다.",
          "첫 15초 후킹과 섹션별 예상 시간·전환 문장을 담은 초안을 작성한다.",
          "초안을 사용자에게 컨펌 요청한다.",
          "피드백이 오면 전체 재작성 대신 해당 위치만 정확히 찾아 반영한다.",
          "컨펌되면 장면·시간·화면 큐를 붙여 영상 제작자에게 핸드오프한다."
        ],
        setup: [
          "OpenAI API 키는 선택 사항이다.",
          "기획자가 넘긴 기획 브리프를 준비한다.",
          "숏폼/롱폼 여부를 먼저 정한다. 정해지지 않으면 원고를 쓰지 않는다.",
          "원고 분위기(전문가형·조언형·문제해결형·스토리텔링형 등)를 선택한다."
        ],
        advanced: [
          {
            title: "수정 유형별 반영(revision-rules)",
            body:
              "피드백은 Hook·Structure·Tone·Evidence·CTA·Safety로 분류해 필요한 구간만 수정한다. 검증되지 않은 수치는 [검증 필요]로 표시한다."
          },
          {
            title: "채널 매니저 피드백 수용",
            body:
              "후킹 방식·구조·길이·이탈 구간 개선 지시를 다음 원고에 반영하고, 어느 구간에 어떻게 반영했는지 기록한다. 사용자 피드백과 충돌하면 사용자 우선."
          }
        ]
      }
    },
    {
      name: "영상 제작자",
      slug: "youtube-video-producer",
      category: "제작",
      summary:
        "촬영 구성, B-roll, 화면 큐, 편집 가이드, 썸네일 방향을 정리한다.",
      skills: ["촬영 큐", "편집 가이드", "썸네일 방향"],
      tools: ["Production checklist"],
      output: "제작 가이드",
      downloadUrl: "./downloads/youtube-video-producer.zip",
      details: {
        workflow: [
          "원하는 제작 형식을 먼저 확인한다(PPT형·이미지형·화면녹화형·실사·AI영상·TTS 등).",
          "형식별로 무료/로컬 방식과 외부 API 비용이 필요한 방식을 구분해 고지한다.",
          "선호 스타일 세팅이 끝난 뒤에만 제작 초안을 만든다.",
          "촬영 구성·B-roll·화면 큐·자막 포인트·썸네일 방향을 정리한다.",
          "제작 초안을 사용자에게 컨펌 요청하고, 피드백을 반영한다.",
          "컨펌된 제작 정보를 채널 매니저에게 핸드오프한다."
        ],
        setup: [
          "OpenAI API 키는 선택 사항이다.",
          "작가가 넘긴 컨펌된 원고(장면·시간·화면 큐 포함)를 준비한다.",
          "제작 형식과 예산/외부 API 사용 의향을 정한다.",
          "선호 영상 스타일(미니멀·역동적·교육형·브랜드 고급형 등)을 정한다."
        ],
        advanced: [
          {
            title: "비용/API 고지 원칙",
            body:
              "비용이 발생할 수 있는 작업은 실행 전에 반드시 고지한다. 가격은 단정하지 않고 서비스 공식 페이지 기준으로 확인하게 하며, 무료/로컬 대안을 먼저 제시한다."
          },
          {
            title: "제작 선호 규칙 저장(production-preferences)",
            body:
              "'더 세련되게' 같은 추상 피드백은 속도/신뢰/브랜드/전환 중심 방향 선택지로 좁힌다. 동의한 방향만 기본 제작 스타일로 저장된다."
          },
          {
            title: "채널 매니저 피드백 수용",
            body:
              "썸네일 방향·CTR 개선·이탈 구간의 컷/리듬 수정 지시를 다음 제작에 반영한다. 저장된 선호 규칙과 충돌하면 사용자 우선."
          }
        ]
      }
    },
    {
      name: "채널 매니저",
      slug: "youtube-channel-manager",
      category: "운영",
      summary:
        "업로드 메타데이터, 제목/썸네일 실험, YouTube Studio 지표 분석, 다음 영상 개선안을 만든다.",
      skills: ["업로드 패키징", "지표 분석", "개선안 작성"],
      tools: ["YouTube Studio 수동 입력"],
      output: "채널 운영 리포트",
      downloadUrl: "./downloads/youtube-channel-manager.zip",
      details: {
        workflow: [
          "제목·설명란·챕터·고정 댓글 등 업로드 메타데이터를 만든다.",
          "썸네일/제목 실험 후보를 정리한다.",
          "게시 후 데이터 제공 방식을 확인하고 YouTube Studio 지표를 받는다.",
          "CTR·평균 시청 지속 시간·이탈 구간을 해석한다.",
          "채널 평균 대비 상위 성과 영상을 식별하고 차별점을 근거와 함께 분석한다.",
          "핵심 개선 1-3개를 골라 기획자·작가·제작자에게 실행 지시로 핸드오프한다."
        ],
        setup: [
          "OpenAI API 키는 선택 사항이다.",
          "데이터 제공 방식을 먼저 고른다. 기본은 수동 입력과 CSV 내보내기이며 별도 세팅이 필요 없다.",
          "단일 영상 회고면 performance-review 항목(CTR·평균 시청 지속·이탈 구간·댓글 반응)을 입력한다.",
          "영상 간 비교 분석을 원하면 최근 영상 10-20개의 제목·조회수 또는 Studio 고급 모드 CSV를 준비한다."
        ],
        advanced: [
          {
            title: "① Studio CSV 내보내기 (권장·무료)",
            body:
              "YouTube Studio → 분석 → 고급 모드 → 내보내기(CSV). 기간을 정해 채널 전체 영상 지표를 받아 붙여넣으면 영상 간 비교 분석이 가능하다. 세팅 없이 가장 정밀한 분석을 얻는 방법이다."
          },
          {
            title: "② YouTube Data API v3 (API 키·무료 할당량)",
            body:
              "Google Cloud Console에서 프로젝트 생성 → 'YouTube Data API v3' 사용 설정 → API 키 발급 → 로컬 환경변수 YOUTUBE_API_KEY에 저장. 조회수·좋아요·댓글 수 자동 수집이 되지만 CTR·노출·시청 지속 시간은 제공하지 않는다."
          },
          {
            title: "③ YouTube Analytics API (소유자 OAuth·난이도 높음)",
            body:
              "Data API 프로젝트에 'YouTube Analytics API'를 추가 사용 설정하고 OAuth 동의 화면·데스크톱 클라이언트를 만든 뒤 본인 채널 계정으로 인증(yt-analytics.readonly 권장). CTR·노출·이탈 구간까지 자동 수집된다. 부담되면 같은 지표를 주는 CSV로 대체한다."
          }
        ]
      }
    },
    {
      name: "직무 분석가",
      slug: "job-role-analyst",
      category: "HR",
      summary:
        "직무 설명, 채용 공고, 업무 범위를 분석해 역할 정의, 필요 역량, 평가 기준을 정리한다.",
      skills: ["직무 분석", "역량 정의", "평가 기준 설계"],
      tools: ["Job description"],
      output: "직무 분석 리포트",
      details: {
        workflow: [
          "분석할 직무 설명·채용 공고·업무 범위 자료를 받는다.",
          "핵심 책임과 성과 기대치를 역할 정의로 정리한다.",
          "역할 수행에 필요한 필수 역량과 우대 역량을 도출한다.",
          "역량별로 관찰 가능한 평가 기준과 지표를 설계한다.",
          "역할 정의·역량·평가 기준을 담은 직무 분석 리포트를 출력한다."
        ],
        setup: [
          "OpenAI API 키는 선택 사항이다.",
          "분석 대상 직무 설명 또는 채용 공고 원문을 준비한다.",
          "조직 맥락(팀 규모·목표·기존 역할과의 관계)이 있으면 함께 제공한다."
        ],
        advanced: [
          {
            title: "평가 기준 커스터마이징",
            body:
              "기본은 관찰 가능한 행동 지표 중심이다. 조직의 기존 평가 체계(등급·역량 모델)가 있으면 그 형식에 맞춰 출력하도록 기준을 지정할 수 있다."
          }
        ]
      }
    }
  ],
  teams: [
    {
      title: "유튜브 콘텐츠 PD팀",
      slug: "youtube-content-pd-team",
      version: "v0.1",
      category: "유튜브 기획·제작·운영",
      summary:
        "컨텐츠 기획자, 영상 원고 작가, 영상 제작자, 채널 매니저가 함께 유튜브 콘텐츠를 기획부터 성과 회고까지 운영하는 팀.",
      runtime: "로컬 실행 (문서 기반 팀 패키지, API 연동은 후속 버전)",
      requiredKeys: ["필수 키 없음 · OpenAI는 선택(무료 모드)"],
      status: "무료 다운로드",
      includes: ["4명 AI 직원", "agent.md", "workflow", "sample briefs", "ops checklist"],
      members: [
        "youtube-content-planner",
        "youtube-script-writer",
        "youtube-video-producer",
        "youtube-channel-manager"
      ],
      flow: [
        {
          from: "youtube-content-planner",
          to: "youtube-script-writer",
          label: "기획 브리프",
          desc: "주제·타깃 시청자·핵심 약속·CTA를 확정해 원고 작가에게 넘긴다."
        },
        {
          from: "youtube-script-writer",
          to: "youtube-video-producer",
          label: "컨펌된 원고",
          desc: "후킹·구성·멘트에 장면·예상 시간·화면 큐를 붙여 영상 제작자에게 넘긴다."
        },
        {
          from: "youtube-video-producer",
          to: "youtube-channel-manager",
          label: "제작 가이드",
          desc: "촬영 구성·B-roll·자막 포인트·썸네일 방향을 채널 매니저에게 넘긴다."
        },
        {
          from: "youtube-channel-manager",
          to: "team",
          label: "성과 개선 지시",
          desc: "업로드 후 CTR·평균 시청 지속·이탈 구간을 분석해, 개선 1-3개를 기획자·작가·제작자에게 피드백한다. (다음 사이클로 순환)"
        }
      ],
      downloadUrl: "./downloads/youtube-content-pd-team.zip"
    }
  ]
};
