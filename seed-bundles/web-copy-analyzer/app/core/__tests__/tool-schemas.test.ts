import { test } from "node:test";
import assert from "node:assert/strict";
import { ALL_TOOL_DEFINITIONS, DIAGNOSE_SECTION_TOOL, FETCH_PAGE_TOOL, REWRITE_SECTION_TOOL } from "../tool-schemas.js";

test("tool-schemas: exports exactly the 6 deterministic MCP tool definitions", () => {
  assert.equal(ALL_TOOL_DEFINITIONS.length, 6);
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

test("tool-schemas: names are exactly the canonical 6 deterministic tools", () => {
  const names = ALL_TOOL_DEFINITIONS.map((t) => t.name).sort();
  assert.deepEqual(names, [
    "compare_report",
    "diagnose_section",
    "fetch_page",
    "parse_sections",
    "readability_scorecard",
    "rewrite_section",
  ]);
});

test("tool-schemas: diagnose_section / rewrite_section take persona as an explicit inline input (no persona_id store lookup)", () => {
  for (const tool of [DIAGNOSE_SECTION_TOOL, REWRITE_SECTION_TOOL]) {
    const props = (tool.inputSchema as { properties: Record<string, unknown> }).properties;
    assert.ok("persona" in props, `${tool.name} must accept an inline 'persona' object`);
    assert.ok(!("persona_id" in props), `${tool.name} must NOT carry a persona_id (no persona store)`);
    const persona = props["persona"] as { type?: string; required?: string[] };
    assert.equal(persona.type, "object");
    assert.deepEqual(persona.required, ["name", "attributes"]);
  }
});

test("tool-schemas: fetch_page.max_bytes has an upper bound (can't request an arbitrarily huge buffer)", () => {
  const maxBytesSchema = (FETCH_PAGE_TOOL.inputSchema as { properties: { max_bytes: { maximum?: number } } }).properties
    .max_bytes;
  assert.equal(typeof maxBytesSchema.maximum, "number");
  assert.ok((maxBytesSchema.maximum as number) <= 5_000_000);
});
