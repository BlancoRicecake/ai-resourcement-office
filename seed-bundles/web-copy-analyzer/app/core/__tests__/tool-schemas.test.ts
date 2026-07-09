import { test } from "node:test";
import assert from "node:assert/strict";
import { ALL_TOOL_DEFINITIONS, FETCH_PAGE_TOOL, SAVE_WORKFLOW_TOOL } from "../tool-schemas.js";

test("tool-schemas: exports exactly 12 MCP tool definitions (§2-3)", () => {
  assert.equal(ALL_TOOL_DEFINITIONS.length, 12);
});

test("tool-schemas: every tool's inputSchema declares additionalProperties:false (§5 input validation)", () => {
  for (const tool of ALL_TOOL_DEFINITIONS) {
    assert.equal(
      (tool.inputSchema as Record<string, unknown>).additionalProperties,
      false,
      `${tool.name} must have additionalProperties:false`
    );
  }
});

test("tool-schemas: names match design.md §2-3 exactly", () => {
  const names = ALL_TOOL_DEFINITIONS.map((t) => t.name).sort();
  assert.deepEqual(names, [
    "compare_report",
    "delete_persona",
    "diagnose_section",
    "fetch_page",
    "get_persona",
    "list_personas",
    "parse_sections",
    "readability_scorecard",
    "remember",
    "rewrite_section",
    "save_persona",
    "save_workflow",
  ]);
});

test("tool-schemas: save_workflow.name matches design §2-3 (maxLength only, no ASCII-only pattern that would reject Korean/spaced display names)", () => {
  // Path-traversal safety is enforced at the HANDLER layer via assertSafeId
  // (blocks / \\ .. and untrimmed input) — see growth/store.ts saveWorkflow.
  // The schema must NOT carry a restrictive `^[a-zA-Z0-9_-]+$` pattern: the
  // design's own example ("'{이름}' 워크플로 저장됨") and the Korean-operating
  // persona require free-form display names. assertSafeId still rejects "../..".
  const nameSchema = (SAVE_WORKFLOW_TOOL.inputSchema as { properties: { name: { maxLength?: number; pattern?: string } } })
    .properties.name;
  assert.equal(nameSchema.maxLength, 80);
  assert.equal(nameSchema.pattern, undefined);
});

test("tool-schemas: fetch_page.max_bytes has an upper bound (can't request an arbitrarily huge buffer)", () => {
  const maxBytesSchema = (FETCH_PAGE_TOOL.inputSchema as { properties: { max_bytes: { maximum?: number } } }).properties
    .max_bytes;
  assert.equal(typeof maxBytesSchema.maximum, "number");
  assert.ok((maxBytesSchema.maximum as number) <= 5_000_000);
});
