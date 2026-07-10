/**
 * Loads worker/agent.md — emitted verbatim as the MCP `instructions` field
 * (initialize response) so hosts like Claude Desktop that don't read local
 * files still get the worker persona. There is no growth-layer merge: the
 * bundle's self-learning lives in memory/ files read by the host agent.
 */

import * as fs from "node:fs/promises";

export async function loadAgentsMd(agentsMdPath: string): Promise<string> {
  return fs.readFile(agentsMdPath, "utf-8");
}
