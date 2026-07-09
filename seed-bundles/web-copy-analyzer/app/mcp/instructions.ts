/**
 * Loads AGENTS.md and merges it with the growth-layer snapshot (§6-2,
 * user-first) into the text emitted as both the MCP `instructions` field
 * (initialize response — for hosts like Claude Desktop that don't read
 * local files) and the `persona://merged` resource (for Agent SDK/LangGraph
 * -style custom agents that need a code path to pull the persona instead of
 * relying on `instructions` auto-application).
 */

import * as fs from "node:fs/promises";
import { mergeInstructions } from "../growth/merge.js";
import type { GrowthStore } from "../growth/index.js";

export async function loadAgentsMd(agentsMdPath: string): Promise<string> {
  return fs.readFile(agentsMdPath, "utf-8");
}

export async function buildMergedInstructions(agentsMdPath: string, growth: GrowthStore): Promise<string> {
  const agentsMd = await loadAgentsMd(agentsMdPath);
  const snapshot = await growth.buildGrowthSnapshot();
  return mergeInstructions(agentsMd, snapshot);
}

export const MERGED_PERSONA_RESOURCE_URI = "persona://merged";
