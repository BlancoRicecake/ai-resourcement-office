/**
 * MCP stdio server (design.md §산출물 3층 ②, implement-skill's three
 * requirements): exposes the 12 tools, emits the AGENTS.md+growth-layer
 * merged persona as both `instructions` (initialize response) and the
 * `persona://merged` resource, and loads custom-tools/.
 *
 * This module is transport-agnostic (createServer returns an unconnected
 * Server so tests can wire it to an InMemoryTransport); mcp/bin.ts is the
 * actual stdio process entrypoint.
 */

import { fileURLToPath } from "node:url";
import * as path from "node:path";
import { existsSync } from "node:fs";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { GrowthStore, KnowledgeStore } from "../growth/index.js";
import { ALL_TOOL_HANDLERS, KNOWLEDGE_TOOL_HANDLERS, type ToolHandler } from "./tools.js";
import { loadCustomTools } from "./custom-tools.js";
import { buildMergedInstructions, MERGED_PERSONA_RESOURCE_URI } from "./instructions.js";

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
  /** Growth-layer root override (tests only — production uses the ~/.web-copy-analyzer/ default). */
  rootDir?: string;
  agentsMdPath?: string;
  customToolsDir?: string;
  /** Injected for deterministic tests; defaults to console.error (MCP stdio reserves stdout for protocol messages). */
  log?: (message: string) => void;
}

export interface CreatedServer {
  server: Server;
  growth: GrowthStore;
  knowledge: KnowledgeStore;
  handlers: readonly ToolHandler[];
  loadedCustomToolNames: string[];
  customToolFailures: string[];
  instructionsText: string;
  agentsMdPath: string;
}

export async function createServer(opts: CreateServerOptions = {}): Promise<CreatedServer> {
  const log = opts.log ?? ((msg: string) => console.error(msg));
  const growth = new GrowthStore({ rootDir: opts.rootDir });
  const knowledge = new KnowledgeStore({ rootDir: opts.rootDir });
  const agentsMdPath = opts.agentsMdPath ?? defaultAgentsMdPath();
  const customToolsDir = opts.customToolsDir ?? defaultCustomToolsDir();

  const instructionsText = await buildMergedInstructions(agentsMdPath, growth);
  // 문제표 #20: surface any session-only degradation (e.g. an unreadable
  // voice.md at startup) on stderr — stdout is reserved for MCP protocol
  // messages, and this is the only channel available before a client connects.
  for (const warning of growth.getSessionOnlyWarnings()) log(warning);

  const { loaded: customHandlers, failures } = await loadCustomTools(customToolsDir);
  for (const failure of failures) log(failure); // 문제표 #15
  log(
    customHandlers.length > 0
      ? `custom-tools 로드됨: ${customHandlers.map((h) => h.definition.name).join(", ")}`
      : "custom-tools 로드됨: 없음"
  );

  const handlers: ToolHandler[] = [...ALL_TOOL_HANDLERS, ...KNOWLEDGE_TOOL_HANDLERS, ...customHandlers];
  const handlerByName = new Map(handlers.map((h) => [h.definition.name, h] as const));

  const server = new Server(
    { name: "web-copy-analyzer", version: "0.1.0" },
    { capabilities: { tools: {}, resources: {} }, instructions: instructionsText }
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
      const result = await handler.execute((request.params.arguments ?? {}) as Record<string, unknown>, { growth, knowledge });
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    } catch (err) {
      return { content: [{ type: "text", text: (err as Error).message }], isError: true };
    }
  });

  server.setRequestHandler(ListResourcesRequestSchema, async () => ({
    resources: [
      {
        uri: MERGED_PERSONA_RESOURCE_URI,
        name: "merged-persona",
        description: "AGENTS.md merged with the user growth layer (user-first, design.md §6-2)",
        mimeType: "text/markdown",
      },
    ],
  }));

  server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
    if (request.params.uri !== MERGED_PERSONA_RESOURCE_URI) {
      throw new Error(`unknown resource: ${request.params.uri}`);
    }
    // Rebuilt live (not the startup snapshot) so a resource read after a
    // remember()/save_persona() call in the same session reflects it.
    const text = await buildMergedInstructions(agentsMdPath, growth);
    return { contents: [{ uri: MERGED_PERSONA_RESOURCE_URI, mimeType: "text/markdown", text }] };
  });

  return {
    server,
    growth,
    knowledge,
    handlers,
    loadedCustomToolNames: customHandlers.map((h) => h.definition.name),
    customToolFailures: failures,
    instructionsText,
    agentsMdPath,
  };
}
