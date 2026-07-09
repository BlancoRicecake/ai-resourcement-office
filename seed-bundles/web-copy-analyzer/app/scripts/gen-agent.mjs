#!/usr/bin/env node
/**
 * Generates plugin/agents/web-copy-analyzer.md FROM worker/agent.md — 원천은
 * worker/agent.md 하나 (repointed from the original AGENTS.md, per this
 * repo's bundle standard: worker/agent.md is the portable persona source,
 * plugin/agents/*.md is the Claude Code-specific generated adapter).
 * Never hand-edit the generated file directly; edit worker/agent.md and
 * re-run `npm run gen:agent`.
 */
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const APP_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url))); // app/
const ROOT = path.dirname(APP_DIR); // bundle root
const AGENT_MD_PATH = path.join(ROOT, "worker", "agent.md");
const OUT_PATH = path.join(ROOT, "plugin", "agents", "web-copy-analyzer.md");

// The 12 MCP wire tool names (worker/mcp/tools.ts), namespaced per
// Claude Code's mcp__<server-name>__<tool-name> convention. <server-name>
// must match the mcpServers key registered in plugin/.claude-plugin/plugin.json.
const MCP_SERVER_NAME = "web-copy-analyzer";
const WIRE_TOOL_NAMES = [
  "save_persona",
  "list_personas",
  "get_persona",
  "delete_persona",
  "fetch_page",
  "parse_sections",
  "readability_scorecard",
  "diagnose_section",
  "rewrite_section",
  "compare_report",
  "remember",
  "save_workflow",
  "search_knowledge",
  "knowledge_neighbors",
  "learn_knowledge",
];

function main() {
  const raw = readFileSync(AGENT_MD_PATH, "utf8");

  // worker/agent.md's own opening paragraphs describe the file's role as a
  // portable persona-definition artifact — not part of the persona itself.
  // The persona body starts at section ①.
  const marker = "## ① 정체성과 판단 성향";
  const idx = raw.indexOf(marker);
  if (idx === -1) {
    throw new Error(
      `gen-agent: worker/agent.md에서 "${marker}" 섹션을 찾지 못했습니다 — worker/agent.md 구조가 바뀌면 이 스크립트도 갱신해야 합니다.`
    );
  }
  const persona = raw.slice(idx).trim();

  const tools = WIRE_TOOL_NAMES.map((name) => `mcp__${MCP_SERVER_NAME}__${name}`).join(", ");

  const frontmatter = [
    "---",
    "name: web-copy-analyzer",
    "description: Conversion-copy consultant that diagnoses landing-page copy against a saved target-buyer persona (above-the-fold scan, section-level attribution to clarity/trust/relevance/CTA, before/after rewrite with testimonial preservation). Use when the user wants to analyze, critique, score, or rewrite marketing or landing-page copy for a specific target audience.",
    `tools: ${tools}`,
    "model: opus",
    "---",
    "",
  ].join("\n");

  mkdirSync(path.dirname(OUT_PATH), { recursive: true });
  writeFileSync(
    OUT_PATH,
    `${frontmatter}\n<!-- GENERATED FILE — do not hand-edit. Source: ../../worker/agent.md via app/scripts/gen-agent.mjs -->\n\n${persona}\n`,
    "utf8"
  );

  console.log(`generated ${path.relative(ROOT, OUT_PATH)} (tools: ${WIRE_TOOL_NAMES.length}, model: opus)`);
}

main();
