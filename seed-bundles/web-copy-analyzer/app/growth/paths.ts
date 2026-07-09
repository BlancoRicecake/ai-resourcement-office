/**
 * Growth-layer root resolution (design.md §6-1). Default location is
 * `~/.web-copy-analyzer/` — "업데이트가 절대 건드리지 않음" (update-immutable,
 * separate from the plugin/AGENTS.md deployment location). Tests must never
 * touch the real home directory, so every growth-layer entry point accepts an
 * explicit `rootDir` override (falls back to `WEB_COPY_ANALYZER_HOME` env var,
 * then the real default).
 */

import * as os from "node:os";
import * as path from "node:path";

export const GROWTH_DIR_NAME = ".web-copy-analyzer";

export function resolveGrowthRoot(rootDir?: string): string {
  if (rootDir) return rootDir;
  if (process.env["WEB_COPY_ANALYZER_HOME"]) return process.env["WEB_COPY_ANALYZER_HOME"] as string;
  return path.join(os.homedir(), GROWTH_DIR_NAME);
}

export function personasDir(root: string): string {
  return path.join(root, "personas");
}

export function personaFilePath(root: string, id: string): string {
  return path.join(personasDir(root), `${id}.md`);
}

export function voiceFilePath(root: string): string {
  return path.join(root, "voice.md");
}

export function decisionsLogPath(root: string): string {
  return path.join(root, "decisions.log");
}

export function workflowsDir(root: string): string {
  return path.join(root, "workflows");
}

export function workflowFilePath(root: string, name: string): string {
  return path.join(workflowsDir(root), `${name}.json`);
}

/** Learned-knowledge root inside the growth layer (survives bundle updates). Seed knowledge lives in the bundle at worker/knowledge/, not here. */
export function knowledgeDir(root: string): string {
  return path.join(root, "knowledge");
}

export function knowledgeNodePath(root: string, id: string): string {
  return path.join(knowledgeDir(root), `${id}.md`);
}
