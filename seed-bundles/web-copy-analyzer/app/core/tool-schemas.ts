/**
 * MCP tool JSON Schemas — verbatim mirror of design.md §2-3 (12 tools total:
 * core 7 + persona management 3 + growth 2). Exported as plain data so:
 *   - a later MCP adapter phase can register these directly with no
 *     duplication/drift risk, and
 *   - a custom-agent author can import the core package directly (without
 *     MCP) and still get the tool-definition contracts (design.md §산출물
 *     3층 ②, "코어 패키지의 프로그래머블 export").
 *
 * NOTE: `define_persona` is intentionally NOT an MCP tool (§2-3 주석) — persona
 * synthesis is a host-LLM judgment call; only save_persona is exposed, and it
 * calls the pure core function `definePersona` internally for validation.
 *
 * These are read-only literal JSON Schema objects — no runtime logic lives
 * here. Functions that implement the schemas' semantics (savePersona,
 * listPersonas, getPersona, deletePersona, remember, saveWorkflow) are
 * growth-layer adapter work for a later phase (see persona.ts header
 * comment); this phase implements and enforces (via constants.ts) the input
 * caps for the tools it DOES implement (parse_sections, readability_scorecard,
 * diagnose_section, rewrite_section, compare_report, fetch_page).
 */

export interface ToolDefinition {
  name: string;
  inputSchema: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
}

export const SAVE_PERSONA_TOOL: ToolDefinition = {
  name: "save_persona",
  inputSchema: {
    type: "object",
    required: ["name", "attributes"],
    properties: {
      name: { type: "string", maxLength: 80 },
      attributes: {
        type: "object",
        required: ["role", "pains", "vocabulary"],
        properties: {
          role: { type: "string" },
          goals: { type: "array", items: { type: "string" } },
          pains: { type: "array", items: { type: "string" } },
          vocabulary: { type: "array", items: { type: "string" } },
          buying_triggers: { type: "array", items: { type: "string" } },
        },
      },
      overwrite: { type: "boolean", default: false },
    },
    additionalProperties: false,
  },
};

export const LIST_PERSONAS_TOOL: ToolDefinition = {
  name: "list_personas",
  inputSchema: { type: "object", properties: {}, additionalProperties: false },
};

export const GET_PERSONA_TOOL: ToolDefinition = {
  name: "get_persona",
  inputSchema: {
    type: "object",
    required: ["id"],
    properties: { id: { type: "string", maxLength: 80 } },
    additionalProperties: false,
  },
};

export const DELETE_PERSONA_TOOL: ToolDefinition = {
  name: "delete_persona",
  inputSchema: {
    type: "object",
    required: ["id"],
    properties: { id: { type: "string", maxLength: 80 } },
    additionalProperties: false,
  },
};

export const FETCH_PAGE_TOOL: ToolDefinition = {
  name: "fetch_page",
  inputSchema: {
    type: "object",
    required: ["url"],
    properties: {
      url: { type: "string", format: "uri", pattern: "^https?://" },
      timeout_ms: { type: "integer", minimum: 1000, maximum: 30000, default: 10000 },
      max_bytes: { type: "integer", maximum: 5000000, default: 5000000 },
      allow_local: { type: "boolean", default: false },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      ok: { type: "boolean" },
      status: { type: "integer" },
      final_url: { type: "string" },
      content_type: { type: "string" },
      bytes: { type: "integer" },
      html: { type: "string" },
      error: { type: "string" },
      error_kind: { enum: ["not_found", "timeout", "blocked", "too_large", "non_html", "network", "ok"] },
    },
  },
};

export const PARSE_SECTIONS_TOOL: ToolDefinition = {
  name: "parse_sections",
  inputSchema: {
    type: "object",
    required: ["html"],
    properties: {
      html: { type: "string" },
      base_url: { type: "string" },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      sections: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: { type: "string" },
            role: { enum: ["hero", "headline", "subhead", "cta", "proof", "feature", "faq", "footer", "other"] },
            text: { type: "string" },
            dom_index: { type: "integer" },
            above_fold_estimate: { type: "boolean" },
          },
        },
      },
      parse_quality: { enum: ["rich", "sparse", "empty"] },
      truncated: { type: "boolean" },
    },
  },
};

