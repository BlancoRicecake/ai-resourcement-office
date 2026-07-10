/**
 * MCP stdio server: exposes the 6 deterministic analysis tools, emits the
 * bundled worker/agent.md as the `instructions` (initialize response), and
 * loads custom-tools/.
 *
 * This module is transport-agnostic (createServer returns an unconnected
 * Server so tests can wire it to an InMemoryTransport); mcp/bin.ts is the
 * actual stdio process entrypoint.
 *
 * There is no growth/persona store and no persona://merged resource: persona
 * is an explicit tool input, and self-learning lives in the bundle's memory/
 * files (read by the host agent), not in a runtime store.
 */

import { fileURLToPath } from "node:url";
import * as path from "node:path";
import { existsSync } from "node:fs";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { ALL_TOOL_HANDLERS, type ToolHandler } from "./tools.js";
import { loadCustomTools } from "./custom-tools.js";
import { loadAgentsMd } from "./instructions.js";

const MODULE_DIR = path.dirname(fileURLToPath(import.meta.url));

/**
 * Resolves worker/agent.md relative to this module's own location. Two
 * layouts must both work:
 *  - running from source: this file is app/mcp/server.ts, so agent.md is at
 *    ../../worker/agent.md (app/mcp -> app -> bundle root -> worker/agent.md).
 *  - running from the esbuild single-file bundle: app/scripts/build.mjs
 *    copies worker/agent.md next to the bundled app/dist/mcp.js (same
 *    directory, since the bundle flattens app/mcp/server.ts into
 *    app/dist/mcp.js).
 * Prefer the bundled same-directory copy when present, else fall back to the
 * source-tree relative path.
 */
export function defaultAgentsMdPath(): string {
  const bundled = path.join(MODULE_DIR, "agent.md");
  if (existsSync(bundled)) return bundled;
  return path.join(MODULE_DIR, "..", "..", "worker", "agent.md");
}

/** custom-tools/ is a per-deployment, user-editable folder — resolved relative to the invoking process's cwd, not this package's install location. */
export function defaultCustomToolsDir(): string {
  return path.join(process.cwd(), "custom-tools");
}

export interface CreateServerOptions {
  agentsMdPath?: string;
  customToolsDir?: string;
  /** Injected for deterministic tests; defaults to console.error (MCP stdio reserves stdout for protocol messages). */
  log?: (message: string) => void;
}

export interface CreatedServer {
  server: Server;
  handlers: readonly ToolHandler[];
  loadedCustomToolNames: string[];
  customToolFailures: string[];
  instructionsText: string;
  agentsMdPath: string;
}

export async function createServer(opts: CreateServerOptions = {}): Promise<CreatedServer> {
  const log = opts.log ?? ((msg: string) => console.error(msg));
  const agentsMdPath = opts.agentsMdPath ?? defaultAgentsMdPath();
  const customToolsDir = opts.customToolsDir ?? defaultCustomToolsDir();

  const instructionsText = await loadAgentsMd(agentsMdPath);

  const { loaded: customHandlers, failures } = await loadCustomTools(customToolsDir);
  for (const failure of failures) log(failure);
  log(
    customHandlers.length > 0
      ? `custom-tools 로드됨: ${customHandlers.map((h) => h.definition.name).join(", ")}`
      : "custom-tools 로드됨: 없음"
  );

  const handlers: ToolHandler[] = [...ALL_TOOL_HANDLERS, ...customHandlers];
  const handlerByName = new Map(handlers.map((h) => [h.definition.name, h] as const));

  const server = new Server(
    { name: "web-copy-analyzer", version: "2.0.0" },
    { capabilities: { tools: {} }, instructions: instructionsText }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: handlers.map((h) => ({
      name: h.definition.name,
      description: `${h.definition.name} (web-copy-analyzer)`,
      inputSchema: h.definition.inputSchema,
    })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const handler = handlerByName.get(request.params.name);
    if (!handler) {
      return { content: [{ type: "text", text: `unknown tool: ${request.params.name}` }], isError: true };
    }
    try {
      const result = await handler.execute((request.params.arguments ?? {}) as Record<string, unknown>);
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    } catch (err) {
      return { content: [{ type: "text", text: (err as Error).message }], isError: true };
    }
  });

  return {
    server,
    handlers,
    loadedCustomToolNames: customHandlers.map((h) => h.definition.name),
    customToolFailures: failures,
    instructionsText,
    agentsMdPath,
  };
}
