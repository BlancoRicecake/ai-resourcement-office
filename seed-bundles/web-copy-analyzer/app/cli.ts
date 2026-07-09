#!/usr/bin/env node
/**
 * Plain CLI wrapper over the 12 web-copy-analyzer tools (worker/mcp/tools.ts)
 * — the universal invocation path for coding agents that don't speak MCP
 * (Codex/Manus/etc). No new business logic: each subcommand looks up the
 * matching ToolHandler and calls handler.execute(wireArgs, { growth }),
 * exactly mirroring MCP tool-call semantics (same input/output JSON shape,
 * same GrowthStore-backed persona/memory persistence at ~/.web-copy-analyzer/).
 *
 * Usage: node cli.js <command> ['<json-wire-args>']
 *        node cli.js persona <save|list|get|delete> ['<json-wire-args>']
 * Prints the JSON result to stdout; errors print {"error": "..."} to stderr
 * and exit 1.
 */
import { ALL_TOOL_HANDLERS, KNOWLEDGE_TOOL_HANDLERS, type ToolHandler } from "./mcp/tools.js";
import { GrowthStore, KnowledgeStore } from "./growth/index.js";

const COMMAND_TO_TOOL: Record<string, string> = {
  "fetch-page": "fetch_page",
  "parse-sections": "parse_sections",
  "readability-scorecard": "readability_scorecard",
  "diagnose-section": "diagnose_section",
  "rewrite-section": "rewrite_section",
  "compare-report": "compare_report",
  remember: "remember",
  "save-workflow": "save_workflow",
  "search-knowledge": "search_knowledge",
  "knowledge-neighbors": "knowledge_neighbors",
  "learn-knowledge": "learn_knowledge",
};

const PERSONA_SUBCOMMAND_TO_TOOL: Record<string, string> = {
  save: "save_persona",
  list: "list_personas",
  get: "get_persona",
  delete: "delete_persona",
};

function usage(): never {
  const commands = [...Object.keys(COMMAND_TO_TOOL), "persona save|list|get|delete"].join(", ");
  console.error(`usage: web-copy-analyzer-cli <command> ['<json-wire-args>']\ncommands: ${commands}`);
  process.exit(1);
}

function findHandler(toolName: string): ToolHandler {
  const handler = [...ALL_TOOL_HANDLERS, ...KNOWLEDGE_TOOL_HANDLERS].find((h) => h.definition.name === toolName);
  if (!handler) throw new Error(`no tool handler for '${toolName}' (worker/mcp/tools.ts drifted)`);
  return handler;
}

function parseJsonArg(raw: string | undefined): Record<string, unknown> {
  if (raw === undefined || raw.trim() === "") return {};
  try {
    return JSON.parse(raw) as Record<string, unknown>;
  } catch (err) {
    throw new Error(`invalid JSON args: ${(err as Error).message}`);
  }
}

async function main(): Promise<void> {
  const [command, ...rest] = process.argv.slice(2);
  if (!command) usage();

  let toolName: string;
  let jsonArg: string | undefined;

  if (command === "persona") {
    const [sub, arg] = rest;
    const mappedSub = sub ? PERSONA_SUBCOMMAND_TO_TOOL[sub] : undefined;
    if (!mappedSub) usage();
    toolName = mappedSub;
    jsonArg = arg;
  } else {
    const mapped = COMMAND_TO_TOOL[command];
    if (!mapped) usage();
    toolName = mapped;
    jsonArg = rest[0];
  }

  const wireArgs = parseJsonArg(jsonArg);
  const handler = findHandler(toolName);
  const growth = new GrowthStore();
  const knowledge = new KnowledgeStore();
  const result = await handler.execute(wireArgs, { growth, knowledge });
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

main().catch((err) => {
  process.stderr.write(`${JSON.stringify({ error: (err as Error).message })}\n`);
  process.exitCode = 1;
});