export const READABILITY_SCORECARD_TOOL: ToolDefinition = {
  name: "readability_scorecard",
  inputSchema: {
    type: "object",
    required: ["parsed_page"],
    properties: { parsed_page: { type: "object" } },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      language: { type: "string" },
      english_dependent_metrics_applicable: { type: "boolean" },
      readability: {
        type: "object",
        properties: { grade_level: { type: "number" }, avg_sentence_len: { type: "number" } },
      },
      structure_checklist: {
        type: "array",
        items: { type: "object", properties: { item: { type: "string" }, pass: { type: "boolean" } } },
      },
      cta_inventory: {
        type: "array",
        items: { type: "object", properties: { text: { type: "string" }, dom_index: { type: "integer" } } },
      },
      headline_length: { type: "object", properties: { chars: { type: "integer" }, words: { type: "integer" } } },
      we_you_ratio: {
        type: "object",
        properties: { we: { type: "integer" }, you: { type: "integer" }, ratio: { type: "number" } },
      },
      jargon_density: {
        type: "object",
        properties: { jargon_terms: { type: "integer" }, per_100_words: { type: "number" } },
      },
    },
  },
};

export const DIAGNOSE_SECTION_TOOL: ToolDefinition = {
  name: "diagnose_section",
  inputSchema: {
    type: "object",
    required: ["parsed_page", "persona_id"],
    properties: {
      parsed_page: { type: "object" },
      section_id: { type: "string", maxLength: 40 },
      persona_id: { type: "string", maxLength: 80 },
      scope: { enum: ["section", "above_fold"], default: "section" },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      brief_kind: { const: "diagnosis" },
      section: { type: "object" },
      persona: { type: "object" },
      deterministic_signals: { type: "object" },
      attribution_frame: { type: "array", items: { enum: ["clarity", "trust", "relevance", "cta"] } },
      instructions_hint: { type: "string" },
    },
  },
};

export const REWRITE_SECTION_TOOL: ToolDefinition = {
  name: "rewrite_section",
  inputSchema: {
    type: "object",
    required: ["parsed_page", "section_id", "persona_id"],
    properties: {
      parsed_page: { type: "object" },
      section_id: { type: "string", maxLength: 40 },
      persona_id: { type: "string", maxLength: 80 },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      brief_kind: { const: "rewrite" },
      section: { type: "object" },
      persona_voice: { type: "object" },
      preservation_constraints: {
        type: "array",
        items: {
          type: "object",
          properties: { kind: { enum: ["testimonial", "proof", "stat", "quote"] }, text: { type: "string" } },
        },
      },
      instructions_hint: { type: "string" },
    },
  },
};

export const COMPARE_REPORT_TOOL: ToolDefinition = {
  name: "compare_report",
  inputSchema: {
    type: "object",
    required: ["before", "after"],
    properties: {
      before: { type: "object" },
      after: {
        type: "array",
        maxItems: 50,
        items: {
          type: "object",
          required: ["section_id", "rewritten_text"],
          properties: {
            section_id: { type: "string", maxLength: 40 },
            rewritten_text: { type: "string", maxLength: 20000 },
            rationale: { type: "string", maxLength: 2000 },
          },
          additionalProperties: false,
        },
      },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      diff: { type: "array" },
      preservation: { type: "object", properties: { ok: { type: "boolean" }, missing: { type: "array" } } },
      rationale_table: { type: "array" },
    },
  },
};

export const REMEMBER_TOOL: ToolDefinition = {
  name: "remember",
  inputSchema: {
    type: "object",
    required: ["kind", "content"],
    properties: {
      kind: { enum: ["persona_pref", "brand_voice", "forbidden_phrase", "decision"] },
      content: { type: "string", maxLength: 2000 },
      context: { type: "string", maxLength: 2000 },
    },
    additionalProperties: false,
  },
};

