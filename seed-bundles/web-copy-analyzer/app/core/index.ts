/**
 * Programmable export surface for the web-copy-analyzer core (design.md
 * §산출물 3층 ②: "코어 패키지의 프로그래머블 export"). A custom-agent author
 * can `import { parseSections, readabilityScorecard, ... } from
 * "@ai-factory/web-copy-analyzer"` directly, with no MCP server involved.
 *
 * BROWSER-SAFE BARREL: this file must never import core/fetch-node.ts (Node
 * http/dns/net APIs). Node consumers that need fetchPage import it from the
 * separate `"@ai-factory/web-copy-analyzer/fetch-node"` subpath export.
 */

export * from "./types.js";

export { parseSections } from "./html-parser.js";
export { readabilityScorecard } from "./readability.js";
export { definePersona, PersonaValidationError } from "./persona.js";
export { buildDiagnosisContext, buildRewriteContext, checkPreservation, PrepContextError } from "./prep-context.js";
export { compareReport, CompareReportValidationError } from "./compare-report.js";

export {
  buildGraph,
  searchKnowledge,
  knowledgeNeighbors,
  extractWikilinks,
  parseKnowledgeNode,
  serializeKnowledgeNode,
  serializeGraphJson,
  deserializeGraphNodes,
  findDanglingEdges,
  findSelfLoops,
  KNOWLEDGE_GRAPH_JSON_VERSION,
  KnowledgeParseError,
  KnowledgeNodeNotFoundError,
} from "./knowledge.js";
export type {
  KnowledgeNode,
  KnowledgeEdge,
  KnowledgeGraph,
  KnowledgeSource,
  KnowledgeConfidence,
  KnowledgeNodeSummary,
  KnowledgeNeighbor,
  KnowledgeNeighborsResult,
  SerializedGraph,
  ParseNodeOptions,
} from "./knowledge.js";

export * as constants from "./constants.js";

export {
  ALL_TOOL_DEFINITIONS,
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
  KNOWLEDGE_TOOL_DEFINITIONS,
  SEARCH_KNOWLEDGE_TOOL,
  KNOWLEDGE_NEIGHBORS_TOOL,
  LEARN_KNOWLEDGE_TOOL,
} from "./tool-schemas.js";
export type { ToolDefinition } from "./tool-schemas.js";
