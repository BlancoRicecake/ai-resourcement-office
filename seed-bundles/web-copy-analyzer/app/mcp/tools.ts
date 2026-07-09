/**
 * The 12 MCP tool handlers (design.md §2-3) — thin wiring only (둘째 원칙: no
 * new business logic here that doesn't already live in core/ or growth/).
 * Each handler: (1) applies schema defaults + validates the wire-format
 * input, (2) translates snake_case wire args into the camelCase shape the
 * core/growth function expects, (3) calls that function, (4) translates the
 * result back to snake_case for the wire response.
 */

import {
  ALL_TOOL_DEFINITIONS,
  KNOWLEDGE_TOOL_DEFINITIONS,
  buildDiagnosisContext,
  buildRewriteContext,
  compareReport,
  parseSections,
  readabilityScorecard,
  type ToolDefinition,
} from "../core/index.js";
import { fetchPage } from "../core/fetch-node.js";
import type {
  CompareReportInput,
  DiagnosisContextInput,
  ParseSectionsInput,
  ParsedPage,
  Persona,
  RewriteContextInput,
  Section,
} from "../core/types.js";
import type { GrowthStore, KnowledgeStore } from "../growth/index.js";
import { applyDefaults, validateToolInput } from "./validate.js";
import { toCamelDeep, toSnakeDeep } from "./wire.js";

export interface ToolContext {
  growth: GrowthStore;
  knowledge: KnowledgeStore;
}

export interface ToolHandler {
  definition: ToolDefinition;
  execute(wireArgs: Record<string, unknown>, ctx: ToolContext): Promise<unknown>;
}

function byName(name: string): ToolDefinition {
  const def = [...ALL_TOOL_DEFINITIONS, ...KNOWLEDGE_TOOL_DEFINITIONS].find((d) => d.name === name);
  if (!def) throw new Error(`no tool definition for '${name}' (core/tool-schemas.ts drifted from mcp/tools.ts)`);
  return def;
}

function prepareInput(def: ToolDefinition, rawArgs: unknown): Record<string, unknown> {
  const withDefaults = applyDefaults(def.inputSchema, rawArgs ?? {});
  validateToolInput(def.inputSchema, withDefaults);
  return withDefaults as Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// persona management (growth-layer)
// ---------------------------------------------------------------------------

const savePersonaTool: ToolHandler = {
  definition: byName("save_persona"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as {
      name: string;
      attributes: { role: string; goals?: string[]; pains: string[]; vocabulary: string[]; buying_triggers?: string[] };
      overwrite?: boolean;
    };
    const result = await ctx.growth.savePersona({
      draft: {
        name: args.name,
        role: args.attributes.role,
        goals: args.attributes.goals,
        pains: args.attributes.pains,
        vocabulary: args.attributes.vocabulary,
        buyingTriggers: args.attributes.buying_triggers,
      },
      overwrite: args.overwrite,
    });
    return toSnakeDeep(result);
  },
};

const listPersonasTool: ToolHandler = {
  definition: byName("list_personas"),
  async execute(_wireArgs, ctx) {
    const personas = await ctx.growth.listPersonas();
    return toSnakeDeep({ personas });
  },
};

const getPersonaTool: ToolHandler = {
  definition: byName("get_persona"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { id: string };
    const persona = await ctx.growth.getPersona(args.id);
    return toSnakeDeep(persona);
  },
};

const deletePersonaTool: ToolHandler = {
  definition: byName("delete_persona"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { id: string };
    const result = await ctx.growth.deletePersona(args.id);
    return toSnakeDeep(result);
  },
};

// ---------------------------------------------------------------------------
// core prep/deterministic tools
// ---------------------------------------------------------------------------

const fetchPageTool: ToolHandler = {
  definition: byName("fetch_page"),
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs);
    const options = toCamelDeep<{ url: string; timeoutMs?: number; maxBytes?: number; allowLocal?: boolean }>(args);
    const result = await fetchPage(options);
    return toSnakeDeep(result);
  },
};

const parseSectionsTool: ToolHandler = {
  definition: byName("parse_sections"),
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs);
    const input = toCamelDeep<ParseSectionsInput>(args);
    const result = parseSections(input);
    return toSnakeDeep(result);
  },
};

const readabilityScorecardTool: ToolHandler = {
  definition: byName("readability_scorecard"),
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs) as { parsed_page: unknown };
    const parsedPage = toCamelDeep<ParsedPage>(args.parsed_page);
    const result = readabilityScorecard(parsedPage);
    return toSnakeDeep(result);
  },
};

