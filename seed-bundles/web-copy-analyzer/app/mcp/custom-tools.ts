/**
 * custom-tools/ loader (design.md §5 "custom-tools/ 신뢰 모델", 문제표 #15).
 * Scans a folder for user-dropped `.js`/`.mjs` scripts, each expected to
 * default-export a `{ definition: ToolDefinition, execute(wireArgs, ctx) }`
 * shape identical to mcp/tools.ts's ToolHandler. Loaded modules run AS-IS —
 * no sandboxing (the trust model is "you put it there, security warning is
 * README-level per §5", this loader's only job is registration + reporting
 * what loaded and what didn't, per 문제표 #15).
 */

import * as fs from "node:fs/promises";
import * as path from "node:path";
import { pathToFileURL } from "node:url";
import type { ToolHandler } from "./tools.js";

export interface CustomToolLoadResult {
  loaded: ToolHandler[];
  /** 문제표 #15: "custom-tool '{name}' 로드 실패: {err}, 건너뜀" — one message per failed script. */
  failures: string[];
}

function isToolHandlerShape(mod: unknown): mod is { default: ToolHandler } | ToolHandler {
  const candidate = (mod as { default?: unknown }).default ?? mod;
  return (
    typeof candidate === "object" &&
    candidate !== null &&
    "definition" in candidate &&
    "execute" in candidate &&
    typeof (candidate as ToolHandler).execute === "function"
  );
}

export async function loadCustomTools(dir: string): Promise<CustomToolLoadResult> {
  const loaded: ToolHandler[] = [];
  const failures: string[] = [];

  let files: string[];
  try {
    files = await fs.readdir(dir);
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return { loaded, failures };
    failures.push(`custom-tools 디렉터리를 읽을 수 없습니다: ${(err as Error).message}`);
    return { loaded, failures };
  }

  const scripts = files.filter((f) => f.endsWith(".js") || f.endsWith(".mjs"));
  for (const file of scripts) {
    const fullPath = path.join(dir, file);
    try {
      const mod = (await import(pathToFileURL(fullPath).href)) as unknown;
      if (!isToolHandlerShape(mod)) {
        throw new Error("module does not export { definition, execute }");
      }
      const handler = ((mod as { default?: ToolHandler }).default ?? mod) as ToolHandler;
      if (!handler.definition?.name) {
        throw new Error("tool definition missing a 'name'");
      }
      loaded.push(handler);
    } catch (err) {
      failures.push(`custom-tool '${file}' 로드 실패: ${(err as Error).message}, 건너뜀`);
    }
  }

  return { loaded, failures };
}