export const SAVE_WORKFLOW_TOOL: ToolDefinition = {
  name: "save_workflow",
  inputSchema: {
    type: "object",
    required: ["name", "steps"],
    properties: {
      name: { type: "string", maxLength: 80 },
      steps: { type: "array", maxItems: 50, items: { type: "string", maxLength: 500 } },
    },
    additionalProperties: false,
  },
};

// ---------------------------------------------------------------------------
// knowledge graph tools (search_knowledge / knowledge_neighbors / learn_knowledge)
//
// Beyond design.md §2-3's canonical 12 — a separate, additive set so
// ALL_TOOL_DEFINITIONS stays the verified §2-3 contract. Same strict-schema
// discipline (additionalProperties:false + size caps consistent with the
// other tools). See KNOWLEDGE_TOOL_DEFINITIONS below and mcp/tools.ts.
// ---------------------------------------------------------------------------

export const SEARCH_KNOWLEDGE_TOOL: ToolDefinition = {
  name: "search_knowledge",
  inputSchema: {
    type: "object",
    required: ["query"],
    properties: {
      query: { type: "string", maxLength: 200 },
      max_results: { type: "integer", minimum: 1, maximum: 50, default: 10 },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      results: {
        type: "array",
        items: {
          type: "object",
          properties: {
            id: { type: "string" },
            title: { type: "string" },
            tags: { type: "array", items: { type: "string" } },
            source: { enum: ["seed", "learned"] },
            snippet: { type: "string" },
          },
        },
      },
    },
  },
};

export const KNOWLEDGE_NEIGHBORS_TOOL: ToolDefinition = {
  name: "knowledge_neighbors",
  inputSchema: {
    type: "object",
    required: ["node_id"],
    properties: {
      node_id: { type: "string", maxLength: 120 },
      depth: { type: "integer", minimum: 1, maximum: 3, default: 1 },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      node: { type: "object" },
      neighbors: { type: "array" },
      edges: {
        type: "array",
        items: { type: "object", properties: { from: { type: "string" }, to: { type: "string" } } },
      },
    },
  },
};

export const LEARN_KNOWLEDGE_TOOL: ToolDefinition = {
  name: "learn_knowledge",
  inputSchema: {
    type: "object",
    required: ["title", "body"],
    properties: {
      title: { type: "string", maxLength: 200 },
      body: { type: "string", maxLength: 20000 },
      tags: { type: "array", maxItems: 20, items: { type: "string", maxLength: 60 } },
      links: { type: "array", maxItems: 30, items: { type: "string", maxLength: 120 } },
      evidence: { type: "array", maxItems: 20, items: { type: "string", maxLength: 500 } },
    },
    additionalProperties: false,
  },
  outputSchema: {
    type: "object",
    properties: {
      learned: { type: "boolean" },
      id: { type: "string" },
      path: { type: "string" },
      shown: { type: "string" },
      rejected: { type: "boolean" },
      reason: { type: "string" },
    },
  },
};

/** The 3 additive knowledge-graph tools (not part of design.md §2-3's 12). */
export const KNOWLEDGE_TOOL_DEFINITIONS: readonly ToolDefinition[] = [
  SEARCH_KNOWLEDGE_TOOL,
  KNOWLEDGE_NEIGHBORS_TOOL,
  LEARN_KNOWLEDGE_TOOL,
];

/** All 12 MCP tool definitions (design.md §2-3), in the same order as the design doc. */
export const ALL_TOOL_DEFINITIONS: readonly ToolDefinition[] = [
  SAVE_PERSONA_TOOL,
  LIST_PERSONAS_TOOL,
  GET_PERSONA_TOOL,
  DELETE_PERSONA_TOOL,
  FETCH_PAGE_TOOL,
  PARSE_SECTIONS_TOOL,
  READABILITY_SCORECARD_TOOL,
  DIAGNOSE_SECTION_TOOL,
  REWRITE_SECTION_TOOL,
  COMPARE_REPORT_TOOL,
  REMEMBER_TOOL,
  SAVE_WORKFLOW_TOOL,
];