async function resolvePersona(ctx: ToolContext, personaId: string): Promise<Persona> {
  // 문제표 #8/#9 are surfaced as PersonaNotFoundError/PersonaCorruptError,
  // which the server's tools/call handler turns into an MCP tool error
  // result carrying the exact user-facing message from growth/types.ts.
  return ctx.growth.getPersona(personaId);
}

const diagnoseSectionTool: ToolHandler = {
  definition: byName("diagnose_section"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as {
      parsed_page: unknown;
      section_id?: string;
      persona_id: string;
      scope?: "section" | "above_fold";
    };
    const persona = await resolvePersona(ctx, args.persona_id);
    const input: DiagnosisContextInput = {
      parsedPage: toCamelDeep<ParsedPage>(args.parsed_page),
      sectionId: args.section_id,
      persona,
      scope: args.scope,
    };
    const brief = buildDiagnosisContext(input);
    return toSnakeDeep(brief);
  },
};

const rewriteSectionTool: ToolHandler = {
  definition: byName("rewrite_section"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { parsed_page: unknown; section_id: string; persona_id: string };
    const persona = await resolvePersona(ctx, args.persona_id);
    const input: RewriteContextInput = {
      parsedPage: toCamelDeep<ParsedPage>(args.parsed_page),
      sectionId: args.section_id,
      persona,
    };
    const brief = buildRewriteContext(input);
    return toSnakeDeep(brief);
  },
};

const compareReportTool: ToolHandler = {
  definition: byName("compare_report"),
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs) as {
      before: unknown;
      after: Array<{ section_id: string; rewritten_text: string; rationale?: string }>;
    };
    const input: CompareReportInput = {
      before: toCamelDeep<ParsedPage>(args.before),
      after: args.after.map((a) => toCamelDeep<{ sectionId: string; rewrittenText: string; rationale?: string }>(a)),
    };
    const result = compareReport(input);
    return toSnakeDeep(result);
  },
};

// ---------------------------------------------------------------------------
// growth tools
// ---------------------------------------------------------------------------

const rememberTool: ToolHandler = {
  definition: byName("remember"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { kind: string; content: string; context?: string };
    const result = await ctx.growth.remember({ kind: args.kind as never, content: args.content, context: args.context });
    return toSnakeDeep(result);
  },
};

const saveWorkflowTool: ToolHandler = {
  definition: byName("save_workflow"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { name: string; steps: string[] };
    const result = await ctx.growth.saveWorkflow({ name: args.name, steps: args.steps });
    return toSnakeDeep(result);
  },
};

// ---------------------------------------------------------------------------
// knowledge graph tools (search_knowledge / knowledge_neighbors / learn_knowledge)
// ---------------------------------------------------------------------------

const searchKnowledgeTool: ToolHandler = {
  definition: byName("search_knowledge"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { query: string; max_results?: number };
    const results = await ctx.knowledge.searchKnowledge(args.query, args.max_results);
    return toSnakeDeep({ results });
  },
};

const knowledgeNeighborsTool: ToolHandler = {
  definition: byName("knowledge_neighbors"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as { node_id: string; depth?: number };
    const result = await ctx.knowledge.knowledgeNeighbors(args.node_id, args.depth);
    return toSnakeDeep(result);
  },
};

const learnKnowledgeTool: ToolHandler = {
  definition: byName("learn_knowledge"),
  async execute(wireArgs, ctx) {
    const args = prepareInput(this.definition, wireArgs) as {
      title: string;
      body: string;
      tags?: string[];
      links?: string[];
      evidence?: string[];
    };
    const result = await ctx.knowledge.learnKnowledge({
      title: args.title,
      body: args.body,
      tags: args.tags,
      links: args.links,
      evidence: args.evidence,
    });
    return toSnakeDeep(result);
  },
};

/** The 3 additive knowledge-graph handlers (beyond design.md §2-3's 12). */
export const KNOWLEDGE_TOOL_HANDLERS: readonly ToolHandler[] = [
  searchKnowledgeTool,
  knowledgeNeighborsTool,
  learnKnowledgeTool,
];

/** All 12 tools, in the same order as design.md §2-3 / core/tool-schemas.ts ALL_TOOL_DEFINITIONS. */
export const ALL_TOOL_HANDLERS: readonly ToolHandler[] = [
  savePersonaTool,
  listPersonasTool,
  getPersonaTool,
  deletePersonaTool,
  fetchPageTool,
  parseSectionsTool,
  readabilityScorecardTool,
  diagnoseSectionTool,
  rewriteSectionTool,
  compareReportTool,
  rememberTool,
  saveWorkflowTool,
];

export type { Section };
