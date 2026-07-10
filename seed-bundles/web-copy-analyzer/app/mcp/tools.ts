/**
 * The 6 deterministic MCP tool handlers — thin wiring only (no business logic
 * here that doesn't already live in core/). Each handler: (1) applies schema
 * defaults + validates the wire-format input, (2) translates snake_case wire
 * args into the camelCase shape the core function expects, (3) calls that
 * function, (4) translates the result back to snake_case for the wire
 * response.
 *
 * There is NO growth/persona store: diagnose_section / rewrite_section take a
 * persona object inline and normalize it with the pure core `definePersona`.
 */

import {
  ALL_TOOL_DEFINITIONS,
  buildDiagnosisContext,
  buildRewriteContext,
  compareReport,
  definePersona,
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
  PersonaDraft,
  RewriteContextInput,
  Section,
} from "../core/types.js";
import { applyDefaults, validateToolInput } from "./validate.js";
import { toCamelDeep, toSnakeDeep } from "./wire.js";

export interface ToolHandler {
  definition: ToolDefinition;
  execute(wireArgs: Record<string, unknown>): Promise<unknown>;
}

/** Wire persona input (examples/input/persona.json shape). */
interface PersonaWireInput {
  name: string;
  attributes: {
    role: string;
    goals?: string[];
    pains: string[];
    vocabulary: string[];
    buying_triggers?: string[];
  };
}

function byName(name: string): ToolDefinition {
  const def = ALL_TOOL_DEFINITIONS.find((d) => d.name === name);
  if (!def) throw new Error(`no tool definition for '${name}' (core/tool-schemas.ts drifted from mcp/tools.ts)`);
  return def;
}

function prepareInput(def: ToolDefinition, rawArgs: unknown): Record<string, unknown> {
  const withDefaults = applyDefaults(def.inputSchema, rawArgs ?? {});
  validateToolInput(def.inputSchema, withDefaults);
  return withDefaults as Record<string, unknown>;
}

/** Normalize an explicit persona wire object into a validated core Persona. */
function resolvePersona(input: PersonaWireInput): Persona {
  const draft: PersonaDraft = {
    name: input.name,
    role: input.attributes.role,
    goals: input.attributes.goals,
    pains: input.attributes.pains,
    vocabulary: input.attributes.vocabulary,
    buyingTriggers: input.attributes.buying_triggers,
  };
  return definePersona(draft);
}

// ---------------------------------------------------------------------------
// deterministic analysis tools
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

const diagnoseSectionTool: ToolHandler = {
  definition: byName("diagnose_section"),
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs) as {
      parsed_page: unknown;
      section_id?: string;
      persona: PersonaWireInput;
      scope?: "section" | "above_fold";
    };
    const persona = resolvePersona(args.persona);
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
  async execute(wireArgs) {
    const args = prepareInput(this.definition, wireArgs) as {
      parsed_page: unknown;
      section_id: string;
      persona: PersonaWireInput;
    };
    const persona = resolvePersona(args.persona);
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

/** All 6 deterministic tools, in the same order as core/tool-schemas.ts ALL_TOOL_DEFINITIONS. */
export const ALL_TOOL_HANDLERS: readonly ToolHandler[] = [
  fetchPageTool,
  parseSectionsTool,
  readabilityScorecardTool,
  diagnoseSectionTool,
  rewriteSectionTool,
  compareReportTool,
];

export type { Section };
