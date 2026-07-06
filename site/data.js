window.AIRO_DATA = {
  workers: [
    {
      name: "리뷰 분석 직원",
      slug: "review-analysis-worker",
      category: "고객분석",
      summary:
        "CSV 고객 리뷰를 읽고 감성 분류, 주요 불만, 개선 요청, 요약 리포트를 만든다.",
      skills: ["CSV 분석", "감성 분류", "리포트 작성"],
      tools: ["OpenAI API", "Local file"],
      output: "리뷰 인사이트 리포트"
    },
    {
      name: "SEO/GEO 브리프 직원",
      slug: "seo-geo-brief-worker",
      category: "마케팅",
      summary:
        "키워드와 제품 설명을 받아 검색과 AI 답변에 대응하는 콘텐츠 브리프를 만든다.",
      skills: ["콘텐츠 구조화", "FAQ 생성", "AEO/GEO 문장화"],
      tools: ["OpenAI API"],
      output: "콘텐츠 브리프"
    },
    {
      name: "제안서 초안 직원",
      slug: "proposal-draft-worker",
      category: "문서자동화",
      summary:
        "고객 요구사항, 서비스 범위, 일정 정보를 받아 B2B 제안서 초안을 만든다.",
      skills: ["요구사항 정리", "제안서 구성", "일정/견적 초안"],
      tools: ["OpenAI API", "Markdown"],
      output: "제안서 초안"
    }
  ],
  bundles: [
    {
      title: "CSV 리뷰 분석 리포트 생성기",
      slug: "csv-review-insight-generator",
      worker: "리뷰 분석 직원",
      category: "고객분석",
      difficulty: "초급",
      runtime: "로컬 실행 (Python 3.8+, pip 불필요)",
      requiredKeys: ["OPENAI_API_KEY (선택)"],
      estimatedCost: "$0 (mock 모드) / $0.01-$0.10 per run",
      includes: ["웹 UI + CLI", "무료 mock 모드", "agent.md", "skills", "sample CSV 20행", "실행 리포트 예시"],
      description:
        "고객 리뷰 CSV를 업로드하면 감성 분류와 핵심 이슈를 요약한 리포트를 생성하는 미니 SaaS. API 키 없이도 무료로 체험 가능.",
      downloadUrl: "../seed-bundles/csv-review-insight-generator/"
    },
    {
      title: "SEO/GEO 콘텐츠 브리프 생성기",
      slug: "seo-geo-content-brief-generator",
      worker: "SEO/GEO 브리프 직원",
      category: "마케팅",
      difficulty: "초급",
      runtime: "로컬 실행 (Python 3.8+, pip 불필요)",
      requiredKeys: ["OPENAI_API_KEY (선택)"],
      estimatedCost: "$0 (mock 모드) / $0.01-$0.08 per brief",
      includes: ["웹 UI + CLI", "무료 mock 모드", "agent.md", "skills", "브리프 예시"],
      description:
        "키워드와 제품 설명을 입력하면 제목 후보, 목차, FAQ, 메타 설명, AI 검색(GEO) 대응 문장을 생성하는 미니 SaaS.",
      downloadUrl: "../seed-bundles/seo-geo-content-brief-generator/"
    },
    {
      title: "고객 요구사항 기반 제안서 초안 생성기",
      slug: "proposal-draft-generator",
      worker: "제안서 초안 직원",
      category: "문서자동화",
      difficulty: "초급",
      runtime: "로컬 실행 (Python 3.8+, pip 불필요)",
      requiredKeys: ["OPENAI_API_KEY (선택)"],
      estimatedCost: "$0 (mock 모드) / $0.03-$0.20 per draft",
      includes: ["웹 UI + CLI", "무료 mock 모드", "agent.md", "skills", "제안서 초안 예시"],
      description:
        "고객 문제, 제공 서비스, 일정, 예산 정보를 받아 포함/제외 범위와 견적 항목까지 담은 제안서 초안을 만드는 미니 SaaS.",
      downloadUrl: "../seed-bundles/proposal-draft-generator/"
    }
  ]
};

