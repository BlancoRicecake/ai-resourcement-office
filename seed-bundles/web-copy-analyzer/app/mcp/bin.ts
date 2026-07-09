#!/usr/bin/env node
/**
 * stdio MCP server process entrypoint. `npx @ai-factory/web-copy-analyzer-mcp`
 * (or `node dist/mcp/bin.js`) runs this directly.
 */

import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { createServer } from "./server.js";

async function main(): Promise<void> {
  const created = await createServer();
  const transport = new StdioServerTransport();
  await created.server.connect(transport);
  // stdout is reserved for MCP protocol frames — all diagnostic output goes to stderr.
  console.error(`web-copy-analyzer MCP server started. tools: ${created.handlers.length}`);
}

main().catch((err) => {
  console.error("web-copy-analyzer MCP server failed to start:", err);
  process.exitCode = 1;
});
