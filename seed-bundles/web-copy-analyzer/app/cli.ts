#!/usr/bin/env node
/**
 * Plain CLI wrapper over the 6 deterministic web-copy-analyzer tools
 * (mcp/tools.ts) — the universal invocation path for coding agents that don't
 * speak MCP (Codex/Manus/etc). No new business logic: each subcommand looks up
 * the matching ToolHandler and calls handler.execute(wireArgs), exactly
 * mirroring MCP tool-call semantics (same input/output JSON shape). Persona is
 * passed inline to diagnose-section / rewrite-section — there is no persona
 * store.
 *
 * Usage: node cli.js <command> ['<json-wire-args>']
 * Prints the JSON result to stdout; errors print {"error": "..."} to stderr
 * and exit 1.
 */
import { ALL_TOOL_HANDLERS, type ToolHandler } from "./mcp/tools.js";

const COMMAND_TO_TOOL: Record<string, string> = {
  "fetch-page": "fetch_page",
  "parse-sections": "parse_sections",
  "readability-scorecard": "readability_scorecard",
  "diagnose-section": "diagnose_section",
  "rewrite-section": "rewrite_section",
  "compare-report": "compare_report",
};

function usage(): never {
  const commands = Object.keys(COMMAND_TO_TOOL).join(", ");
  console.error(`usage: web-copy-analyzer-cli <command> ['<json-wire-args>']\ncommands: ${commands}`);
  process.exit(1);
}

function findHandler(toolName: string): ToolHandler {
  const handler = ALL_TOOL_HANDLERS.find((h) => h.definition.name === toolName);
  if (!handler) throw new Error(`no tool handler for '${toolName}' (mcp/tools.ts drifted)`);
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

  const toolName = COMMAND_TO_TOOL[command];
  if (!toolName) usage();

  const wireArgs = parseJsonArg(rest[0]);
  const handler = findHandler(toolName);
  const result = await handler.execute(wireArgs);
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

main().catch((err) => {
  process.stderr.write(`${JSON.stringify({ error: (err as Error).message })}\n`);
  process.exitCode = 1;
});
