/**
 * MCP tool JSON Schemas — the 6 deterministic analysis tools. Exported as
 * plain data so:
 *   - the MCP adapter (mcp/tools.ts) registers these directly with no
 *     duplication/drift risk, and
 *   - a custom-agent author can import the core package directly (without
 *     MCP) and still get the tool-definition contracts.
 *
 * These are read-only literal JSON Schema objects — no runtime logic lives
 * here. All 6 tools are deterministic and call NO LLM: fetch_page (network),
 * parse_sections / readability_scorecard (pure analysis), diagnose_section /
 * rewrite_section (assemble a judgment payload for the host LLM), and
 * compare_report (deterministic before/after + preservation check).
 *
 * Persona is an EXPLICIT INPUT (no persona store): diagnose_section and
 * rewrite_section take a `persona` object inline (same wire shape the user
 * writes in examples/input/persona.json — `{ name, attributes }`). The bundle
 * carries no growth/persona-store runtime; the host agent selects or
 * interviews a persona from `memory/PERSONAS.md` and passes it here.
 */

export interface ToolDefinition {
  name: string;
  inputSchema: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
}

/**
 * Explicit persona input for diagnose_section / rewrite_section. Same wire
 * shape as examples/input/persona.json: `{ name, attributes: { role, goals?,
 * pains, vocabulary, buying_triggers? } }`. The handler normalizes this into
 * a core Persona via definePersona (pure validation), so no persona_id lookup
 * / file read is involved.
 */
export const PERSONA_INPUT_SCHEMA: Record<string, unknown> = {
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
  },
  additionalProperties: false,
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
    required: ["parsed_page", "persona"],
    properties: {
      parsed_page: { type: "object" },
      section_id: { type: "string", maxLength: 40 },
      persona: PERSONA_INPUT_SCHEMA,
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
    required: ["parsed_page", "section_id", "persona"],
    properties: {
      parsed_page: { type: "object" },
      section_id: { type: "string", maxLength: 40 },
      persona: PERSONA_INPUT_SCHEMA,
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

/** The 6 deterministic MCP tool definitions (the canonical tool set). */
export const ALL_TOOL_DEFINITIONS: readonly ToolDefinition[] = [
  FETCH_PAGE_TOOL,
  PARSE_SECTIONS_TOOL,
  READABILITY_SCORECARD_TOOL,
  DIAGNOSE_SECTION_TOOL,
  REWRITE_SECTION_TOOL,
  COMPARE_REPORT_TOOL,
];
